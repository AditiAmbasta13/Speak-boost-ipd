document.getElementById('analyzeButton').addEventListener('click', function() {
    // Get the pace value from the input
    const pace = document.getElementById('paceInput').value;

    // Send a POST request to the Flask backend
    fetch('/analyze_speech', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pace: pace })
    })
    .then(response => response.json())
    .then(data => {
        // Display the result in the page
        document.getElementById('result').innerText = data.message;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
