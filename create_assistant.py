from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def create_morpheus_assistant():
    """Create Morpheus AI assistant"""
    try:
        assistant = client.beta.assistants.create(
            name="Morpheus AI",
            instructions="""You are Morpheus AI, an expert in Cardano blockchain and DRMZ. 
            Your role is to provide informative and engaging content about Cardano's technology, 
            development, and community initiatives. You should be knowledgeable about blockchain 
            technology, decentralized finance, and the Cardano ecosystem.""",
            model="gpt-4-1106-preview",
            tools=[{"type": "retrieval"}]  # For accessing knowledge files
        )
        
        print(f"\nMorpheus AI Assistant created successfully!")
        print(f"Assistant ID: {assistant.id}")
        print(f"Name: {assistant.name}")
        return assistant.id
        
    except Exception as e:
        print(f"Error creating assistant: {e}")
        return None

if __name__ == "__main__":
    assistant_id = create_morpheus_assistant() 