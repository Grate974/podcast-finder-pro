"""
PODCAST INDEX API - SIMPLE TEST
Just shows you what's actually in the API (no filters)
"""

import streamlit as st
import requests
import pandas as pd
import hashlib
import time
from datetime import datetime

st.set_page_config(page_title="API Test", page_icon="🔍", layout="wide")

st.title("🔍 Podcast Index API Test")
st.markdown("### Let's see what the API actually returns (no filters)")
st.markdown("---")

# Sidebar for credentials
with st.sidebar:
    st.header("🔑 API Credentials")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("API Secret", type="password")
    
    if not api_key or not api_secret:
        st.warning("⚠️ Enter credentials")
        st.stop()
    
    st.markdown("---")
    test_type = st.radio(
        "Test Type",
        ["Get 10 Recent Podcasts", "Search 'business'", "Get 100 Recent Podcasts"]
    )
    
    test_button = st.button("🧪 Run Test", type="primary")

def get_headers(api_key, api_secret):
    """Generate auth headers"""
    epoch_time = int(time.time())
    data_to_hash = api_key + api_secret + str(epoch_time)
    sha_1 = hashlib.sha1(data_to_hash.encode()).hexdigest()
    
    return {
        'X-Auth-Date': str(epoch_time),
        'X-Auth-Key': api_key,
        'Authorization': sha_1,
        'User-Agent': 'PodcastTest/1.0'
    }

if test_button:
    st.markdown("---")
    
    base_url = "https://api.podcastindex.org/api/1.0"
    headers = get_headers(api_key, api_secret)
    
    try:
        if test_type == "Get 10 Recent Podcasts":
            st.subheader("📡 Calling: /recent/feeds (max=10)")
            url = f"{base_url}/recent/feeds"
            params = {'max': 10}
            
        elif test_type == "Get 100 Recent Podcasts":
            st.subheader("📡 Calling: /recent/feeds (max=100)")
            url = f"{base_url}/recent/feeds"
            params = {'max': 100}
            
        else:  # Search business
            st.subheader("📡 Calling: /search/byterm (q=business)")
            url = f"{base_url}/search/byterm"
            params = {'q': 'business', 'max': 10}
        
        st.code(f"GET {url}")
        st.code(f"Params: {params}")
        
        with st.spinner("🔄 Calling API..."):
            response = requests.get(url, headers=headers, params=params, timeout=30)
        
        st.markdown("### 📊 Response")
        
        # Show status
        if response.status_code == 200:
            st.success(f"✅ Status Code: {response.status_code}")
        else:
            st.error(f"❌ Status Code: {response.status_code}")
        
        # Show raw response
        with st.expander("🔍 Raw JSON Response (click to expand)"):
            st.json(response.json())
        
        # Parse and display
        data = response.json()
        
        if data.get('status') == 'true':
            feeds = data.get('feeds', [])
            
            st.success(f"✅ API returned {len(feeds)} podcasts")
            
            if feeds:
                st.markdown("---")
                st.subheader("📋 Podcast Data")
                
                # Convert to DataFrame
                podcast_list = []
                for feed in feeds:
                    podcast_list.append({
                        'Title': feed.get('title', 'N/A'),
                        'Author': feed.get('author', 'N/A'),
                        'Owner': feed.get('ownerName', 'N/A'),
                        'Email': feed.get('email', 'N/A'),
                        'Episodes': feed.get('episodeCount', 0),
                        'Language': feed.get('language', 'N/A'),
                        'Last Update': datetime.fromtimestamp(feed.get('lastUpdateTime', 0)).strftime('%Y-%m-%d %H:%M'),
                        'Explicit': 'Yes' if feed.get('explicit') else 'No',
                        'iTunes ID': feed.get('itunesId', 'N/A'),
                        'Categories': str(feed.get('categories', {})),
                        'Website': feed.get('link', 'N/A'),
                        'Feed URL': feed.get('url', 'N/A')
                    })
                
                df = pd.DataFrame(podcast_list)
                
                # Show stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", len(df))
                with col2:
                    avg_eps = df['Episodes'].mean()
                    st.metric("Avg Episodes", f"{avg_eps:.0f}")
                with col3:
                    with_email = df[df['Email'] != 'N/A']['Email'].count()
                    st.metric("With Email", with_email)
                with col4:
                    with_author = df[df['Author'] != 'N/A']['Author'].count()
                    st.metric("With Author", with_author)
                
                st.markdown("---")
                
                # Show table
                st.dataframe(df, use_container_width=True, height=400)
                
                # Show sample categories
                st.markdown("---")
                st.subheader("🏷️ Sample Categories Found")
                
                categories_found = set()
                for feed in feeds:
                    cats = feed.get('categories', {})
                    for cat_value in cats.values():
                        if cat_value:
                            categories_found.add(str(cat_value))
                
                if categories_found:
                    st.write("Categories in this batch:")
                    for cat in sorted(list(categories_found))[:20]:
                        st.write(f"- {cat}")
                else:
                    st.info("No categories found in this batch")
                
                # Show episode count distribution
                st.markdown("---")
                st.subheader("📊 Episode Count Distribution")
                st.write(df['Episodes'].describe())
                
                # Show language distribution
                st.markdown("---")
                st.subheader("🌍 Languages Found")
                lang_counts = df['Language'].value_counts()
                st.write(lang_counts)
                
                # Download button
                st.markdown("---")
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
                
            else:
                st.warning("⚠️ API returned 0 podcasts")
        
        else:
            st.error(f"❌ API Error: {data.get('description', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)

else:
    st.info("""
    ### 🧪 Test Your API Connection
    
    This simple test shows you EXACTLY what the Podcast Index API returns.
    
    **What this does:**
    1. Calls the API with your credentials
    2. Shows you the raw response
    3. Displays the data in a table
    4. Shows statistics about what was returned
    
    **How to use:**
    1. Enter your API credentials in the sidebar
    2. Choose a test type
    3. Click "Run Test"
    4. See what you get!
    
    **This will help us debug:**
    - ✅ Are credentials working?
    - ✅ What data is actually returned?
    - ✅ What do episode counts look like?
    - ✅ What languages are present?
    - ✅ What categories exist?
    
    Let's see what's actually in the API! 🔍
    """)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>🧪 API Test Tool</div>", unsafe_allow_html=True)
