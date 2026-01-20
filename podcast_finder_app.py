"""
🎙️ PODCAST FINDER PRO
Built for Podcast Outreach

A beautiful web app to find and filter podcasts using Podcast Index API
No coding required - just use the filters and download your results!
"""

import streamlit as st
import requests
import pandas as pd
import hashlib
import time
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Podcast Finder Pro",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {padding: 2rem;}
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
    }
    .stButton>button:hover {background-color: #FF6B6B;}
    h1 {color: #FF4B4B;}
    </style>
    """, unsafe_allow_html=True)

# Helper Functions
def get_podcast_index_headers(api_key, api_secret):
    """Generate authentication headers for Podcast Index API"""
    epoch_time = int(time.time())
    data_to_hash = api_key + api_secret + str(epoch_time)
    sha_1 = hashlib.sha1(data_to_hash.encode()).hexdigest()
    
    return {
        'X-Auth-Date': str(epoch_time),
        'X-Auth-Key': api_key,
        'Authorization': sha_1,
        'User-Agent': 'PodcastFinderPro/1.0'
    }

def search_podcasts(api_key, api_secret, max_results=1000, days_back=365):
    """Search for podcasts from Podcast Index - always search wide, filter later"""
    base_url = "https://api.podcastindex.org/api/1.0"
    # Always search for a wide timeframe (1 year) and filter later
    since_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
    
    url = f"{base_url}/recent/feeds"
    params = {'since': since_timestamp, 'max': max_results}
    headers = get_podcast_index_headers(api_key, api_secret)
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'true':
                return data.get('feeds', []), None
            else:
                return [], f"API Error: {data.get('description', 'Unknown error')}"
        else:
            return [], f"HTTP Error {response.status_code}"
    except Exception as e:
        return [], f"Connection Error: {str(e)}"

def search_by_term(api_key, api_secret, search_term):
    """Search podcasts by keyword/term"""
    base_url = "https://api.podcastindex.org/api/1.0"
    url = f"{base_url}/search/byterm"
    params = {'q': search_term, 'max': 1000}
    headers = get_podcast_index_headers(api_key, api_secret)
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'true':
                return data.get('feeds', []), None
            else:
                return [], f"API Error: {data.get('description', 'Unknown error')}"
        else:
            return [], f"HTTP Error {response.status_code}"
    except Exception as e:
        return [], f"Connection Error: {str(e)}"

def filter_podcasts(podcasts, min_episodes, max_days_since_post, created_within_days,
                   languages, exclude_explicit, categories_filter, country_filter):
    """Filter podcasts based on Jaquory's criteria"""
    cutoff_timestamp = int((datetime.now() - timedelta(days=max_days_since_post)).timestamp())
    created_cutoff = int((datetime.now() - timedelta(days=created_within_days)).timestamp()) if created_within_days > 0 else 0
    
    filtered = []
    
    for podcast in podcasts:
        # Amount of posts (episode count filter)
        episode_count = podcast.get('episodeCount', 0)
        if episode_count < min_episodes:
            continue
        
        # Language filter
        if languages:
            podcast_language = podcast.get('language', '').lower()
            if podcast_language not in [lang.lower() for lang in languages]:
                continue
        
        # Explicit content filter
        if exclude_explicit and podcast.get('explicit', False):
            continue
        
        # Date of last post filter
        last_update = podcast.get('lastUpdateTime', 0)
        if last_update < cutoff_timestamp:
            continue
        
        # When podcast was created filter
        if created_within_days > 0:
            date_added = podcast.get('dateAdded', 0)
            if date_added > 0 and date_added < created_cutoff:
                continue
        
        # Country filter (basic - based on language codes)
        if country_filter != 'Any':
            podcast_language = podcast.get('language', '').lower()
            if country_filter == 'US' and 'en-us' not in podcast_language and podcast_language != 'en':
                continue
            elif country_filter == 'UK' and 'en-gb' not in podcast_language:
                continue
            elif country_filter == 'Canada' and 'en-ca' not in podcast_language:
                continue
            elif country_filter == 'Australia' and 'en-au' not in podcast_language:
                continue
        
        # Category filter
        if categories_filter:
            podcast_categories = [cat.lower() for cat in podcast.get('categories', {}).values()]
            if not any(filter_cat.lower() in cat for filter_cat in categories_filter for cat in podcast_categories):
                continue
        
        filtered.append(podcast)
    
    return filtered

def extract_podcast_data(podcasts):
    """Extract and format podcast data for display"""
    results = []
    
    for podcast in podcasts:
        result = {
            'Title': podcast.get('title', 'Unknown'),
            'Author': podcast.get('author', ''),
            'Owner': podcast.get('ownerName', ''),
            'Email': podcast.get('email', ''),
            'Website': podcast.get('link', ''),
            'Feed URL': podcast.get('url', ''),
            'Episodes': podcast.get('episodeCount', 0),
            'Language': podcast.get('language', ''),
            'Categories': ', '.join([cat for cat in podcast.get('categories', {}).values()]),
            'Last Updated': datetime.fromtimestamp(podcast.get('lastUpdateTime', 0)).strftime('%Y-%m-%d'),
            'Created': datetime.fromtimestamp(podcast.get('dateAdded', 0)).strftime('%Y-%m-%d') if podcast.get('dateAdded') else '',
            'iTunes ID': podcast.get('itunesId', ''),
            'Explicit': 'Yes' if podcast.get('explicit', False) else 'No',
            'Description': podcast.get('description', '')[:200] + '...' if len(podcast.get('description', '')) > 200 else podcast.get('description', ''),
            'Image': podcast.get('image', '')
        }
        results.append(result)
    
    return pd.DataFrame(results)

# Main App
def main():
    st.title("🎙️ Podcast Finder Pro")
    st.markdown("### Find Your Perfect Podcast Leads")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Try to load API credentials from secrets
        try:
            api_key = st.secrets["podcast_index"]["api_key"]
            api_secret = st.secrets["podcast_index"]["api_secret"]
            st.success("✅ Using stored credentials")
        except:
            # Fallback to user input if secrets not available
            st.subheader("🔑 API Credentials")
            st.info("Enter your Podcast Index API credentials")
            api_key = st.text_input("API Key", type="password", help="Get from https://api.podcastindex.org/")
            api_secret = st.text_input("API Secret", type="password")
            
            if not api_key or not api_secret:
                st.warning("⚠️ Enter API credentials")
                st.markdown("[Get Free API Key →](https://api.podcastindex.org/)")
                st.stop()
        
        st.markdown("---")
        
        # Search
        st.subheader("🔍 Search")
        search_term = st.text_input(
            "Search Term", 
            placeholder="business, technology, health...",
            help="Search for podcasts by keyword, topic, or category"
        )
        
        st.markdown("---")
        
        # Filters - Jaquory's Requirements
        st.subheader("🎯 Filters")
        
        # Amount of posts (episodes)
        min_episodes = st.slider(
            "Minimum Episodes",
            min_value=1,
            max_value=500,
            value=15,
            help="Amount of posts - minimum episode count"
        )
        
        # Date of last post
        max_days_since_post = st.slider(
            "Posted Within Last X Days",
            min_value=1,
            max_value=365,
            value=30,
            help="Date of last post - only show podcasts that posted recently"
        )
        
        # When podcast was created
        created_within_days = st.slider(
            "Created Within Last X Days (Optional)",
            min_value=0,
            max_value=3650,
            value=365,
            help="When the podcast was created - 0 means no filter"
        )
        
        # Location filter
        country_filter = st.selectbox(
            "Country (Optional)",
            options=['Any', 'US', 'UK', 'Canada', 'Australia'],
            index=0,
            help="Filter by country - based on language and metadata"
        )
        
        # Language
        languages = st.multiselect(
            "Languages",
            options=['en', 'en-us', 'es', 'fr', 'de', 'pt', 'it'],
            default=['en', 'en-us'],
            help="Podcast language"
        )
        
        # Additional filters
        exclude_explicit = st.checkbox("Exclude Explicit Content", value=False)
        
        categories_input = st.text_input(
            "Categories (comma-separated, optional)",
            placeholder="sports, business, technology",
            help="Filter by categories - leave empty for all"
        )
        categories_filter = [cat.strip() for cat in categories_input.split(',')] if categories_input else []
        
        max_results = st.slider("Max Results to Fetch", 100, 1000, 1000, 100)
        
        st.markdown("---")
        search_button = st.button("🔍 Search Podcasts", type="primary")
    
    # Main Content
    if search_button:
        if not search_term or not search_term.strip():
            st.error("⚠️ Please enter a search term (e.g., business, technology, sports)")
            st.stop()
        
        with st.spinner("🔍 Searching..."):
            podcasts, error = search_by_term(api_key, api_secret, search_term)
            
            if error:
                st.error(f"❌ {error}")
                st.stop()
            
            if not podcasts:
                st.warning(f"⚠️ No podcasts found for '{search_term}'")
                st.stop()
            
            st.success(f"✅ Found {len(podcasts)} podcasts for '{search_term}'")
        
        with st.spinner("🎯 Filtering..."):
            filtered = filter_podcasts(
                podcasts, 
                min_episodes, 
                max_days_since_post,
                created_within_days,
                languages, 
                exclude_explicit, 
                categories_filter,
                country_filter
            )
            
            if not filtered:
                st.warning("⚠️ No matches. Relax filters.")
                st.stop()
            
            df = extract_podcast_data(filtered)
        
        # Results
        st.markdown("---")
        st.header(f"📊 Results: {len(df)} Podcasts")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(df))
        with col2:
            st.metric("Avg Episodes", f"{df['Episodes'].mean():.0f}")
        with col3:
            st.metric("With Email", df['Email'].notna().sum())
        with col4:
            st.metric("With Author", df['Author'].notna().sum())
        
        st.markdown("---")
        
        # Display
        default_cols = ['Title', 'Author', 'Email', 'Episodes', 'Last Updated', 'Categories']
        selected_cols = st.multiselect("Select Columns", df.columns.tolist(), default=default_cols)
        
        if selected_cols:
            st.dataframe(df[selected_cols], use_container_width=True, height=400)
            
            # Download
            st.markdown("---")
            st.subheader("📥 Download")
            csv = df.to_csv(index=False)
            st.download_button(
                "📄 Download CSV",
                csv,
                f"podcasts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    else:
        st.info("""
        ### 👋 Welcome to Podcast Finder Pro!
        
        **Built for Podcast Outreach**
        
        **How to use:**
        1. Enter a search term (business, technology, sports, etc.)
        2. Set your filters:
           - Amount of posts (minimum episodes)
           - Date of last post (posted within X days)
           - When podcast was created
           - Country/Language
        3. Click "Search Podcasts"
        4. Download CSV for your outreach!
        
        **Example Query:**
        _"Show me podcasts that released in the last year, based in the US, 
        that have over 15 episodes and have posted in the last 30 days"_
        
        **Settings for this:**
        - Search Term: `business` (or any niche)
        - Minimum Episodes: `15`
        - Posted Within Last: `30` days
        - Created Within Last: `365` days
        - Country: `US`
        - Languages: `en, en-us`
        
    
        Ready to find a podcast? Enter a search term and start! 🚀
        """)
        
        st.markdown("---")
        st.subheader("💡 Search Tips")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Good Search Terms:**
            - business
            - entrepreneurship
            - technology
            - marketing
            - investing
            - real estate
            - health
            - fitness
            """)
        
        with col2:
            st.markdown("""
            **Pro Tips:**
            - Start broad, refine with filters
            - Try different search terms
            - Set "Created Within" to 0 for all podcasts
            - US podcasts usually use "en" or "en-us"
            - Download and combine multiple searches!
            """)
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #666;'>🎙️ Podcast Finder Pro | Powered by Podcast Index</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
