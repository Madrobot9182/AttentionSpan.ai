import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import LiveGraph from './components/LiveGraph'
import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import About from './pages/About'
import Configure from './pages/Configuration'

function App() {  
  const [count, setCount] = useState(0)

  return (
      <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />       {/* homepage */}
        <Route path="/about" element={<About />} />
        <Route path="/configuration" element={<Configure />} />   {/* ✅ this line */}
      </Routes>
    </BrowserRouter>

  )
}

export default App