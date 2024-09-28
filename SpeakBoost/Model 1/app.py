from flask import Flask, render_template, request, jsonify, send_from_directory
import speech_recognition as sr
import nltk
from io import BytesIO
from textblob import TextBlob
import language_tool_python
from pydub import AudioSegment
import os

app = Flask(__name__, static_folder='static')

# Ensure nltk resources are downloaded
nltk.download('punkt')

# Initialize LanguageTool for grammar checking
tool = language_tool_python.LanguageTool('en-US')

def analyze_audio(audio_data):
    # Convert audio data (bytes) to an AudioFile
    audio_file = BytesIO(audio_data)
    
    # Convert to WAV format using pydub (from webm/ogg to wav)
    try:
        sound = AudioSegment.from_file(audio_file, format="webm")  # or 'ogg' depending on what browser sends
        wav_io = BytesIO()
        sound.export(wav_io, format="wav")
        wav_io.seek(0)
        
        # Now use speech_recognition with WAV format
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio = recognizer.record(source)
    except Exception as e:
        return {"error": f"Error processing audio file: {str(e)}"}
    
    # Recognize speech using Google Web Speech API
    try:
        text = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return {"error": "Could not understand audio"}
    except sr.RequestError:
        return {"error": "Could not request results from Google Web Speech API"}
    
    # Text analysis
    words = nltk.word_tokenize(text)
    word_count = len(words)
    filler_words = ['um', 'uh', 'like', 'you know', 'actually']
    filler_count = sum(1 for word in words if word.lower() in filler_words)
    
    # Sentiment analysis using TextBlob
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    
    # Grammar check using LanguageTool
    matches = tool.check(text)
    grammar_errors = len(matches)
    grammar_feedback = [match.message for match in matches[:3]]  # Limit to top 3 errors
    
    return {
        'text': text,
        'word_count': word_count,
        'filler_count': filler_count,
        'sentiment': 'Positive' if sentiment > 0.1 else 'Negative' if sentiment < -0.1 else 'Neutral',
        'sentiment_score': round(sentiment, 2),
        'grammar_errors': grammar_errors,
        'grammar_feedback': grammar_feedback,
    }

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze_page():
    if request.method == 'GET':
        return render_template('analyze.html')
    elif request.method == 'POST':
        audio_data = request.data
        if not audio_data:
            return jsonify({"error": "No audio data provided"}), 400
        
        result = analyze_audio(audio_data)
        return jsonify(result)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)
