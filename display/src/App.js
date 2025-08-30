import React, { useEffect, useState } from 'react';
import io from 'socket.io-client';
import './App.css';

const socket = io('http://localhost:3000');

function App() {
    const [score, setScore] = useState({ team1: 0, team2: 0 });
    const [winner, setWinner] = useState(null);

    useEffect(() => {
        socket.on('scoreUpdate', (newScore) => {
            setScore(newScore);
            
            // Determine winner
            if (newScore.team1 >= 10) {
                setWinner('Team 1');
            } else if (newScore.team2 >= 10) {
                setWinner('Team 2');
            }
        });

        return () => {
            socket.off('scoreUpdate');
        };
    }, []);

    return (
        <div className="display-container">
            {winner ? (
                <div className="winner-animation">
                    <h1>{winner} Wins!</h1>
                    <div className="celebration"></div>
                </div>
            ) : (
                <div className="score-display">
                    <h2>Team 1: {score.team1}</h2>
                    <h2>Team 2: {score.team2}</h2>
                </div>
            )}
        </div>
    );
}

export default App; 