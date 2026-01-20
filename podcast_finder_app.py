"""
🎙️ PODCAST FINDER PRO
Better than ListenNotes - Built for Podcast Outreach

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

def filter_podcasts(podcasts, min_episodes, max_days_since_post, languages, 
                   exclude_explicit, categories_filter):
    """Filter podcasts based on criteria"""
    cutoff_timestamp = int((datetime.now() - timedelta(days=max_days_since_post)).timestamp())
    filtered = []
    
    for podcast in podcasts:
        # Episode count filter
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
        
        # Last update time filter
        last_update = podcast.get('lastUpdateTime', 0)
        if last_update < cutoff_timestamp:
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
    st.markdown("### Better than ListenNotes - Find Your Perfect Podcast Leads")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Credentials
        st.subheader("🔑 API Credentials")
        api_key = st.text_input("API Key", type="password", help="Get from https://api.podcastindex.org/")
        api_secret = st.text_input("API Secret", type="password")
        
        if not api_key or not api_secret:
            st.warning("⚠️ Enter API credentials")
            st.markdown("[Get Free API Key →](https://api.podcastindex.org/)")
            st.stop()
        
        st.markdown("---")
        
        # Search Options
        st.subheader("🔍 Search Method")
        search_method = st.radio("How to search?", ["Recent Active Podcasts", "Search by Keyword"])
        
        if search_method == "Search by Keyword":
            search_term = st.text_input("Search Term", placeholder="business, technology...")
        else:
            search_term = None
            st.info("Will search podcasts updated in the last year, then filter by your criteria below.")
        
        st.markdown("---")
        
        # Filters
        st.subheader("🎯 Filters")
        min_episodes = st.slider("Minimum Episodes", 1, 500, 15)
        max_days_since_post = st.slider("Posted Within Last X Days", 7, 365, 30)
        languages = st.multiselect("Languages", ['en', 'es', 'fr', 'de', 'pt', 'it', 'ja', 'zh'], default=['en'])
        exclude_explicit = st.checkbox("Exclude Explicit Content", value=False)
        
        categories_input = st.text_input("Categories (comma-separated)", placeholder="business, technology")
        categories_filter = [cat.strip() for cat in categories_input.split(',')] if categories_input else []
        
        max_results = st.slider("Max Results", 100, 1000, 1000, 100)
        
        st.markdown("---")
        search_button = st.button("🔍 Search Podcasts", type="primary")
    
    # Main Content
    if search_button:
        with st.spinner("🔍 Searching..."):
            if search_method == "Search by Keyword" and search_term:
                podcasts, error = search_by_term(api_key, api_secret, search_term)
                info = f"Keyword: '{search_term}'"
            else:
                # Always search for 1 year of data, then filter
                podcasts, error = search_podcasts(api_key, api_secret, max_results, 365)
                info = f"Searching last year of podcasts"
            
            if error:
                st.error(f"❌ {error}")
                st.stop()
            
            if not podcasts:
                st.warning("⚠️ No podcasts found")
                st.stop()
            
            st.success(f"✅ Found {len(podcasts)} podcasts ({info})")
        
        with st.spinner("🎯 Filtering..."):
            filtered = filter_podcasts(podcasts, min_episodes, max_days_since_post, languages, exclude_explicit, categories_filter)
            
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
        ### 👋 Welcome!
        
        1. Enter API credentials
        2. Choose search method
        3. Set filters
        4. Click Search
        5. Download results!
        
        **Why this is better than ListenNotes:**
        - Free
        - More control
        - Better UX
        - Direct API access
        """)
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #666;'>🎙️ Podcast Finder Pro | Powered by Podcast Index</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
