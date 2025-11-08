import { useEffect } from 'react'
import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import About from './pages/About'
import Configure from './pages/Configuration'
import moleratImg from './assets/molerat.jpeg'
import BouncingBalls from './components/BouncingBalls'

function App() {

  // --- Detect minimize or tab hide ---
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.hidden) {
        // Window minimized or switched tab — start PiP window
        try {
          await fetch('http://localhost:5001/start_pip', { method: 'POST' })
          console.log('PiP started')
        } catch (error) {
          console.error('Failed to start PiP:', error)
        }
      } else {
        // Window restored — stop PiP window
        try {
          await fetch('http://localhost:5001/stop_pip', { method: 'POST' })
          console.log('PiP stopped')
        } catch (error) {
          console.error('Failed to stop PiP:', error)
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  return (
    <BrowserRouter>
      <BouncingBalls image={moleratImg} count={15} />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/configuration" element={<Configure />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App