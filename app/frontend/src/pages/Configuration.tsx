import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

const Configure: React.FC = () => {
  const TOTAL_TRIALS = 5
  const [waiting, setWaiting] = useState(false)
  const [ready, setReady] = useState(false)
  const [startTime, setStartTime] = useState<number | null>(null)
  const [reactionTime, setReactionTime] = useState<number | null>(null)
  const [trialCount, setTrialCount] = useState(0)
  const [allTimes, setAllTimes] = useState<number[]>([])
  const timeoutRef = useRef<number | null>(null)
  const [isDone, setIsDone] = useState(false)
  const [inProgress, setInProgress] = useState(false)
  const navigate = useNavigate()

  const startTest = () => {
    setReactionTime(null)
    setWaiting(true)
    setReady(false)
    setIsDone(false)
    setInProgress(true)

    // Random delay before green screen
    const delay = Math.random() * 3000 + 2000
    timeoutRef.current = window.setTimeout(() => {
      setWaiting(false)
      setReady(true)
      setStartTime(performance.now())
    }, delay)
  }

  const handleClick = () => {
    if (waiting) {
      // Clicked too early
      clearTimeout(timeoutRef.current!)
      setWaiting(false)
      alert('Too soon! Try again.')
    } else if (ready) {
      // Measure reaction time
      const endTime = performance.now()
      const newTime = endTime - (startTime ?? 0)
      setReady(false)
      setReactionTime(newTime)

      // Record result
      setAllTimes(prev => [...prev, newTime])
      const nextTrial = trialCount + 1
      setTrialCount(nextTrial)

      // If all 5 trials are done, show results
      if (nextTrial >= TOTAL_TRIALS) {
        setIsDone(true)
        setInProgress(false)
      }
    }
  }

  const handleReturn = () => {
    console.log('Returning to home screen')
    navigate('/')
  }

  const averageTime =
    allTimes.length > 0
      ? Math.round(allTimes.reduce((a, b) => a + b, 0) / allTimes.length)
      : null

  return (
    <main
      className={`min-h-screen flex flex-col items-center justify-center text-center ${
        waiting ? 'bg-red-100' : ready ? 'bg-green-200' : 'bg-gray-50'
      }`}
      onClick={ready || waiting ? handleClick : undefined}
    >
      <h1 className="text-4xl font-bold mb-6">Configure Focus Baseline</h1>

      {/* Intro screen */}
      {!waiting && !ready && reactionTime === null && trialCount === 0 && (
        <>
          <p className="text-lg mb-6">
            We’ll measure your reaction speed 5 times to calibrate your focus
            level.
          </p>
          <button
            onClick={startTest}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-2xl shadow"
          >
            Start Test
          </button>
        </>
      )}

      {waiting && <p className="text-xl text-gray-700">Wait for green...</p>}
      {ready && <p className="text-2xl text-gray-800 font-semibold">Click now!</p>}

      {/* During test trials */}
      {reactionTime && !isDone && (
        <div>
          <p className="text-xl mt-4">
            Trial {trialCount} of {TOTAL_TRIALS}: {Math.round(reactionTime)} ms
          </p>
          <button
            onClick={startTest}
            className="mt-6 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-2xl shadow"
          >
            Next Trial
          </button>
        </div>
      )}

      {/* After finishing all trials */}
      {isDone && (
        <div style={{ marginTop: '10px' }} className="flex flex-col items-center">
          <p className="text-xl mb-4">
            ✅ All tests complete! Average reaction time: {averageTime} ms
          </p>
          <button
            onClick={handleReturn}
            className="px-6 py-3 rounded-2xl font-semibold shadow bg-blue-500 hover:bg-blue-600 text-white"
          >
            Return
          </button>
        </div>
      )}

      {/* Return button only before or after test */}
      {!inProgress && !isDone && trialCount === 0 && (
        <div style={{ marginTop: '10px' }}>
          <button
            onClick={handleReturn}
            className="px-6 py-3 rounded-2xl font-semibold shadow bg-gray-400 hover:bg-gray-500 text-white"
          >
            Return
          </button>
        </div>
      )}
    </main>
  )
}

export default Configure