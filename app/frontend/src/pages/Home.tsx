import React from 'react'
import { useNavigate } from 'react-router-dom'
import { observer } from 'mobx-react-lite'
import projectStore from '../ProjectStore'
import './Home.css'

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
  }

  const handleCalibrate = () => {
    console.log('Open calibration settings')
    navigate('/calibrate')
  }

  return (
    <main className="home-container">
      <header className="brand-title">AttentionSpan.AI</header>

      <section className="center-section">
        <h1 className="main-title">Focus Garden</h1>
        <p className="subtitle">
          Grow your garden by focusing!
        </p>

        <div className="button-row">
          <button
            onClick={handleStart}
            disabled={projectStore.isStudying}
            className="garden-button start"
          >
            Start Study Session
          </button>

          <button
            onClick={handleEnd}
            disabled={!projectStore.isStudying}
            className="garden-button end"
          >
            End Study Session
          </button>

          <button
            onClick={handleCalibrate}
            className="garden-button calibrate"
          >
            Calibrate
          </button>
        </div>

        {projectStore.isStudying && (
          <p className="session-active">
            🌿 Session Active — tracking focus data...
          </p>
        )}

        <div className="garden-section">
          {/* Place garden game components here */}
          <p className="garden-placeholder">
            🌱 Your garden will grow here...
          </p>
        </div>
      </section>
    </main>
  )
})

export default Home
