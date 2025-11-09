// App.tsx
import { useEffect } from 'react';
import { observer } from 'mobx-react-lite';
import projectStore from '../src/ProjectStore'
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import About from './pages/About';
import Configure from './pages/Configuration';
import moleratImg from './assets/molerat.jpeg';
import BouncingBalls from './components/BouncingBalls';

const App: React.FC = observer(() => {

  useEffect(() => {
    if (!projectStore.isStudying) return;

    const handleVisibilityChange = async () => {
      if (document.hidden) {
        try {
          await fetch('http://localhost:5001/start_pip', { method: 'POST' });
          console.log('PiP started');
        } catch (error) {
          console.error('Failed to start PiP:', error);
        }
      } else {
        try {
          await fetch('http://localhost:5001/stop_pip', { method: 'POST' });
          console.log('PiP stopped');
        } catch (error) {
          console.error('Failed to stop PiP:', error);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);

  }, [projectStore.isStudying]);

  return (
    <BrowserRouter>
      <BouncingBalls image={moleratImg} count={15} />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/configuration" element={<Configure />} />
      </Routes>
    </BrowserRouter>
  );
});

export default App;
