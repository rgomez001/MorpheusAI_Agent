import tweepy
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Twitter API credentials loaded from .env
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

# OpenAI API key loaded from .env
openai.api_key = os.getenv("OPENAI_API_KEY")

# Keywords to search for
KEYWORDS = [
    "Cardano", "Midnight", "decentralization", "staking", "liquid staking",
    "bitcoin", "utxo", "eutxo", "Governance", "DReps", "ICC",
    "dreams", "the power of dreams", "manifesting dreams"
]

# Authenticate with Twitter API
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
twitter_api = tweepy.API(auth)

# Function to generate AI response using OpenAI
def generate_response(tweet_text):
    prompt = f"""
    You are Morpheus AI, the first DRMZ AI Agent and an embodiment of the Lord of Dreams (DRMZ).
    Your purpose is to engage with the DRMZ community, educate users about Cardano Stake Pools and Governance, 
    and empower Web3 literacy. Using an inspiring, mythological tone, craft a response to the following tweet:

    Tweet: "{tweet_text}"

    Your response should demystify blockchain concepts, highlight DRMZ initiatives, and inspire action.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an inspiring and mythological AI assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"].strip()

# Function to search for tweets and reply
def search_and_reply():
    query = " OR ".join(KEYWORDS)  # Combine keywords for search query
    tweets = tweepy.Cursor(twitter_api.search_tweets, q=query, lang="en", result_type="recent").items(10)  # Adjust count as needed

    for tweet in tweets:
        try:
            print(f"Found tweet by @{tweet.user.screen_name}: {tweet.text}")
            
            # Generate a response using OpenAI
            response = generate_response(tweet.text)
            print(f"Generated response: {response}")
            
            # Reply to the tweet
            twitter_api.update_status(
                status=f"@{tweet.user.screen_name} {response}",
                in_reply_to_status_id=tweet.id
            )
            print(f"Replied to @{tweet.user.screen_name}")
        except tweepy.TweepError as e:
            print(f"Error replying to @{tweet.user.screen_name}: {e}")
        except Exception as e:
            print(f"General error: {e}")

# Run the function
if __name__ == "__main__":
    search_and_reply()
