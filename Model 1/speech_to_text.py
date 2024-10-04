import speech_recognition as sr
import time
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import language_tool_python

# Function to count words
def count_words(text):
    return len(text.split())

# Function to calculate pace
def calculate_pace(word_count, duration):
    if duration == 0:
        return 0
    return (word_count / duration) * 60  # words per minute

# Function to detect filler words
def detect_fillers(text):
    pattern = r'\b(?:um|uh|like|you know|so|aaaa|uhmmmm|mmm)\b'
    filler_words = re.findall(pattern, text, re.IGNORECASE)
    return len(filler_words)

# Function to analyze sentiment
def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)
    return score['compound']

# Function to get grammatical feedback
def get_grammar_feedback(text):
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    return len(matches), [match.message for match in matches]

# Initialize the recognizer and microphone
recognizer = sr.Recognizer()
mic = sr.Microphone()

print("Please start speaking...")

try:
    with mic as source:
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source)
        
        # Record audio
        print("Listening...")
        audio = recognizer.listen(source, timeout=10)  # Listen for up to 10 seconds

        # Recognize speech using Google Web Speech API
        text = recognizer.recognize_google(audio)
        print(f"Recognized Text: {text}")

        # Calculate duration of spoken audio
        duration = len(audio.frame_data) / audio.sample_rate / audio.sample_width  # Duration in seconds

        # Count words, fillers, and calculate pace
        word_count = count_words(text)
        filler_count = detect_fillers(text)
        pace = calculate_pace(word_count, duration)
        sentiment = analyze_sentiment(text)
        grammar_errors, grammar_feedback = get_grammar_feedback(text)

        # Print results
        print(f"Word Count: {word_count}")
        print(f"Filler Words Count: {filler_count}")
        print(f"Speech Pace: {pace:.2f} words per minute")
        print(f"Sentiment Analysis: {'Positive' if sentiment > 0 else 'Negative' if sentiment < 0 else 'Neutral'}")
        print(f"Grammar Errors: {grammar_errors}")
        print(f"Grammar Feedback: {', '.join(grammar_feedback)}")

except sr.UnknownValueError:
    print("Sorry, could not understand the audio.")
except sr.RequestError:
    print("Sorry, there was an error with the request.")
except Exception as e:
    print(f"An error occurred: {e}")
