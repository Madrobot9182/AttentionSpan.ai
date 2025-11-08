import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const Home: React.FC = () => {
  const [sessionActive, setSessionActive] = useState(false)
  const navigate = useNavigate()

  const handleStart = () => {
    setSessionActive(true)
    console.log('Study session started')
    // TODO: Add EEG or focus tracking start logic here
  }

  const handleEnd = () => {
    setSessionActive(false)
    console.log('Study session ended')
    // TODO: Stop tracking, save data, etc.
  }

  const handleConfigure = () => {
    console.log('Open configuration settings')
    // TODO: Open config modal or navigate to settings page
    navigate('/configuration')
  }

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 flex flex-col items-center justify-center p-8">
      <section className="text-center">
        <h1 className="text-4xl font-bold mb-2">NeuroLearn</h1>
        <p className="text-lg text-gray-600 mb-8">
          Adaptive Focus-Aware Study Platform
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={handleStart}
            disabled={sessionActive}
            className={`px-6 py-3 rounded-2xl font-semibold shadow 
              ${sessionActive ? 'bg-gray-300 cursor-not-allowed' : 'bg-green-500 hover:bg-green-600 text-white'}`}
          >
            Start Study Session
          </button>

          <button
            onClick={handleEnd}
            disabled={!sessionActive}
            className={`px-6 py-3 rounded-2xl font-semibold shadow 
              ${!sessionActive ? 'bg-gray-300 cursor-not-allowed' : 'bg-red-500 hover:bg-red-600 text-white'}`}
          >
            End Study Session
          </button>

          <button
            onClick={handleConfigure}
            className="px-6 py-3 rounded-2xl font-semibold shadow bg-blue-500 hover:bg-blue-600 text-white"
          >
            Configure
          </button>
        </div>

        {sessionActive && (
          <p className="mt-6 text-green-600 font-medium">
            Session Active — tracking focus data...
          </p>
        )}
      </section>
    </main>
  )
}

export default Home