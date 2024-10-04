console.log("Script loaded");

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const recordingStatus = document.getElementById('recordingStatus');
const analysisResults = document.getElementById('analysisResults');

function startRecording() {
    console.log("startRecording called");

    // Use the default microphone
    const audioConstraints = {
        audio: true
    };

    navigator.mediaDevices.getUserMedia(audioConstraints)
        .then(stream => {
            console.log("Got media stream");
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' }); // Use supported mimeType
            mediaRecorder.start();
            isRecording = true;
            updateUI();

            mediaRecorder.addEventListener("dataavailable", event => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener("stop", () => {
                console.log("Recording stopped");
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' }); // Send in webm format
                audioChunks = [];
                sendAudioForAnalysis(audioBlob);
            });
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
            alert('Error accessing microphone. Please ensure you have given permission or check your browser settings.');
        });
}

function stopRecording() {
    console.log("stopRecording called");
    if (isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        updateUI();
    }
}

function sendAudioForAnalysis(audioBlob) {
    console.log("Sending audio for analysis");

    // Create a temporary link to check the audio format
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();

    fetch('/analyze', {
        method: 'POST',
        body: audioBlob,
        headers: {
            'Content-Type': 'application/octet-stream'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log("Analysis results received:", data);
        displayAnalysisResults(data);
    })
    .catch(error => {
        console.error('Error:', error);
        analysisResults.textContent = 'Error occurred during analysis. Please try again.';
        analysisResults.style.display = 'block';
    });
}

function displayAnalysisResults(data) {
    console.log("Displaying analysis results");
    if (data.error) {
        analysisResults.textContent = `Error: ${data.error}`;
    } else {
        analysisResults.innerHTML = `
            <h3>Recognized Text:</h3>
            <p>${data.text}</p>
            <h3>Analysis:</h3>
            <ul>
                <li>Word Count: ${data.word_count}</li>
                <li>Filler Count: ${data.filler_count}</li>
                <li>Sentiment: ${data.sentiment} (Score: ${data.sentiment_score})</li>
                <li>Grammar Errors: ${data.grammar_errors}</li>
            </ul>
            <h3>Grammar Feedback:</h3>
            <ul>
                ${data.grammar_feedback.map(feedback => `<li>${feedback}</li>`).join('')}
            </ul>
        `;
    }
    analysisResults.style.display = 'block';
}

function updateUI() {
    console.log("Updating UI, isRecording:", isRecording);
    startButton.disabled = isRecording;
    stopButton.disabled = !isRecording;
    recordingStatus.textContent = isRecording ? 'Recording...' : 'Not recording';
}

startButton.addEventListener('click', startRecording);
stopButton.addEventListener('click', stopRecording);

updateUI();
