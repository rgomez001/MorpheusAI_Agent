import tweepy
from dotenv import load_dotenv
import os

def test_twitter_post():
    # Load environment variables
    load_dotenv()
    
    print("1. Creating Twitter client...")
    client = tweepy.Client(
        bearer_token=os.getenv("BEARER_TOKEN"),
        consumer_key=os.getenv("API_KEY"),
        consumer_secret=os.getenv("API_KEY_SECRET"),
        access_token=os.getenv("ACCESS_TOKEN"),
        access_token_secret=os.getenv("ACCESS_TOKEN_SECRET")
    )
    
    print("\n2. Attempting to post a test tweet...")
    try:
        tweet = client.create_tweet(text="This is a test tweet from my bot!")
        print(f"Success! Tweet ID: {tweet.data['id']}")
    except tweepy.errors.Forbidden as e:
        print(f"Forbidden error: {str(e)}")
        print("\nPossible solutions:")
        print("1. Check if your app has Write permissions")
        print("2. Verify your Access Token has Write permissions")
        print("3. Make sure your app has Elevated access")
    except Exception as e:
        print(f"Other error: {str(e)}")

if __name__ == "__main__":
    test_twitter_post() 