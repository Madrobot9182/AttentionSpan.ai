import { useState, useEffect } from 'react';
import './BouncingBalls.css';

interface Ball {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface BouncingBallsProps {
  image: string;
  count?: number;
}

const BouncingBalls: React.FC<BouncingBallsProps> = ({ image, count = 100 }) => {
  const [balls, setBalls] = useState<Ball[]>([]);

  const handleClick = () => {
    const newBalls: Ball[] = [];
    for (let i = 0; i < count; i++) {
      newBalls.push({
        id: i,
        x: Math.random() * (window.innerWidth - 50),
        y: Math.random() * (window.innerHeight - 50),
        vx: (Math.random() - 0.5) * 10,
        vy: (Math.random() - 0.5) * 10,
      });
    }
    setBalls(newBalls);
  };

  useEffect(() => {
    const interval = setInterval(() => {
      setBalls(prev =>
        prev.map(ball => {
          let { x, y, vx, vy } = ball;

          x += vx;
          y += vy;

          if (x < 0 || x > window.innerWidth - 50) vx = -vx;
          if (y < 0 || y > window.innerHeight - 50) vy = -vy;

          return { ...ball, x, y, vx, vy };
        })
      );
    }, 16);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bouncing-container">
      <img
        src={image}
        alt="MoleRat"
        className="clickable-image"
        onClick={handleClick}
      />
      {balls.map(ball => (
        <img
          key={ball.id}
          src={image}
          alt="ball"
          className="bouncing-ball"
          style={{ left: ball.x, top: ball.y }}
        />
      ))}
    </div>
  );
};

export default BouncingBalls;
