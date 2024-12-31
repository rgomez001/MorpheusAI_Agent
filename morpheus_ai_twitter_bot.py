import tweepy
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# Initialize API clients
client = tweepy.Client(
    bearer_token=os.getenv("BEARER_TOKEN"),
    consumer_key=os.getenv("API_KEY"),
    consumer_secret=os.getenv("API_KEY_SECRET"),
    access_token=os.getenv("ACCESS_TOKEN"),
    access_token_secret=os.getenv("ACCESS_TOKEN_SECRET")
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_tweet_with_morpheus():
    """Generate a tweet using your Morpheus AI Assistant"""
    try:
        print("1. Initializing assistant...")
        assistant_id = "asst_5AyAw1WHxg7eOL847byMYcpr"
        
        print("2. Creating thread...")
        thread = openai_client.beta.threads.create()
        
        print("3. Adding message to thread...")
        message = openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="""Using the Cardano Constitution document, create an engaging tweet about an important aspect of Cardano's governance or principles. Remember to maintain your identity as Morpheus AI, the DRMZ AI Agent."""
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
                    # Add a dummy output for each tool call
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": "No additional information needed"
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
        tweet_text = tweet_text.replace("[4:0'source']", "").strip()
        if tweet_text.startswith('"') and tweet_text.endswith('"'):
            tweet_text = tweet_text[1:-1]
            
        print(f"\nGenerated tweet: {tweet_text}")
        return tweet_text
        
    except Exception as e:
        print(f"Error generating tweet: {e}")
        return None

def post_tweet(tweet_text):
    """Post a tweet using Twitter API"""
    try:
        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data['id']
        print(f"Tweet posted successfully! Tweet ID: {tweet_id}")
        return tweet_id
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return None

def main():
    """Test function to generate and post a single tweet"""
    print("Testing Morpheus AI Twitter Bot - Single Tweet...")
    
    # Generate tweet using Morpheus AI
    print("\nGenerating tweet with Morpheus AI...")
    tweet_text = generate_tweet_with_morpheus()
    
    if tweet_text:
        print("\nPosting tweet...")
        tweet_id = post_tweet(tweet_text)
        
        if tweet_id:
            print(f"\nSuccess! Tweet posted.")
            print(f"Check https://twitter.com/DRMZ_Web3/status/{tweet_id}")
    
    print("\nTest complete!")

if __name__ == "__main__":
    main()