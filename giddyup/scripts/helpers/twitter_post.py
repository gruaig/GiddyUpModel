#!/usr/bin/env python3
"""
Twitter posting script using X API v1.1 with OAuth 1.0a
Usage: python3 twitter_post.py "Your tweet text here"
"""

import os
import sys
import requests
from requests_oauthlib import OAuth1

def post_tweet(tweet_text):
    """Post a tweet using X API v1.1 with OAuth 1.0a."""
    
    # Get credentials from environment
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_secret = os.getenv('TWITTER_ACCESS_SECRET')
    
    if not all([api_key, api_secret, access_token, access_secret]):
        print("❌ Twitter credentials not set!")
        return False
    
    try:
        # OAuth 1.0a User Context authentication
        auth = OAuth1(api_key, api_secret, access_token, access_secret)
        
        # POST to X API v1.1 (more reliable for posting)
        print(f"🐦 Posting tweet: {tweet_text}")
        response = requests.post(
            "https://api.twitter.com/1.1/statuses/update.json", 
            auth=auth,
            data={"status": tweet_text}
        )
        
        if response.status_code == 200:
            tweet_id = response.json().get('id')
            print(f"✅ Tweet posted successfully! ID: {tweet_id}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error posting tweet: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 twitter_post.py \"Your tweet text here\"")
        sys.exit(1)
    
    tweet_text = sys.argv[1]
    post_tweet(tweet_text)
