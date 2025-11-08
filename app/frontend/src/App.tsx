import { useState } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import About from './pages/About';
import Configure from './pages/Configuration';
import moleratImg from './assets/molerat.jpeg';
import BouncingBalls from './components/BouncingBalls';

function App() {  
	return (
	  <BrowserRouter>
		<BouncingBalls image={moleratImg} count={15} /> {/* background balls */}
		<Routes>
		  <Route path="/" element={<Home />} />      
		  <Route path="/about" element={<About />} />
		  <Route path="/configuration" element={<Configure />} />  
		</Routes>
	  </BrowserRouter>
	)
}

export default App