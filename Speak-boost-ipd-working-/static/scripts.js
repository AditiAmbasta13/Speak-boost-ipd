let mediaRecorder;
let audioChunks = [];

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
        url: '/upload',
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function(data) {
            console.log(data);
            displayResults(data);
        },
        error: function(err) {
            console.error(err);
            alert('Error analyzing audio: ' + err.responseText);
        }
    });
}

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();

            audioChunks = [];
            mediaRecorder.addEventListener("dataavailable", event => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener("stop", () => {
                const audioBlob = new Blob(audioChunks);
                const audioFile = new File([audioBlob], "audio.wav", { type: 'audio/wav' });
                
                const formData = new FormData();
                formData.append('file', audioFile);
            
                fetch('/analyze_real_time', {
                    method: 'POST',
                    body: formData
                }).then(response => response.json())
                  .then(data => {
                      console.log(data);
                      displayResults(data);
                  })
                  .catch(error => {
                      console.error('Error:', error);
                      alert('Error analyzing real-time audio: ' + error.message);
                  });
            });

            document.getElementById('recordingStatus').textContent = 'Recording...';
        });
}

function stopRecording() {
    if (mediaRecorder) {
        mediaRecorder.stop();
        document.getElementById('recordingStatus').textContent = 'Recording stopped.';
    }
}

function displayResults(data) {
    displayTranscript(data.transcript);
    displayWordCount(data.word_count);
    displayFillerCount(data.filler_count);
    displayGrammaticalErrors(data.grammatical_errors);
    displayFeedback(data.feedback);
    createCharts(data);
}

function displayTranscript(transcript) {
    document.getElementById('transcript').innerHTML = `<h3>Transcript:</h3><p>${transcript}</p>`;
}

function displayWordCount(count) {
    document.getElementById('wordCount').innerHTML = `<h3>Word Count:</h3><p>${count}</p>`;
}

function displayFillerCount(count) {
    document.getElementById('fillerCount').innerHTML = `<h3>Filler Word Count:</h3><p>${count}</p>`;
}

function displayGrammaticalErrors(errors) {
    let errorsHtml = '<h3>Grammatical Errors:</h3><ul>';
    errors.forEach(error => {
        errorsHtml += `<li>${error.message} (Suggested: ${error.replacements.join(', ')})</li>`;
    });
    errorsHtml += '</ul>';
    document.getElementById('grammaticalErrors').innerHTML = errorsHtml;
}

function displayFeedback(feedback) {
    let feedbackHtml = '<h3>Feedback:</h3><ul>';
    feedback.forEach(item => {
        feedbackHtml += `<li>${item}</li>`;
    });
    feedbackHtml += '</ul>';
    document.getElementById('feedback').innerHTML = feedbackHtml;
}

function createCharts(data) {
    createChart('wordsPerMinuteChart', 'Words Per Minute', [data.words_per_minute], 'WPM');
    createChart('toneChart', 'Tone (Energy)', [data.tone.energy], 'Energy');
    createChart('pitchChart', 'Average Pitch', [data.pitch], 'Pitch');
    createChart('paceChart', 'Speech Pace', [data.pace], 'Words/Second');
    createSentimentChart('sentimentChart', data.sentiment);
}

function createChart(canvasId, label, data, labelName) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [labelName],
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

function createSentimentChart(canvasId, sentimentData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [sentimentData.positive, sentimentData.negative, sentimentData.neutral],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(255, 206, 86, 0.2)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Sentiment Analysis'
                }
            }
        }
    });
}