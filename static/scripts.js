let audioBlob;

function uploadAudio() {
    var fileInput = document.getElementById('audioUpload');
    var audioFile = fileInput.files[0];

    if (!audioFile) {
        alert('Please upload an audio file!');
        return;
    }

    var formData = new FormData();
    formData.append('file', audioFile);

    $.ajax({
        url: '/upload',  // Make sure this matches your Flask route
        type: 'POST',    // Ensure it's a POST request
        data: formData,
        contentType: false,
        processData: false,
        success: function(data) {
            console.log(data);
            displayResults(data); // Display charts
            displayTranscript(data.transcript); // Display transcript
        },
        error: function(err) {
            console.error(err);
            alert('Error analyzing audio: ' + err.responseText); // Show the server error
        }
    });
}

function displayTranscript(transcript) {
    const transcriptDiv = document.getElementById('transcript');
    transcriptDiv.innerHTML = `<h3>Transcript:</h3><p>${transcript}</p>`;
}


function displayResults(data) {
    // Prepare data for charts
    const wordsPerMinuteData = [data.words_per_minute]; // Example data
    const toneData = data.tone; // Tone distribution
    const pitchData = data.pitch; // Pitch levels
    const paceData = data.pace; // Pace levels
    const sentimentData = data.sentiment; // Sentiment analysis

    createChart('wordsPerMinuteChart', 'Words Per Minute', wordsPerMinuteData, 'WPM');
    createChart('toneChart', 'Tone Distribution', toneData, 'Tone');
    createChart('pitchChart', 'Pitch Levels', pitchData, 'Pitch');
    createChart('paceChart', 'Pace Levels', paceData, 'Pace');
    createChart('sentimentChart', 'Sentiment Analysis', sentimentData, 'Sentiment');
}

function createChart(canvasId, label, data, labelName) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: 'bar', // You can change this to 'line', 'pie', etc.
        data: {
            labels: ['Value'],
            datasets: [{
                label: label,
                data: data,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Implement startRecording and stopRecording functions here as needed
let mediaRecorder;
let audioChunks = [];

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const audioFile = new File([audioBlob], "audio.wav", { type: 'audio/wav' });
            
                // Send the file to the server for real-time analysis
                const formData = new FormData();
                formData.append('file', audioFile);
            
                fetch('/analyze_real_time', {
                    method: 'POST',
                    body: formData
                }).then(response => response.json())
                  .then(data => {
                      console.log(data);  // For debugging
                      // Reuse the same functions for displaying results and transcript as for the uploaded file
                      displayResults(data);  // Display charts based on the returned data
                      displayTranscript(data.transcript);  // Display the transcript
                  })
                  .catch(error => {
                      console.error('Error:', error);
                      alert('Error analyzing real-time audio: ' + error.message);
                  });
            };
            
        });
}

function stopRecording() {
    mediaRecorder.stop();
}
