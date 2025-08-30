const socket = io('http://localhost:5000');

let gameState = {
    gameNumber: '',
    team1: {
        name: '',
        orange: 0,
        purple: 0,
        penalties: [],
        score: 0
    },
    team2: {
        name: '',
        orange: 0,
        purple: 0,
        penalties: [],
        score: 0
    }
};

// Initialize DOM elements
const elements = {
    gameNumber: document.getElementById('gameNumber'),
    team1Name: document.getElementById('team1Name'),
    team2Name: document.getElementById('team2Name'),
    team1Score: document.getElementById('team1-score'),
    team2Score: document.getElementById('team2-score'),
    team1Orange: document.getElementById('team1-orange'),
    team2Orange: document.getElementById('team2-orange'),
    team1Purple: document.getElementById('team1-purple'),
    team2Purple: document.getElementById('team2-purple'),
    team1Penalty: document.getElementById('team1Penalty'),
    team2Penalty: document.getElementById('team2Penalty')
};

// Update the scoring constants and calculation
const SCORING = {
    ORANGE_BALL: 1,     // Orange ball on opponent's half = 1 point
    PURPLE_BALL: -2     // Purple ball on opponent's half = -2 points
};

const PENALTY_VALUES = {
    touching_robot: -30,    // Touching robot during match
    robot_outside: -30,     // Robot completely outside the field
    ball_thrown: -30,       // Ball thrown over the wall
    wrong_start: -10,       // Wrong starting position
    ball_outside: -10,      // Ball outside the field
    illegal_action: -30,    // Any illegal action
    late_start: -30         // Late start
};

// Add timeout constant at the top with other constants
const SAVE_TIMEOUT = 5000; // 5 seconds timeout

// Update balls count and recalculate score
function updateBalls(team, color, increment) {
    const teamData = gameState[team];
    teamData[color] = Math.max(0, teamData[color] + increment);
    updateDisplay();
    calculateScores();
}

// Calculate scores based on WRO Double Tennis rules
function calculateScores() {
    for (const team of ['team1', 'team2']) {
        const teamData = gameState[team];
        let score = 0;
        
        // Orange balls (should be on opponent's half)
        score += teamData.orange * SCORING.ORANGE_BALL;
        
        // Purple balls (should be on own half, negative points if on opponent's half)
        score += teamData.purple * SCORING.PURPLE_BALL;
        
        // Apply penalties
        teamData.penalties.forEach(penalty => {
            score += PENALTY_VALUES[penalty] || 0;
        });
        
        // Final score cannot be negative
        teamData.score = Math.max(0, score);
    }
    
    updateDisplay();
    sendScoreUpdate(); // Send immediate update to server
}

// Update display with current state
function updateDisplay() {
    elements.team1Orange.textContent = gameState.team1.orange;
    elements.team2Orange.textContent = gameState.team2.orange;
    elements.team1Purple.textContent = gameState.team1.purple;
    elements.team2Purple.textContent = gameState.team2.purple;
    elements.team1Score.textContent = gameState.team1.score;
    elements.team2Score.textContent = gameState.team2.score;
}

// Add these new functions to handle penalties display

function togglePenaltyDropdown(team) {
    const clickedDropdown = elements[team + 'Penalty'];
    
    // Close other dropdown first
    const otherTeam = team === 'team1' ? 'team2' : 'team1';
    elements[otherTeam + 'Penalty'].style.display = 'none';
    
    // Toggle clicked dropdown
    clickedDropdown.style.display = clickedDropdown.style.display === 'none' ? 'block' : 'none';
    
    // Prevent the click from immediately closing the dropdown
    event.stopPropagation();
}

function updatePenaltyDisplay(team) {
    const penalties = gameState[team].penalties;
    const container = document.getElementById(team + '-active-penalties');
    container.innerHTML = '';
    
    const penaltyLabels = {
        'touching_robot': 'Touching Robot (-30)',
        'robot_outside': 'Robot Outside Field (-30)',
        'intentional_damage': 'Intentional Damage (-30)',
        'ball_thrown': 'Ball Thrown (-30)',
        'robot_modification': 'Robot Modified (-30)',
        'restart_match': 'Match Restart (-50)',
        'field_damage': 'Field Damage (-40)',
        'wrong_ball': 'Wrong Ball Color (-10)',
        'ball_outside': 'Ball Outside (-10)',
        'late_start': 'Late Start (-20)',
        'incorrect_ball_handling': 'Incorrect Ball Handling (-15)'
    };
    
    penalties.forEach(penalty => {
        if (penalty) {
            const tag = document.createElement('span');
            tag.className = 'penalty-tag';
            tag.innerHTML = `
                ${penaltyLabels[penalty]}
                <button onclick="removePenalty('${team}', '${penalty}')">&times;</button>
            `;
            container.appendChild(tag);
        }
    });
}

function removePenalty(team, penalty) {
    const select = elements[team + 'Penalty'];
    const options = Array.from(select.options);
    options.forEach(option => {
        if (option.value === penalty) {
            option.selected = false;
        }
    });
    gameState[team].penalties = gameState[team].penalties.filter(p => p !== penalty);
    updatePenaltyDisplay(team);
    calculateScores();
}

// Update the existing penalty change handlers
elements.team1Penalty.addEventListener('change', (e) => {
    gameState.team1.penalties = Array.from(e.target.selectedOptions).map(option => option.value);
    updatePenaltyDisplay('team1');
    calculateScores();
});

elements.team2Penalty.addEventListener('change', (e) => {
    gameState.team2.penalties = Array.from(e.target.selectedOptions).map(option => option.value);
    updatePenaltyDisplay('team2');
    calculateScores();
});

// Update the click outside handler
document.addEventListener('click', (e) => {
    const target = e.target;
    
    // Close dropdowns if click is not on a penalty-related element
    if (!target.closest('.penalty-select') && 
        !target.closest('.penalty-toggle')) {
        elements.team1Penalty.style.display = 'none';
        elements.team2Penalty.style.display = 'none';
    }
});

// Add click handler for the penalty select to prevent closing
elements.team1Penalty.addEventListener('click', (e) => {
    e.stopPropagation();
});

elements.team2Penalty.addEventListener('click', (e) => {
    e.stopPropagation();
});

// Initialize penalty displays
updatePenaltyDisplay('team1');
updatePenaltyDisplay('team2');

// Update the saveCount function
function saveCount() {
    const gameData = {
        gameNumber: elements.gameNumber.value,
        team1Name: elements.team1Name.value,
        team2Name: elements.team2Name.value,
        timestamp: new Date().toISOString(),
        table: document.getElementById('tableSelect').value,
        ...gameState
    };
    
    const saveButton = document.querySelector('.save');
    saveButton.textContent = 'Saving...';
    saveButton.disabled = true;
    
    socket.emit('saveGame', gameData);
}

// Handle save completion
socket.on('savingComplete', (response) => {
    const saveButton = document.querySelector('.save');
    saveButton.textContent = 'Save Count';
    saveButton.disabled = false;
    
    if (response.status === 'success') {
        hasGameBeenSaved = true;
        sendScoreUpdate(); // Send update with saved status
        alert('Game saved successfully!');
    } else {
        alert('Error saving game: ' + response.message);
    }
});

// Add new function for sending score updates to server
function sendScoreUpdate() {
    const tableSelect = document.getElementById('tableSelect');
    socket.emit('updateScore', {
        table: tableSelect.value,
        scores: {
            team1: gameState.team1.score,
            team2: gameState.team2.score,
            team1Name: elements.team1Name.value,
            team2Name: elements.team2Name.value,
            hasBeenSaved: hasGameBeenSaved
        }
    });
}

// Update resetCount to not send updates
function resetCount() {
    gameState = {
        gameNumber: '',
        team1: { name: '', orange: 0, purple: 0, penalties: [], score: 0 },
        team2: { name: '', orange: 0, purple: 0, penalties: [], score: 0 }
    };
    
    elements.gameNumber.value = '';
    elements.team1Name.value = '';
    elements.team2Name.value = '';
    elements.team1Penalty.selectedIndex = -1;
    elements.team2Penalty.selectedIndex = -1;
    
    updateDisplay(); // Only update local display, don't send to server
}

// Initialize the display
updateDisplay(); 