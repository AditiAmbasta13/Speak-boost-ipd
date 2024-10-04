import whisper
import speech_recognition as sr
import numpy as np
import io
import re
import soundfile as sf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import language_tool_python

# Load the Whisper model
model = whisper.load_model("base")

def whisper_speech_to_text(audio_data):
    audio_np, _ = sf.read(io.BytesIO(audio_data), dtype='float32')
    result = model.transcribe(audio_np, fp16=False)
    return result['text']

def count_words(text):
    return len(text.split())

def calculate_pace(word_count, duration):
    if duration == 0:
        return 0
    return (word_count / duration) * 60  # words per minute

def detect_fillers(text):
    pattern = r'\b(?:um|uh|like|you know|so|aaaa|uhmmmm|mmm)\b'
    filler_words = re.findall(pattern, text, re.IGNORECASE)
    return len(filler_words), filler_words

def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)
    return score['compound'], score

def get_grammar_feedback(text):
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    corrected_text = tool.correct(text)
    return len(matches), [match.message for match in matches], corrected_text

# Function to provide suggestions based on metrics
def provide_suggestions(pace, filler_count, sentiment_score, grammar_errors):
    suggestions = []
    
    # Pace suggestions
    if pace < 120:
        suggestions.append("Your pace is too slow. Try to maintain a quicker rhythm to engage your audience.")
    elif pace > 160:
        suggestions.append("Your pace is too fast. Slow down to allow your audience to absorb the information.")
    else:
        suggestions.append("Your pace is ideal for effective communication.")

    # Filler words suggestions
    if filler_count > 0:
        suggestions.append(f"You used {filler_count} filler words: {', '.join(fillers_used)}. Practice pausing instead of using fillers when you think.")
    
    # Sentiment suggestions
    if sentiment_score < 0:
        suggestions.append("Your speech sentiment is negative. Consider using more positive language to encourage your audience.")
    elif sentiment_score > 0:
        suggestions.append("Your speech sentiment is positive, which is great! Keep it up!")

    # Grammar suggestions
    if grammar_errors > 0:
        suggestions.append(f"You have {grammar_errors} grammar issues. Review the feedback and practice these structures for clarity.")

    return suggestions

recognizer = sr.Recognizer()
mic = sr.Microphone()

print("Please start speaking...")

try:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        audio = recognizer.listen(source, timeout=10)
        audio_data = audio.get_wav_data()

        text = whisper_speech_to_text(audio_data)
        print(f"Recognized Text with Punctuation: {text}")

        duration = len(audio.frame_data) / audio.sample_rate / audio.sample_width
        word_count = count_words(text)
        filler_count, fillers_used = detect_fillers(text)
        pace = calculate_pace(word_count, duration)
        sentiment_score, sentiment_details = analyze_sentiment(text)
        grammar_errors, grammar_feedback, corrected_text = get_grammar_feedback(text)

        # Display results
        print(f"Word Count: {word_count}")
        print(f"Filler Words Count: {filler_count} ({', '.join(fillers_used)})")
        print(f"Speech Pace: {pace:.2f} words per minute.")
        print(f"Sentiment Analysis: {'Positive' if sentiment_score > 0 else 'Negative' if sentiment_score < 0 else 'Neutral'}")
        print(f"Detailed Sentiment Scores: {sentiment_details}")
        print(f"Grammar Errors: {grammar_errors}")
        print(f"Grammar Feedback: {', '.join(grammar_feedback)}")
        print(f"Corrected Text: {corrected_text}")

        # Provide suggestions for improvement
        suggestions = provide_suggestions(pace, filler_count, sentiment_score, grammar_errors)
        print("Suggestions for Improvement:")
        for suggestion in suggestions:
            print(f"- {suggestion}")

except sr.UnknownValueError:
    print("Sorry, could not understand the audio.")
except sr.RequestError:
    print("Sorry, there was an error with the request.")
except Exception as e:
    print(f"An error occurred: {e}")