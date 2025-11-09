import React from 'react'
import { useNavigate } from 'react-router-dom'
import { observer } from 'mobx-react-lite'
import projectStore from '../ProjectStore'

const Home: React.FC = observer(() => {
  const navigate = useNavigate()

  const handleStart = async () => {
    projectStore.isStudying = true
    try {
      await fetch('http://localhost:5001/start_pip', { method: 'POST' });
      console.log('PiP started');
    } catch (error) {
      console.error('Failed to start PiP:', error);
    }
    console.log('Study session started')
    // TODO: Add EEG or focus tracking start logic here
  }

  const handleEnd = async () => {
    projectStore.isStudying = false
    try {
      await fetch('http://localhost:5001/stop_pip', { method: 'POST' });
      console.log('PiP stopped');
    } catch (error) {
      console.error('Failed to stop PiP:', error);
    }
    console.log('Study session ended')
    // TODO: Stop tracking, save data, etc.
  }

  const handleConfigure = () => {
    console.log('Open configuration settings')
    navigate('/configuration')
  }

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 flex flex-col items-center justify-center p-8">
      <section className="text-center">
        <h1 className="text-4xl font-bold mb-2">AttentionSpan.AI</h1>
        <p className="text-lg text-gray-600 mb-8">
          Adaptive Focus-Aware Study Platform
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={handleStart}
            disabled={projectStore.isStudying} // use store value
            className={`px-6 py-3 rounded-2xl font-semibold shadow 
              ${projectStore.isStudying ? 'bg-gray-300 cursor-not-allowed' : 'bg-green-500 hover:bg-green-600 text-white'}`}
          >
            Start Study Session
          </button>

          <button
            onClick={handleEnd}
            disabled={!projectStore.isStudying} // use store value
            className={`px-6 py-3 rounded-2xl font-semibold shadow 
              ${!projectStore.isStudying ? 'bg-gray-300 cursor-not-allowed' : 'bg-red-500 hover:bg-red-600 text-white'}`}
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

        {projectStore.isStudying && (
          <p className="mt-6 text-green-600 font-medium">
            Session Active — tracking focus data...
          </p>
        )}
      </section>
    </main>
  )
})

export default Home
