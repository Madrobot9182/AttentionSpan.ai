import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

const COLORS = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange', 'Pink']
const TRIALS_PER_PHASE = 10

const Configure: React.FC = () => {
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
    <main className="min-h-screen flex flex-col items-center justify-center text-center bg-gray-50">
      <h1 className="text-4xl font-bold mb-6">Color-Word Focus Test</h1>

      {/* === Start Screen === */}
      {!inProgress && !isDone && trialCount === 0 && phase === 'word' && (
        <>
          <p className="text-lg mb-6">
            Phase 1: You’ll see a color word (e.g. “Red”) shown in a random color.
            <br />
            Choose the <strong>meaning of the word</strong> (ignore the color).
            <br />
            You’ll do this <strong>10 times</strong>, then move on to Phase 2.
          </p>
          <button
            onClick={handleStart}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-2xl shadow"
          >
            Start Test
          </button>
          <button
            onClick={handleReturn}
            className="mt-3 px-6 py-3 bg-gray-400 hover:bg-gray-500 text-white font-semibold rounded-2xl shadow"
          >
            Return
          </button>
        </>
      )}

      {/* === Phase Transition Screen === */}
      {phase === 'transition' && (
        <div className="flex flex-col items-center">
          <p className="text-lg mb-6 max-w-xl">
            Great job on Phase 1! 🎉
            <br />
            Now we’re moving to <strong>Phase 2</strong>.
            <br />
            This time, choose the <strong>color of the text</strong> instead of the word’s meaning.
            <br />
            Again, you’ll complete <strong>10 trials</strong>.
          </p>
          <button
            onClick={handleStartPhase2}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-2xl shadow"
          >
            Start Phase 2
          </button>
        </div>
      )}

      {/* === Active Trial === */}
      {inProgress && currentWord && currentColor && (
        <div>
          <p
            className="text-6xl font-bold mb-8 select-none"
            style={{ color: currentColor }}
          >
            {currentWord}
          </p>

          <div className="grid grid-cols-2 gap-4">
            {options.map(opt => (
              <button
                key={opt}
                onClick={() => handleOptionClick(opt)}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-2xl shadow text-lg"
              >
                {opt}
              </button>
            ))}
          </div>

          <p className="mt-4 text-gray-500">
            Trial {trialCount + 1} of {TRIALS_PER_PHASE} —{' '}
            {phase === 'word' ? 'Choose the WORD' : 'Choose the COLOR'}
          </p>
        </div>
      )}

      {/* === Feedback === */}
      {feedback && (
        <p className="mt-6 text-xl font-semibold text-gray-700">{feedback}</p>
      )}
      {reactionTime && (
        <p className="mt-2 text-gray-600">Reaction time: {reactionTime} ms</p>
      )}

      {/* === Results Screen === */}
      {isDone && (
        <div className="flex flex-col items-center mt-8">
          <p className="text-xl mb-4">✅ Test complete!</p>
          <p className="mb-2">Average reaction time (Word meaning): {average(wordTimes)} ms</p>
          <p className="mb-2">Average reaction time (Text color): {average(colorTimes)} ms</p>
          <p className="mb-6 font-semibold">
            Correct answers: {correctCount} / {TRIALS_PER_PHASE * 2}
          </p>
          <p className="mb-4">On a scale of 1–10, how focused were you during this activity?</p>

          <div className="flex gap-2 mb-6">
            {[...Array(10)].map((_, i) => {
              const num = i + 1
              const selected = focusLevel === num
              return (
                <button
                  key={num}
                  onClick={() => setFocusLevel(num)}
                  className={`w-10 h-10 rounded-full font-semibold border transition-colors ${
                    selected
                      ? 'bg-blue-500 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-100'
                  }`}
                >
                  {num}
                </button>
              )
            })}
          </div>

          {focusLevel && (
            <p className="text-gray-600 mb-4">Your Focus Level: {focusLevel}</p>
          )}

          <button
            onClick={handleReturn}
            className="px-6 py-3 rounded-2xl font-semibold shadow bg-blue-500 hover:bg-blue-600 text-white"
          >
            Return
          </button>
        </div>
      )}
    </main>
  )
}

export default Configure
