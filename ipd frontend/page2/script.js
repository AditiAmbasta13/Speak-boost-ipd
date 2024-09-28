// Navigation Button Interaction
const prevButton = document.querySelectorAll('.nav-button')[0];
const nextButton = document.querySelectorAll('.nav-button')[1];

// Add event listeners for navigation buttons
prevButton.addEventListener('click', () => {
    console.log('Previous button clicked');
});

nextButton.addEventListener('click', () => {
    console.log('Next button clicked');
});
