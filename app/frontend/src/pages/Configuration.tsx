import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom';

const Configure: React.FC = () => {
  const [waiting, setWaiting] = useState(false);
  const [ready, setReady] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [reactionTime, setReactionTime] = useState<number | null>(null);
  const timeoutRef = useRef<number | null>(null);
  const [isDone, setIsDone] = useState(false);
  const navigate = useNavigate()
 
  const startTest = () => {
    setReactionTime(null);
    setWaiting(true);
    setReady(false);

    // Random delay before green screen
    const delay = Math.random() * 3000 + 2000;
    timeoutRef.current = window.setTimeout(() => {
      setWaiting(false);
      setReady(true);
      setStartTime(performance.now());
    }, delay);
  };

  const handleClick = () => {
    if (waiting) {
      // Clicked too early
      clearTimeout(timeoutRef.current!);
      setWaiting(false);
      alert('Too soon! Try again.');
    } else if (ready) {
      // Measure reaction time
      const endTime = performance.now();
      setReady(false);
      setReactionTime(endTime - (startTime ?? 0));
      setIsDone(true);
    };
  }

  const handleReturn = () => {
    console.log('Open home screen')
    // TODO: Open config modal or navigate to settings page
    navigate('/')
  }

  return (
    <main
      className={`min-h-screen flex flex-col items-center justify-center text-center ${
        waiting ? 'bg-red-100' : ready ? 'bg-green-200' : 'bg-gray-50'
      }`}
      onClick={ready || waiting ? handleClick : undefined}
    >
      <h1 className="text-4xl font-bold mb-6">Configure Focus Baseline</h1>

      {!waiting && !ready && !reactionTime && (
        <>
          <p className="text-lg mb-6">
            We’ll measure your reaction speed to help calibrate your focus level.
          </p>
          <button
            onClick={startTest}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-2xl shadow"
          >
            Start Test
          </button>
        </>
      )}

      {waiting && (
        <p className="text-xl text-gray-700">Wait for green...</p>
      )}

      {ready && (
        <p className="text-2xl text-gray-800 font-semibold">Click now!</p>
      )}

      {reactionTime && (
        <div>
          <p className="text-xl mt-4">Your reaction time: {Math.round(reactionTime)} ms</p>
          <button
            onClick={startTest}
            className="mt-6 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-2xl shadow"
          >
            Try Again
          </button>
        </div>
      )}

      {isDone && 
        <button
        onClick={handleReturn}
        className="px-6 py-3 rounded-2xl font-semibold shadow bg-blue-500 hover:bg-blue-600 text-white"
        >
          return
        </button>
      }
    </main>
  )
}

export default Configure