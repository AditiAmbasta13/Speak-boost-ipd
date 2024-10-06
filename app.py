import whisper
import speech_recognition as sr
import numpy as np
import io
import re
import soundfile as sf
from flask import Flask, request, jsonify, render_template
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import language_tool_python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the Whisper model
model = whisper.load_model("base")

def whisper_speech_to_text(audio_data):
    audio_np, sample_rate = sf.read(io.BytesIO(audio_data), dtype='float32')
    result = model.transcribe(audio_np, fp16=False)
    return result['text'], len(audio_np) / sample_rate

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
    return score['compound']

def get_grammar_feedback(text):
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    corrected_text = tool.correct(text)
    return len(matches), [match.message for match in matches], corrected_text

def provide_suggestions(pace, filler_count, sentiment_score, grammar_errors):
    suggestions = []
    
    if pace < 120:
        suggestions.append("Your pace is too slow. Try to maintain a quicker rhythm to engage your audience.")
    elif pace > 160:
        suggestions.append("Your pace is too fast. Slow down to allow your audience to absorb the information.")
    else:
        suggestions.append("Your pace is ideal for effective communication.")

    if filler_count > 0:
        suggestions.append(f"You used {filler_count} filler words. Practice pausing instead of using fillers when you think.")
    
    if sentiment_score < -0.05:
        suggestions.append("Your speech sentiment is negative. Consider using more positive language to encourage your audience.")
    elif sentiment_score > 0.05:
        suggestions.append("Your speech sentiment is positive, which is great! Keep it up!")
    else:
        suggestions.append("Your speech sentiment is neutral. Consider adding more emotional emphasis where appropriate.")

    if grammar_errors > 0:
        suggestions.append(f"You have {grammar_errors} grammar issues. Review the feedback and practice these structures for clarity.")

    return suggestions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    audio_file = request.files['file']
    
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if audio_file:
        audio_data = audio_file.read()
        
        try:
            text, duration = whisper_speech_to_text(audio_data)
            word_count = count_words(text)
            filler_count, fillers_used = detect_fillers(text)
            pace = calculate_pace(word_count, duration)
            sentiment_score = analyze_sentiment(text)
            grammar_errors, grammar_feedback, corrected_text = get_grammar_feedback(text)

            suggestions = provide_suggestions(pace, filler_count, sentiment_score, grammar_errors)

            return jsonify({
                'text': text,
                'word_count': word_count,
                'filler_count': filler_count,
                'filler_words': fillers_used,
                'pace': pace,
                'sentiment_score': sentiment_score,
                'grammar_errors': grammar_errors,
                'grammar_feedback': grammar_feedback,
                'corrected_text': corrected_text,
                'suggestions': suggestions
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)