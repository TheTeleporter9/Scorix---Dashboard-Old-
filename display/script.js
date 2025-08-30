const socket = io('http://localhost:5000');
let currentTable = '1';
let currentTeams = {
    team1: 'Team 1',
    team2: 'Team 2'
};

let displayState = 'table-select'; // New initial state
let prepTimeLeft = 90; // 90 seconds prep time
let gameTimeLeft = 120; // 120 seconds (2 min) game time
let timer = null;
let gameTimerStarted = false;

// Add new state tracking variables
let hasGameBeenSaved = false;
let latestSavedScores = null;

// DOM elements
const winnerDisplay = document.getElementById('winner-display');
const scoreDisplay = document.getElementById('score-display');
const team1Score = document.getElementById('team1-score');
const team2Score = document.getElementById('team2-score');
const winnerText = document.getElementById('winner-text');
const tableIndicator = document.getElementById('table-indicator');
const timerDisplay = document.getElementById('timer-display');

// Handle keyboard input for table selection and state changes
document.addEventListener('keydown', (event) => {
    if (displayState === 'table-select' && (event.key === '1' || event.key === '2')) {
        currentTable = event.key;
        displayState = 'prep';
        requestTableScore();
        startPrepTimer();
    } else if (event.code === 'Space' && !event.repeat) {
        event.preventDefault();
        advanceState();
    }
});

function showPage(pageId) {
    // First, start fade out of current page
    document.querySelectorAll('.page.active').forEach(page => {
        page.style.opacity = '0';
        page.style.transform = 'scale(0.95)';
        
        // After fade out, hide the page and show new one
        setTimeout(() => {
            page.classList.remove('active');
            const newPage = document.getElementById(pageId);
            newPage.classList.add('active');
            
            // Force a reflow to ensure animation plays
            newPage.offsetHeight;
            
            // Fade in new page
            newPage.style.opacity = '1';
            newPage.style.transform = 'scale(1)';
        }, 500);
    });
    
    // If no active page, show new page immediately
    if (!document.querySelector('.page.active')) {
        const newPage = document.getElementById(pageId);
        newPage.classList.add('active');
        
        // Force a reflow to ensure animation plays
        newPage.offsetHeight;
        
        // Fade in new page
        newPage.style.opacity = '1';
        newPage.style.transform = 'scale(1)';
    }
}

function advanceState() {
    switch(displayState) {
        case 'prep':
            displayState = 'game';
            showPage('game-page');
            document.getElementById('timer-display').textContent = 'Press SPACE to start';
            gameTimerStarted = false;
            hasGameBeenSaved = false; // Reset saved state for new game
            break;
        case 'game':
            if (!gameTimerStarted) {
                startGameTimer();
            } else if (hasGameBeenSaved) {
                displayState = 'winner';
                showPage('winner-page');
                showWinnerState();
            } else {
                // Show message that scores need to be saved first
                alert('Please save the game scores before showing the winner!');
            }
            break;
        case 'winner':
            displayState = 'reset';
            showPage('reset-page');
            break;
        case 'reset':
            displayState = 'prep';
            showPage('prep-page');
            resetGame();
            break;
    }
}

function startPrepTimer() {
    displayState = 'prep';
    showPage('prep-page');
    prepTimeLeft = 90;
    updateTimerDisplay(prepTimeLeft, 'prep-timer');
    
    timer = setInterval(() => {
        prepTimeLeft--;
        updateTimerDisplay(prepTimeLeft, 'prep-timer');
        
        if (prepTimeLeft <= 0) {
            clearInterval(timer);
            advanceState();
        }
    }, 1000);
}

function startGameTimer() {
    if (!gameTimerStarted) {
        gameTimerStarted = true;
        displayState = 'game';
        clearInterval(timer);
        gameTimeLeft = 120;
        updateTimerDisplay(gameTimeLeft, 'timer-display');
        
        timer = setInterval(() => {
            gameTimeLeft--;
            updateTimerDisplay(gameTimeLeft, 'timer-display');
            
            if (gameTimeLeft <= 0) {
                clearInterval(timer);
                if (hasGameBeenSaved) {
                    showWinnerState();
                } else {
                    document.getElementById('timer-display').textContent = 'Save scores to see winner';
                }
            }
        }, 1000);
    }
}

function showWinnerState() {
    if (!hasGameBeenSaved) {
        alert('Please save the game scores before showing the winner!');
        return; // Don't proceed if game hasn't been saved
    }
    displayState = 'winner';
    clearInterval(timer);
    showPage('winner-page');
    
    // Get the latest scores from the server for the current table
    socket.emit('requestTableScore', { table: currentTable });
}

function resetGame() {
    displayState = 'prep';
    clearInterval(timer);
    startPrepTimer();
}

function updateTimerDisplay(seconds, elementId) {
    const timerElement = document.getElementById(elementId);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    timerElement.textContent = 
        `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Update the showWinner function
function showWinner(winner) {
    document.getElementById('winner-text').textContent = `${winner} Wins!`;
}

// Request score for current table
function requestTableScore() {
    socket.emit('requestTableScore', { table: currentTable });
}

// Handle score updates from server
socket.on('scoreUpdate', (data) => {
    if (data.table === currentTable) {
        const scores = data.scores;
        
        // Update team names
        if (scores.team1Name) {
            currentTeams.team1 = scores.team1Name;
            document.getElementById('team1-name').textContent = scores.team1Name;
        }
        if (scores.team2Name) {
            currentTeams.team2 = scores.team2Name;
            document.getElementById('team2-name').textContent = scores.team2Name;
        }

        // Update hasGameBeenSaved status
        hasGameBeenSaved = scores.hasBeenSaved;

        // Update scores if in game state
        if (displayState === 'game' && gameTimerStarted) {
            team1Score.textContent = scores.team1;
            team2Score.textContent = scores.team2;
        }
        
        // Show winner if in winner state
        if (displayState === 'winner') {
            if (scores.team1 > scores.team2) {
                showWinner(currentTeams.team1);
            } else if (scores.team2 > scores.team1) {
                showWinner(currentTeams.team2);
            } else {
                showWinner("It's a tie!");
            }
        }
    }
});

// Request initial score on connection
socket.on('connect', () => {
    requestTableScore();
});

// Add listener for game save completion
socket.on('savingComplete', (response) => {
    if (response.status === 'success') {
        hasGameBeenSaved = true;
        // Only proceed to winner state if timer is finished AND we're trying to show winner
        if (gameTimeLeft <= 0 && displayState === 'winner') {
            showWinnerState();
        }
    }
});

// Initialize with table select page instead of prep timer
showPage('table-select-page'); 