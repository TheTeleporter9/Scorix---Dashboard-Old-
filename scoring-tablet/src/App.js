import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './App.css';

const socket = io('http://localhost:3000');

function App() {
    const [score, setScore] = useState({ team1: 0, team2: 0 });

    useEffect(() => {
        socket.on('scoreUpdate', (newScore) => {
            setScore(newScore);
        });

        return () => {
            socket.off('scoreUpdate');
        };
    }, []);

    const updateScore = (team, increment) => {
        const newScore = {
            ...score,
            [team]: Math.max(0, score[team] + increment)
        };
        setScore(newScore);
        socket.emit('updateScore', newScore);
    };

    return (
        <div className="scoring-container">
            <div className="team-section">
                <h2>Team 1</h2>
                <button onClick={() => updateScore('team1', 1)}>+1</button>
                <h3>{score.team1}</h3>
                <button onClick={() => updateScore('team1', -1)}>-1</button>
            </div>
            
            <div className="team-section">
                <h2>Team 2</h2>
                <button onClick={() => updateScore('team2', 1)}>+1</button>
                <h3>{score.team2}</h3>
                <button onClick={() => updateScore('team2', -1)}>-1</button>
            </div>
        </div>
    );
}

export default App; 