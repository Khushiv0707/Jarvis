import time
import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
import pygame
import os
import pywhatkit
from gtts import gTTS
from colorama import init, Fore, Style
from ai_handler import AIHandler
from dotenv import load_dotenv
load_dotenv()

# Initialize colorama
init(autoreset=True)

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Initialize AI Handler
ai_handler = AIHandler(GROQ_API_KEY)

def speak(text):
    print(f"{Fore.CYAN}Nova: {Style.BRIGHT}{text}")
    try:
        tts = gTTS(text)
        tts.save('temp.mp3') 
        pygame.mixer.init()
        pygame.mixer.music.load('temp.mp3')
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        os.remove("temp.mp3") 
        time.sleep(0.3) # Short delay to let audio finish cleanly
    except Exception as e:
        print(f"{Fore.RED}TTS Error: {e}")
        # Fallback to pyttsx3 if gTTS fails
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

def processCommand(command):
    print(f"{Fore.YELLOW}Processing: {Style.DIM}{command}")
    
    # Try AI first
    result = ai_handler.process_command(command)
    action = result.get("action")
    query = result.get("query")
    response = result.get("response")

    # If AI fails (quota exceeded), use Fallback Logic
    if "trouble processing" in response:
        print(f"{Fore.RED}AI Error detected. Using Fallback Logic...")
        command_lower = command.lower()
        
        if command_lower.startswith("play"):
            song_name = command_lower.replace("play", "").strip()
            speak(f"AI is offline, but I'll play {song_name} for you.")
            pywhatkit.playonyt(song_name)
            return
        elif "search" in command_lower or "browse" in command_lower:
            search_query = command_lower.replace("search", "").replace("browse", "").strip()
            speak(f"Searching the web for {search_query}.")
            webbrowser.open(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")
            return
        elif "open" in command_lower:
            site = command_lower.replace("open", "").replace("website", "").strip()
            speak(f"Opening {site}.")
            webbrowser.open(f"https://{site.replace(' ', '')}.com")
            return
        elif "news" in command_lower:
            fetch_news()
            return
        elif "weather" in command_lower:
            if "weather in" in command_lower:
                location = command_lower.split("weather in")[-1].strip()
            elif "weather of" in command_lower:
                location = command_lower.split("weather of")[-1].strip()
            else:
                location = command_lower.replace("weather", "").strip()
            
            location = location.title() # Capitalize like "Delhi"
            speak(f"AI is offline, but I'll find the weather for {location} for you.")
            webbrowser.open(f"https://www.google.com/search?q=weather+in+{location.replace(' ', '+')}")
            return
        else:
            speak("I'm sorry, my AI is currently offline due to quota limits, and I didn't recognize that basic command.")
            return

    speak(response)

    if action == "play_song":
        pywhatkit.playonyt(query)
    elif action == "browse":
        search_query = query.replace(" ", "+")
        webbrowser.open(f"https://www.google.com/search?q={search_query}")
    elif action == "open_youtube_channel":
        search_query = query.replace(" ", "+") + "+channel"
        webbrowser.open(f"https://www.youtube.com/results?search_query={search_query}")
    elif action == "weather":
        search_query = f"weather+in+{query.replace(' ', '+')}" if query else "weather"
        webbrowser.open(f"https://www.google.com/search?q={search_query}")
    elif action == "open_website":
        site = query.lower().replace("website", "").replace(" ", "").strip()
        if not site.endswith((".com", ".org", ".net", ".in", ".edu", ".gov")):
            site = site + ".com"
        webbrowser.open(f"https://{site}")
    elif action == "general_query":
        # Response is already spoken by Jarvis
        pass
    
    # Special case for news if user specifically asks
    if "news" in command.lower():
        fetch_news()

def fetch_news():
    r = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}")
    if r.status_code == 200:
        data = r.json()
        articles = data.get('articles', [])
        speak("Here are the top headlines.")
        for i, article in enumerate(articles[:3]): # Speak top 3 news
            speak(f"Headline {i+1}: {article['title']}")

if __name__ == "__main__":
    recognizer = sr.Recognizer()
    
    # This prevents Nova from cutting you off too early
    # 5.0 seconds of silence required to end a phrase
    recognizer.pause_threshold = 3.0 
    recognizer.non_speaking_duration = 0.5

    # Initial calibration
    with sr.Microphone() as source:
        print(f"{Fore.CYAN}Nova: {Style.BRIGHT}Calibrating microphone... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    speak("Nova is online and ready.")
    
    while True:
        try:
            with sr.Microphone() as source:
                print(f"\n{Fore.GREEN}Listening for wake word 'Hi Nova'...")
                # Removed frequent adjustment here to keep threshold stable
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
            
            word = recognizer.recognize_google(audio).lower()
            
            if "hi nova" in word or "hii nova" in word:
                speak("I am here. How can I help?")
                
                # Continuous conversation loop
                while True:
                    try:
                        with sr.Microphone() as source:
                            print(f"{Fore.BLUE}Listening for command...")
                            # 30s to start speaking, 20s total speech length
                            audio = recognizer.listen(source, timeout=30, phrase_time_limit=20)
                            command = recognizer.recognize_google(audio)
                            
                            print(f"{Fore.WHITE}You said: {command}")
                            
                            # Check if user wants to stop the conversation
                            if any(exit_word in command.lower() for exit_word in ["stop", "go to sleep", "thank you", "bye", "goodbye"]):
                                speak("Alright, let me know if you need anything else. Going to sleep.")
                                break # Exit inner loop back to wake word
                            
                            processCommand(command)

                    except sr.WaitTimeoutError:
                        print(f"{Fore.YELLOW}No command detected. Going back to sleep.")
                        break # Exit inner loop back to wake word
                    except sr.UnknownValueError:
                        print(f"{Fore.RED}Could not understand audio. Still listening...")
                        # We stay in the loop to try again
                    except Exception as e:
                        print(f"{Fore.RED}Error in conversation: {e}")
                        break

        except sr.UnknownValueError:
            pass # Ignore if it doesn't understand anything
        except sr.WaitTimeoutError:
            pass # Ignore timeout
        except Exception as e:
            print(f"{Fore.RED}Error: {e}")
            time.sleep(1)
