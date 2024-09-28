from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Route to render the HTML page
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle speech analysis request
@app.route('/analyze_speech', methods=['POST'])
def analyze_speech():
    data = request.get_json()
    pace_value = data.get('pace', 'Unknown')
    # Here, you can add logic to process the pace value, e.g., slow, medium, fast
    return jsonify({'message': f'Pace received: {pace_value}'})

if __name__ == '__main__':
    app.run(debug=True)
