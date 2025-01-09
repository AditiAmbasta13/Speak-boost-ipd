from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import os
import json
import tempfile
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import librosa
from datetime import datetime

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# Configuration
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

# Initialize MySQL and OpenAI
mysql = MySQL(app)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Communication scenarios configuration
COMMUNICATION_SCENARIOS = {
    'interview': {
        'title': 'Job Interview',
        'description': 'Practice common interview questions and responses',
        'prompts': [
            'Tell me about yourself and your professional background.',
            'What are your greatest strengths and weaknesses?',
            'Where do you see yourself in five years?'
        ],
        'metrics': {
            'target_wpm': (130, 150),
            'tone': 'professional and confident',
            'key_points': ['clear articulation', 'structured responses', 'positive attitude']
        }
    },
    'presentation': {
        'title': 'Business Presentation',
        'description': 'Practice delivering engaging presentations',
        'prompts': [
            'Present a project proposal to stakeholders',
            'Give a quarterly business update',
            'Pitch a new product or service'
        ],
        'metrics': {
            'target_wpm': (140, 160),
            'tone': 'authoritative and engaging',
            'key_points': ['clear structure', 'engaging delivery', 'audience awareness']
        }
    },
    'negotiation': {
        'title': 'Business Negotiation',
        'description': 'Practice negotiation skills and techniques',
        'prompts': [
            'Negotiate a salary increase',
            'Discuss contract terms with a client',
            'Resolve a business conflict'
        ],
        'metrics': {
            'target_wpm': (120, 140),
            'tone': 'assertive yet diplomatic',
            'key_points': ['active listening', 'clear objectives', 'win-win solutions']
        }
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_scenarios')
def get_scenarios():
    """Return available communication scenarios"""
    return jsonify(COMMUNICATION_SCENARIOS)

@app.route('/analyze_speech', methods=['POST'])
def analyze_speech():
    """Analyze real-time speech using OpenAI"""
    if 'user_id' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
        
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    scenario_id = request.form.get('scenario')
    if scenario_id not in COMMUNICATION_SCENARIOS:
        return jsonify({'error': 'Invalid scenario'}), 400

    try:
        audio_file = request.files['audio']
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            audio_file.save(temp_audio.name)
            
            # Get audio duration and properties
            duration = librosa.get_duration(path=temp_audio.name)
            
            # Transcribe with Whisper
            with open(temp_audio.name, "rb") as audio:
                transcript_response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                )
            transcript = transcript_response.text

            # Calculate basic metrics
            words = len(transcript.split())
            wpm = (words / duration) * 60 if duration > 0 else 0

            # Analyze with GPT-4
            scenario = COMMUNICATION_SCENARIOS[scenario_id]
            analysis_prompt = f"""
            Analyze this speech for a {scenario['title']} scenario:
            "{transcript}"
            
            Target metrics:
            - WPM: {scenario['metrics']['target_wpm']}
            - Desired tone: {scenario['metrics']['tone']}
            - Key points: {', '.join(scenario['metrics']['key_points'])}
            
            Provide analysis in this JSON format:
            {{
                "metrics": {{
                    "clarity": <score 1-10>,
                    "confidence": <score 1-10>,
                    "professionalism": <score 1-10>,
                    "engagement": <score 1-10>
                }},
                "tone_analysis": "<brief analysis of tone and delivery>",
                "strengths": ["<key strength>", ...],
                "areas_for_improvement": ["<specific suggestion>", ...],
                "recommended_phrases": ["<better phrasing example>", ...],
                "voice_coaching_tips": ["<specific vocal technique tip>", ...],
                "grammar": {{
                    "score": <score 1-10>,
                    "issues": ["<description of grammar issue>", ...],
                    "suggestions": ["<corrected version>", ...]
                }}
            }}
            """

            analysis_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert communication coach."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7
            )

            # Parse GPT-4 analysis
            analysis = json.loads(analysis_response.choices[0].message.content)

            # Generate voice feedback
            feedback_prompt = f"""
            Based on the analysis, create a brief, encouraging voice coaching feedback
            that addresses the key points and suggests improvements. Keep it under 100 words
            and use a supportive, coaching tone.
            """

            feedback_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a supportive voice coach."},
                    {"role": "user", "content": feedback_prompt}
                ],
                temperature=0.7
            )

            voice_feedback = feedback_response.choices[0].message.content

            # Save analysis to database
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO speech_analysis_reports 
                (user_id, scenario_id, transcript, words_per_minute, duration,
                speaking_clarity, speaking_confidence, speaking_professionalism,
                tone_analysis, strengths, areas_for_improvement,
                recommended_phrases, voice_coaching_tips, sentiment_analysis,
                structure_feedback, audio_duration)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session['user_id'],
                scenario_id,
                transcript,
                wpm,
                duration,
                analysis['metrics']['clarity'],
                analysis['metrics']['confidence'],
                analysis['metrics']['professionalism'],
                analysis['tone_analysis'],
                json.dumps(analysis['strengths']),
                json.dumps(analysis['areas_for_improvement']),
                json.dumps(analysis['recommended_phrases']),
                json.dumps(analysis['voice_coaching_tips']),
                voice_feedback,
                analysis['tone_analysis'],
                duration
            ))
            mysql.connection.commit()
            cur.close()

            # Prepare response
            results = {
                'transcript': transcript,
                'wpm': wpm,
                'duration': duration,
                'analysis': analysis,
                'voice_feedback': voice_feedback,
                'scenario': scenario['title']
            }

            return jsonify(results)

    except Exception as e:
        print(f"Error in speech analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup temporary file
        if 'temp_audio' in locals():
            os.unlink(temp_audio.name)

@app.route('/speech-analysis')
def speech_analysis():
    """Render the speech analysis page"""
    if 'user_id' not in session:
        flash("Please log in to access speech analysis.", "warning")
        return redirect(url_for('login'))
    
    # Fetch user data for the sidebar
    cur = mysql.connection.cursor()
    cur.execute("SELECT username, avatar_url FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    
    username = user[0] if user else "Unknown"
    avatar_url = user[1] if user and user[1] else 'https://api.multiavatar.com/default.svg'
    
    return render_template('speech_analysis.html', 
                         username=username, 
                         avatar_url=avatar_url)

# Keep existing routes for login, register, etc.