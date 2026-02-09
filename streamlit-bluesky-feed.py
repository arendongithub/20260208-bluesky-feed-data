import streamlit as st
import json
import requests
from bs4 import BeautifulSoup
from time import strftime
from atproto import Client

def timestamp():
    return strftime("%Y%m%d%H%M%S")

def get_bsky_author_id(handle):
    """Fetch the DID (Decentralized Identifier) for a Bluesky handle."""
    url = f"https://bsky.app/profile/{handle}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        did_tag = soup.find('p', {'id': 'bsky_did'})
        
        if did_tag:
            return did_tag.text.strip()
        else:
            st.error("DID not found in the profile page.")
            return None
    
    return None

def fetch_feed_data(client, author_did, number_of_posts):
    """Fetch feed data from Bluesky."""
    feed = []
    cursor = ''
    
    try:
        for i in range(int(number_of_posts / 50) + (1 if number_of_posts % 50 > 0 else 0)):
            data = client.get_author_feed(
                actor=author_did,
                filter='posts_and_author_threads',
                cursor=cursor
            )
            cursor = data.cursor
            st.write(f"Fetched {len(data.feed)} items, cursor: {cursor}")
            feed = feed + data.feed
            
            # Break if we have enough posts
            if len(feed) >= number_of_posts:
                feed = feed[:number_of_posts]
                break
        
        return data, feed
    except Exception as e:
        st.error(f"Error fetching feed: {str(e)}")
        return None, None


def main():
    st.set_page_config(page_title="Bluesky Feed Downloader", layout="centered")
    
    st.image("theplant-logo.png")
    st.title("Bluesky Feed Data Downloader")
    
    # Create a form for user input
    with st.form("feed_form"):
        st.subheader("Login Credentials")
        handle = st.text_input("Enter your Bluesky handle:", placeholder="e.g., yourname.bsky.social")
        password = st.text_input("Enter your Bluesky password:", type="password")
        
        st.subheader("Feed Settings")
        author_handle = st.text_input("Enter the Bluesky handle of the author to fetch feed for:", placeholder="e.g., author.bsky.social")
        number_of_posts = st.number_input("Number of posts to fetch:", min_value=1, value=50, step=50)
        
        submitted = st.form_submit_button("Fetch Feed Data")
    
    # Process the form submission
    if submitted:
        if not handle or not password or not author_handle:
            st.error("Please fill in all fields.")
            return
        
        with st.spinner("Logging in and fetching data..."):
            try:
                # Login to Bluesky
                client = Client()
                client.login(handle, password)
                st.success("Successfully logged in!")
                
                # Get author DID
                st.info("Fetching author information...")
                author_did = get_bsky_author_id(author_handle)
                
                if not author_did:
                    st.error("Could not find author. Please check the handle and try again.")
                    return
                
                # Fetch feed data
                st.info("Fetching feed data...")
                data, feed = fetch_feed_data(client, author_did, int(number_of_posts))
                
                if data is None or feed is None:
                    st.error("Failed to fetch feed data.")
                    return
                
                st.success(f"Data fetched successfully! Received {len(feed)} items.")
                
                # Prepare JSON data for download
                jsondata = json.loads(data.json())
                json_string = json.dumps(jsondata, indent=2)
                
                # Display the data
                # st.subheader("Feed Data Preview")
                # st.json(jsondata)
                
                # Download button
                filename = f"{timestamp()}-feed_data.json"
                st.download_button(
                    label="Download JSON Data",
                    data=json_string,
                    file_name=filename,
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
