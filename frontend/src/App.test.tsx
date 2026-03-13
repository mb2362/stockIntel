import React from 'react';

function App() {
    return (
        <div style={{ padding: '20px', fontFamily: 'Arial' }}>
            <h1>Test - If you see this, React is working!</h1>
            <p>Current time: {new Date().toLocaleTimeString()}</p>
        </div>
    );
}

export default App;
