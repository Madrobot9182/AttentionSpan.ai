// App.tsx
import { useEffect } from 'react';
import { observer } from 'mobx-react-lite';
import projectStore from '../src/ProjectStore'
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import About from './pages/About';
import Calibration from './pages/Calibration';

const App: React.FC = observer(() => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/calibrate" element={<Calibration />} />
      </Routes>
    </BrowserRouter>
  );
});

export default App;
