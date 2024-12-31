import os
import time
import re
from openai import OpenAI
import tweepy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def is_first_tweet():
    """Check if this is the first tweet"""
    try:
        client = tweepy.Client(
            consumer_key=os.getenv('API_KEY'),
            consumer_secret=os.getenv('API_KEY_SECRET'),
            access_token=os.getenv('ACCESS_TOKEN'),
            access_token_secret=os.getenv('ACCESS_TOKEN_SECRET')
        )
        tweets = client.get_users_tweets(id=client.get_me().data.id)
        return tweets.data is None or len(tweets.data) == 0
    except Exception as e:
        print(f"Error checking tweet history: {e}")
        return False

def generate_tweet_with_morpheus():
    """Let Morpheus AI generate tweets from its knowledge and personality"""
    try:
        print("1. Initializing assistant...")
        assistant_id = "asst_5AyAw1WHxg7eOL847byMYcpr"
        
        print("2. Creating thread...")
        thread = openai_client.beta.threads.create()
        
        print("3. Adding message to thread...")
        content = """Share ONE brief technical insight about Cardano or DRMZ.
        STRICT REQUIREMENTS:
        - Maximum 280 characters
        - Focus on a single point
        - Include 1-2 relevant hashtags
        - Be concise but informative"""
            
        message = openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=content
        )
        
        print("4. Running assistant...")
        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        print("5. Waiting for response...")
        timeout = 30
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                print("\nTimeout: Assistant took too long to respond")
                return None
                
            run_status = openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"Status: {run_status.status}")
            
            if run_status.status == 'completed':
                break
            elif run_status.status == 'requires_action':
                print("\nHandling required actions...")
                tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                
                for tool_call in tool_calls:
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": "Proceed with generating the tweet."
                    })
                
                run = openai_client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            elif run_status.status == 'failed':
                print("\nAssistant run failed")
                return None
                
            time.sleep(1)
        
        print("\n6. Getting response...")
        messages = openai_client.beta.threads.messages.list(thread_id=thread.id)
        tweet_text = messages.data[0].content[0].text.value.strip()
        
        # Clean up the tweet text
        tweet_text = re.sub(r'【.*?】', '', tweet_text).strip()
        if tweet_text.startswith('"') and tweet_text.endswith('"'):
            tweet_text = tweet_text[1:-1].strip()
            
        print(f"\nGenerated tweet: {tweet_text}")
        return tweet_text
        
    except Exception as e:
        print(f"Error generating tweet: {e}")
        return None

def post_tweet(tweet_text):
    """Post a tweet using Twitter API"""
    try:
        # Twitter API authentication
        client = tweepy.Client(
            consumer_key=os.getenv('API_KEY'),
            consumer_secret=os.getenv('API_KEY_SECRET'),
            access_token=os.getenv('ACCESS_TOKEN'),
            access_token_secret=os.getenv('ACCESS_TOKEN_SECRET')
        )
        
        # Clean up the tweet text to remove any meta text
        if '"' in tweet_text:
            tweet_text = tweet_text.split('"')[1]
        
        # Post tweet
        print("\nPosting tweet...")
        response = client.create_tweet(text=tweet_text)
        
        print("\nSuccess!")
        print(f"Check https://twitter.com/DRMZ_Agent/status/{response.data['id']}")
        
        return True
    except Exception as e:
        print(f"\nError posting tweet: {e}")
        return False

def main():
    """Main function to test the Twitter bot"""
    print("Testing Morpheus AI Twitter Bot...")
    
    print("\nGenerating tweet with Morpheus AI...")
    tweet_text = generate_tweet_with_morpheus()
    
    if tweet_text:
        post_tweet(tweet_text)
    
    print("\nTest complete!")

if __name__ == "__main__":
    main()