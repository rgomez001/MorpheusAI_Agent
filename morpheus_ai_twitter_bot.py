import tweepy
from dotenv import load_dotenv
import os
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Twitter API credentials
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

def create_client():
    try:
        # Create client with minimal configuration
        return tweepy.Client(
            bearer_token=BEARER_TOKEN,
            wait_on_rate_limit=True
        )
    except Exception as e:
        print(f"Error creating client: {e}")
        return None

def check_rate_limits():
    try:
        client = create_client()
        if client:
            # Get rate limit status
            response = client.get_recent_tweets_count("Cardano")
            print(f"Rate limit remaining: {response.meta}")
            return True
    except Exception as e:
        print(f"Error checking rate limits: {e}")
        return False

def main():
    print(f"[{datetime.now()}] Starting Twitter API test...")
    print("Checking rate limits...")
    
    if check_rate_limits():
        print("Rate limit check successful")
    else:
        print("Rate limit check failed")

if __name__ == "__main__":
    main()