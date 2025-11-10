import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

const COLORS = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange', 'Pink']
const TRIALS_PER_PHASE = 10

const Calibration: React.FC = () => {
  const [phase, setPhase] = useState<'word' | 'transition' | 'color'>('word')
  const [trialCount, setTrialCount] = useState(0)
  const [startTime, setStartTime] = useState<number | null>(null)
  const [reactionTime, setReactionTime] = useState<number | null>(null)
  const [wordTimes, setWordTimes] = useState<number[]>([])
  const [colorTimes, setColorTimes] = useState<number[]>([])
  const [currentWord, setCurrentWord] = useState<string | null>(null)
  const [currentColor, setCurrentColor] = useState<string | null>(null)
  const [options, setOptions] = useState<string[]>([])
  const [isDone, setIsDone] = useState(false)
  const [inProgress, setInProgress] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [correctCount, setCorrectCount] = useState(0)
  const timeoutRef = useRef<number | null>(null)
  const [focusLevel, setFocusLevel] = useState<number | null>(null)
  
  const navigate = useNavigate()

  const startTrial = () => {
    setFeedback(null)
    setReactionTime(null)

    const word = COLORS[Math.floor(Math.random() * COLORS.length)]
    let color: string
    do {
      color = COLORS[Math.floor(Math.random() * COLORS.length)]
    } while (color === word)

    const shuffled = [...COLORS].sort(() => Math.random() - 0.5)
    const possible = new Set([word, color])
    while (possible.size < 4) possible.add(shuffled.pop()!)
    const finalOptions = Array.from(possible).sort(() => Math.random() - 0.5)

    setCurrentWord(word)
    setCurrentColor(color.toLowerCase())
    setOptions(finalOptions)
    setInProgress(true)
    setStartTime(performance.now())
  }

  const handleOptionClick = (choice: string) => {
    if (!currentWord || !currentColor || !startTime) return

    const endTime = performance.now()
    const time = endTime - startTime
    const correct =
      phase === 'word' ? choice === currentWord : choice.toLowerCase() === currentColor

    if (correct) {
      setFeedback('✅ Correct!')
      setCorrectCount(prev => prev + 1)
      if (phase === 'word') setWordTimes(prev => [...prev, time])
      else setColorTimes(prev => [...prev, time])
    } else {
      const correctAnswer = phase === 'word' ? currentWord : capitalize(currentColor)
      setFeedback(`❌ Wrong! The correct answer was ${correctAnswer}.`)
    }

    setReactionTime(Math.round(time))
    setInProgress(false)

    const nextTrial = trialCount + 1
    setTrialCount(nextTrial)

    timeoutRef.current = window.setTimeout(() => {
      if (nextTrial >= TRIALS_PER_PHASE) {
        if (phase === 'word') {
          setPhase('transition') // show transition screen
          setTrialCount(0)
        } else {
          setIsDone(true)
        }
      } else {
        startTrial()
      }
    }, 200)
  }

  const handleStart = () => {
    setPhase('word')
    setTrialCount(0)
    setWordTimes([])
    setColorTimes([])
    setCorrectCount(0)
    setIsDone(false)
    startTrial()
  }

  const handleStartPhase2 = () => {
    setPhase('color')
    startTrial()
  }

  const handleReturn = () => {
    navigate('/')
  }

  const average = (arr: number[]) =>
    arr.length > 0 ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : null

  const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1)

  return (
    <main className="calibration-container">
  <h1 className="title">Color-Word Focus Test</h1>

  {/* Start Screen */}
  {!inProgress && !isDone && trialCount === 0 && phase === 'word' && (
    <div className="start-screen">
      <p className="instructions">
        Phase 1: You'll see a color word shown in a random color.
        Choose the <strong>meaning of the word</strong> (ignore the color).
        You’ll do this 10 times, then move on to Phase 2.
      </p>

      <button onClick={handleStart} className="btn primary">
        Start Test
      </button>

      <button onClick={handleReturn} className="btn secondary">
        Return
      </button>
    </div>
  )}

  {/* Phase 1 → Phase 2 Transition */}
  {phase === 'transition' && (
    <div className="transition-screen">
      <p className="instructions">
        Great job on Phase 1! 🎉<br/>
        Now we’re moving to <strong>Phase 2</strong>.<br/>
        Choose the <strong>color of the text</strong> instead of the word’s meaning.<br/>
        You’ll complete 10 trials again.
      </p>
      <button onClick={handleStartPhase2} className="btn primary">
        Start Phase 2
      </button>
    </div>
  )}

      
  {/* Active Trial */}
  {inProgress && (
    <div className="trial">
      <div className="stroop-word-container">
        <p className="stroop-word" style={{ color: currentColor ? currentColor.toLowerCase() : 'black' }}>
          {currentWord}
        </p>
      </div>

      <div className="options">
        {options.map(opt => (
          <button
            key={opt}
            onClick={() => handleOptionClick(opt)}
            className="option-btn"
          >
            {opt}
          </button>
        ))}
      </div>

      <p className="trial-counter">
        Trial {trialCount + 1} of {TRIALS_PER_PHASE} —
        {phase === 'word' ? ' Choose the WORD' : ' Choose the COLOR'}
      </p>
    </div>
  )}

  {/* Feedback */}
  {feedback && <p className="feedback">{feedback}</p>}
  {reactionTime && <p className="reaction-time">Reaction: {reactionTime} ms</p>}

  {/* Done */}
  {isDone && (
    <div className="results">
      <p className="complete">✅ Test complete!</p>
      <p>Average Word Time: {average(wordTimes)} ms</p>
      <p>Average Color Time: {average(colorTimes)} ms</p>

      <p className="correct-count">
        Correct answers: {correctCount}/{TRIALS_PER_PHASE * 2}
      </p>

      <p className="focus-label">On a scale of 1–10, how focused were you during this activity?</p>

      <div className="focus-scale">
        {[...Array(10)].map((_, i) => {
          const num = i + 1
          const selected = focusLevel === num
          return (
            <button
              key={num}
              onClick={() => setFocusLevel(num)}
              className={`focus-btn ${selected ? 'selected' : ''}`}
            >
              {num}
            </button>
          )
        })}
      </div>

      {focusLevel && (
        <>1
           <p className="focus-display">Your Focus Level: {focusLevel}</p>
          <button onClick={handleReturn} className="btn primary">
            Return
          </button>
        </>
      )}
    </div>
  )}
</main>

  )
}

export default Calibration
