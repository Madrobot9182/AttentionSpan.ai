import { Line } from "react-chartjs-2";
import { useState, useEffect } from "react";

const LiveGraph = () => {
  const [labels, setLabels] = useState([0]);
  const [values, setValues] = useState([0]);

  useEffect(() => {
    const interval = setInterval(() => {
        const rng = Math.random() * 100;
        setLabels(prev => [...prev.slice(-20), prev.length]);
        setValues(prev => [...prev.slice(-20), rng]);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const data = {
    labels,
    datasets: [{ label: "Live Data", data: values, borderColor: "blue", fill: false }],
  };

  return <Line data={data} />;
}

export default LiveGraph;