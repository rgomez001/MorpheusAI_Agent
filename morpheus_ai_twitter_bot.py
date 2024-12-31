import os
import time
import re
from openai import OpenAI
import tweepy
from dotenv import load_dotenv
import schedule
from datetime import datetime, timedelta
import pytz
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class TweetTracker:
    def __init__(self, filename='replied_tweets.json'):
        self.filename = filename
        self.replied_tweets = self.load_tweets()
        
    def load_tweets(self):
        """Load previously replied tweets from file"""
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                # Clean up old tweets (older than 7 days)
                current_time = datetime.now()
                data = {
                    tweet_id: timestamp 
                    for tweet_id, timestamp in data.items()
                    if current_time - datetime.fromisoformat(timestamp) < timedelta(days=7)
                }
                return data
        except FileNotFoundError:
            return {}
            
    def save_tweets(self):
        """Save replied tweets to file"""
        with open(self.filename, 'w') as f:
            json.dump(self.replied_tweets, f)
            
    def already_replied(self, tweet_id):
        """Check if we've already replied to this tweet"""
        return str(tweet_id) in self.replied_tweets
        
    def mark_as_replied(self, tweet_id):
        """Mark a tweet as replied to"""
        self.replied_tweets[str(tweet_id)] = datetime.now().isoformat()
        self.save_tweets()

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

def clean_tweet_text(text):
    """Clean the tweet text by removing metadata and ensuring proper formatting"""
    # Remove metadata tags
    text = re.sub(r'【.*?】', '', text)
    
    # Check if there are hashtags
    if '#' in text:
        # Split into main text and hashtags
        parts = text.split('#')
        main_text = parts[0].strip()
        hashtags = ['#' + tag.strip() for tag in parts[1:] if tag.strip()]
        
        # Combine with double line break before hashtags
        return f"{main_text}\n\n{' '.join(hashtags)}"
    
    return text.strip()

def generate_tweet_with_morpheus():
    """Let Morpheus AI generate tweets from its knowledge and personality"""
    try:
        print("Analyzing community tweet...")
        thread = openai_client.beta.threads.create()
        
        message = openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="""Share a brief, mystical response (max 200 characters for main message).

            STRICT RULES:
            1. Keep the main message under 200 characters
            2. Add a line break before hashtags
            3. Use 2-3 relevant hashtags
            4. Do not include any metadata or source tags
            5. Total tweet must be under 280 characters

            Example:
            The dreams of Web3 manifest through Cardano's innovation

            #DRMZ #Cardano #Web3"""
        )
        
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
        return clean_tweet_text(tweet_text)
        
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

def test_schedule():
    """Print scheduled times without actually tweeting"""
    pst = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(pst)
    
    print("\nMorpheus AI Scheduler Test Mode")
    print("-------------------------------")
    print(f"Current time (PST): {current_time.strftime('%I:%M %p')}")
    print("\nScheduled tweet times (PST):")
    print("1. 7:00 AM  - GM + Daily insight")
    print("2. 12:00 PM - Community engagement")
    print("3. 6:00 PM  - Trending topics")
    print("\nTest Mode: No tweets will be sent")
    print("\nPress Ctrl+C to exit test mode")
    
    # Simulate schedule checks
    while True:
        next_run = schedule.next_run()
        if next_run:
            print(f"\nNext scheduled tweet would be at: {next_run} PST")
        time.sleep(10)  # Check every 10 seconds in test mode

def monitor_trending_topics():
    """Monitor trending Cardano and Web3 topics"""
    try:
        client = tweepy.Client(
            consumer_key=os.getenv('API_KEY'),
            consumer_secret=os.getenv('API_KEY_SECRET'),
            access_token=os.getenv('ACCESS_TOKEN'),
            access_token_secret=os.getenv('ACCESS_TOKEN_SECRET')
        )
        
        # Search terms for relevant topics
        search_queries = [
            "Cardano",
            "DRMZ",
            "Web3",
            "ADA",
            "DeFi"
        ]
        
        # Get recent popular tweets for each topic
        trending_tweets = []
        for query in search_queries:
            tweets = client.search_recent_tweets(
                query=f"{query} -is:retweet min_faves:50",
                max_results=10,
                tweet_fields=['public_metrics', 'created_at']
            )
            if tweets.data:
                trending_tweets.extend(tweets.data)
        
        # Sort by engagement (likes + retweets)
        trending_tweets.sort(
            key=lambda x: x.public_metrics['like_count'] + x.public_metrics['retweet_count'],
            reverse=True
        )
        
        return trending_tweets[:5]  # Return top 5 trending tweets
        
    except Exception as e:
        print(f"Error monitoring trends: {e}")
        return None

def generate_engagement_response(tweet_text):
    """Let Morpheus AI respond based on its own training and personality"""
    try:
        print("Analyzing community tweet...")
        thread = openai_client.beta.threads.create()
        
        message = openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"""Respond to this tweet with a brief, insightful comment:
            "{tweet_text}"

            GUIDELINES:
            1. Keep your response concise and meaningful
            2. Focus on one key point
            3. Use hashtags only when they add value
            4. If using hashtags, add them on a new line
            5. Stay under 280 characters total

            You can respond either with or without hashtags, depending on what feels most natural for your message."""
        )
        
        # Run the assistant
        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id="asst_5AyAw1WHxg7eOL847byMYcpr"
        )
        
        # Wait for response
        while True:
            run_status = openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run_status.status == 'completed':
                # Get the response
                messages = openai_client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                response_text = messages.data[0].content[0].text.value.strip()
                
                # Clean up response
                if response_text.startswith('"') and response_text.endswith('"'):
                    response_text = response_text[1:-1].strip()
                
                return response_text
                
            elif run_status.status == 'failed':
                print("Failed to generate response")
                return None
                
            time.sleep(1)
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_multiple_responses():
    """Test Morpheus AI's responses to different scenarios"""
    print("\nTesting Multiple Response Types")
    print("------------------------------")
    
    test_cases = [
        "Cardano's eUTXO model is revolutionizing DeFi!",
        "DRMZ stake pool just minted another block! 🎉",
        "The future of Web3 governance looks promising",
        "AI and blockchain technology are converging",
        "Community-driven development is key to success"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: '{test_case}'")
        print("Generating response...")
        
        response = generate_engagement_response(test_case)
        if response:
            cleaned_response = clean_tweet_text(response)
            print(f"Response: '{cleaned_response}'")
            print("\n" + "-"*50)
        
        # Pause between tests to avoid rate limits
        time.sleep(3)

def monitor_cardano_community(client):
    """Monitor and engage with relevant Cardano community tweets"""
    try:
        print("Monitoring Cardano community tweets...")
        # Updated search query without min_faves
        tweets = client.search_recent_tweets(
            query="(Cardano OR ADA OR Web3) -is:retweet lang:en",
            max_results=10,
            tweet_fields=['public_metrics', 'created_at', 'author_id']
        )
        
        if tweets.data:
            for tweet in tweets.data:
                # Filter for tweets with some engagement
                if tweet.public_metrics['like_count'] >= 5:
                    # Skip if we've already replied
                    if tracker.already_replied(tweet.id):
                        continue
                        
                    # Generate and post response
                    response = generate_engagement_response(tweet.text)
                    if response:
                        print(f"\nResponding to tweet: {tweet.text[:100]}...")
                        client.create_tweet(
                            text=response,
                            in_reply_to_tweet_id=tweet.id
                        )
                        
                        # Mark as replied
                        tracker.mark_as_replied(tweet.id)
                        
                        # Wait between responses
                        time.sleep(60)
                        
    except Exception as e:
        print(f"Error monitoring community: {e}")

def run_morpheus_bot(client, test_mode=False):
    """Main bot function for continuous operation"""
    tracker = TweetTracker()
    last_run_hour = None  # Track when we last posted
    
    if test_mode:
        print("\nRunning in TEST MODE - Generating immediate tweet...")
        generate_and_post_tweet(client, "test")
        return

    while True:
        try:
            current_time = datetime.now(pytz.timezone('America/Los_Angeles'))
            current_hour = current_time.hour
            current_minute = current_time.minute
            
            # Only post if we haven't posted this hour and it's within the first 5 minutes of the hour
            if current_hour != last_run_hour and current_minute < 5:
                if current_hour == 7:
                    print("\nTime for morning tweet!")
                    if generate_and_post_tweet(client, "morning"):
                        last_run_hour = current_hour
                elif current_hour == 12:
                    print("\nTime for community tweet!")
                    if generate_and_post_tweet(client, "community"):
                        last_run_hour = current_hour
                elif current_hour == 18:
                    print("\nTime for trending tweet!")
                    if generate_and_post_tweet(client, "trending"):
                        last_run_hour = current_hour
            
            # Monitor community
            monitor_cardano_community(client)
            
            # Short sleep to prevent excessive API calls
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(300)

def verify_credentials():
    """Verify Twitter API credentials before starting"""
    try:
        print("Verifying Twitter credentials...")
        client = tweepy.Client(
            bearer_token=os.getenv('BEARER_TOKEN'),
            consumer_key=os.getenv('API_KEY'),
            consumer_secret=os.getenv('API_KEY_SECRET'),
            access_token=os.getenv('ACCESS_TOKEN'),
            access_token_secret=os.getenv('ACCESS_TOKEN_SECRET'),
            wait_on_rate_limit=True
        )
        
        # Test the credentials
        me = client.get_me()
        print(f"Authentication successful! Connected as: @{me.data.username}")
        return client
        
    except Exception as e:
        print(f"Authentication Error: {e}")
        print("Please check your Twitter API credentials in .env file")
        return None

def generate_and_post_tweet(client, tweet_type="test"):
    """Generate and post a tweet based on the type"""
    try:
        print(f"Generating {tweet_type} tweet...")
        
        # Create a new thread
        thread = openai_client.beta.threads.create()
        
        # Updated prompts with character limit emphasis
        prompts = {
            "morning": "Create a brief good morning tweet about Cardano or Web3. Keep it under 200 characters.",
            "community": "Share a brief thought about the Cardano community. Keep it under 200 characters.",
            "trending": "Comment briefly on Cardano or Web3 trends. Keep it under 200 characters.",
            "test": """As Morpheus AI, share ONE brief insight about Cardano (max 200 characters).

            IMPORTANT:
            - Keep it very concise
            - One key point only
            - Optional hashtags at the end
            - Total must be under 280 characters
            
            Example: 'The eUTXO model brings unprecedented precision to DeFi transactions, making Cardano a fortress of financial reliability. #Cardano #DeFi'"""
        }
        
        # Create message in thread
        message = openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompts.get(tweet_type, prompts["test"])
        )
        
        # Run the assistant
        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id="asst_5AyAw1WHxg7eOL847byMYcpr"  # Make sure this is your correct assistant ID
        )
        
        print("Waiting for response...")
        
        # Wait for response with timeout
        timeout = 30  # 30 seconds timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            run_status = openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run_status.status == 'completed':
                messages = openai_client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                tweet_text = messages.data[0].content[0].text.value
                
                # Clean and format the tweet
                cleaned_tweet = clean_tweet_text(tweet_text)
                
                if len(cleaned_tweet) > 280:
                    print(f"Tweet too long ({len(cleaned_tweet)} chars). Regenerating...")
                    return generate_and_post_tweet(client, tweet_type)
                
                print(f"\nPosting tweet: {cleaned_tweet}")
                response = client.create_tweet(text=cleaned_tweet)
                print("Tweet posted successfully!")
                return True
                
            elif run_status.status == 'failed':
                print("Failed to generate tweet - Assistant error")
                return False
                
            time.sleep(1)
            
        print("Tweet generation timed out")
        return False
            
    except Exception as e:
        print(f"Error generating/posting tweet: {e}")
        print("Full error details:", str(e))
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
    client = verify_credentials()
    if client:
        print("\nStarting Morpheus AI Twitter Bot...")
        print("1. Run in production mode (scheduled tweets)")
        print("2. Run in test mode (immediate tweet)")
        choice = input("Choose mode (1/2): ")
        
        if choice == "2":
            run_morpheus_bot(client, test_mode=True)
        else:
            print("\nCurrent schedule (PST):")
            print("- 7:00 AM  : Morning tweet (GM + insight)")
            print("- 12:00 PM : Community engagement")
            print("- 6:00 PM  : Trending topics")
            print("\nPress Ctrl+C to stop")
            print("\nNext scheduled tweet will be posted at the next scheduled hour.")
            run_morpheus_bot(client)
    else:
        print("\nBot startup cancelled due to authentication failure")