import json
from groq import Groq

class AIHandler:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.system_prompt = """
        You are Nova, a highly intelligent virtual assistant. 
        Your task is to parse user commands and return a JSON object with the following structure:
        {
            "action": "play_song", "browse", "open_youtube_channel", "weather", "open_website", or "general_query",
            "query": "the search string, song name, location for weather, or website name (leave empty if not applicable)",
            "response": "a very short, witty, and helpful response that you will say to the user"
        }
        
        Examples:
        User: "Play some Bohemian Rhapsody"
        Response: {"action": "play_song", "query": "Bohemian Rhapsody", "response": "Certainly. Playing Bohemian Rhapsody on YouTube."}
        
        User: "Search for the latest space news"
        Response: {"action": "browse", "query": "latest space news", "response": "Searching the web for the latest in space exploration."}

        User: "What's the weather in London?"
        Response: {"action": "weather", "query": "London", "response": "Checking the forecast for London. I hope it's sunny!"}
        
        User: "Open Amazon"
        Response: {"action": "open_website", "query": "amazon", "response": "Opening Amazon for you."}

        User: "Open MrBeast's YouTube channel"
        Response: {"action": "open_youtube_channel", "query": "MrBeast", "response": "Opening MrBeast's channel for you."}
        
        User: "What is the capital of France?"
        Response: {"action": "general_query", "query": "", "response": "The capital of France is Paris."}
        
        Keep responses conversational and helpful. If asked for information, project ideas, or complex topics, provide a few detailed bullet points or a clear explanation. For simple tasks like opening apps, weather, websites, or playing songs, stay concise.
        """

    def process_command(self, user_command):
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile", # Using a highly capable Groq model
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_command}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            print(f"Groq AI Error: {e}")
            return {
                "action": "general_query",
                "query": "",
                "response": "I'm sorry, I'm having trouble processing that right now."
            }
