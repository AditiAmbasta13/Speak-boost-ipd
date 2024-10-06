from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import os
import numpy as np
from scipy.io import wavfile
from nltk.sentiment import SentimentIntensityAnalyzer
import librosa
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)

# Ensure the uploads directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Convert float32 values to float to ensure JSON serialization
def convert_floats(obj):
    if isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats(i) for i in obj]
    elif isinstance(obj, np.float32):
        return float(obj)
    return obj

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    audio_file = request.files['file']

    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    audio_file_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)

    try:
        audio_file.save(audio_file_path)
        
        # Analyze the uploaded audio file
        transcript, analysis_result = analyze_audio(audio_file_path)

        # Ensure that any float32 values are converted
        response_data = {
            'transcript': transcript,
            **convert_floats(analysis_result)
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Return the error message


@app.route('/analyze_real_time', methods=['POST'])
def analyze_real_time():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    audio_file = request.files['file']

    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    audio_file_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)

    try:
        # Save the uploaded file
        audio_file.save(audio_file_path)

        # Log the file type for debugging purposes
        print(f"File type: {audio_file.content_type}")
        print(f"File size: {os.path.getsize(audio_file_path)} bytes")
        
        # Ensure the file is a valid WAV format by converting to standard WAV
        audio = AudioSegment.from_file(audio_file_path)
        converted_audio_path = audio_file_path.replace(".wav", "_converted.wav")
        audio.export(converted_audio_path, format="wav")

        # Now analyze the properly converted WAV file
        transcript, analysis_result = analyze_audio(converted_audio_path)

        # Convert float32 values before returning
        response_data = {
            'transcript': transcript,
            **convert_floats(analysis_result)
        }

        return jsonify(response_data), 200

    except Exception as e:
        # Log the error to help with debugging
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500




def analyze_audio(file_path):
    recognizer = sr.Recognizer()
    # Get transcript from audio
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)  # Read the entire audio file
        try:
            # Use Google Web Speech API for transcription
            transcript = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            transcript = "Could not understand audio."
        except sr.RequestError:
            transcript = "Could not request results from the service."

    # Perform actual analysis
    analysis = {
        'words_per_minute': calculate_wpm(transcript, file_path),
        'tone': analyze_tone(file_path),  # Analyze tone
        'pitch': analyze_pitch(file_path),  # Analyze pitch
        'pace': analyze_pace(transcript),  # Analyze pace
        'sentiment': analyze_sentiment(transcript)  # Analyze sentiment
    }

    return transcript, analysis

def calculate_wpm(transcript, file_path):
    words = len(transcript.split())
    # Get audio duration in seconds
    sample_rate, samples = wavfile.read(file_path)
    duration = len(samples) / sample_rate  # Duration in seconds
    wpm = words / (duration / 60)
    return wpm

def analyze_tone(file_path):
    # Load the audio file
    y, sr = librosa.load(file_path)
    
    # Calculate the energy of the audio signal
    energy = np.mean(librosa.feature.rms(y=y))

    # Tone can be represented by energy levels
    tone_analysis = {
        'energy': energy
    }
    return tone_analysis

def analyze_pitch(file_path):
    # Load the audio file
    y, sr = librosa.load(file_path)

    # Extract pitches
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

    # Calculate average pitch
    avg_pitch = np.mean(pitches[pitches > 0])  # Ignore zero values
    return avg_pitch

def analyze_pace(transcript):
    words = len(transcript.split())
    return words / (len(transcript.split()) * 0.5)  # Average pace as words per second

def analyze_sentiment(transcript):
    sia = SentimentIntensityAnalyzer()
    sentiment = sia.polarity_scores(transcript)
    return {
        'positive': sentiment['pos'],
        'negative': sentiment['neg'],
        'neutral': sentiment['neu'],
        'compound': sentiment['compound']
    }

if __name__ == '__main__':
    app.run(debug=True)
