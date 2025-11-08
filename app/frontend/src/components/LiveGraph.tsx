import React, { useState, useEffect } from "react";
import { VictoryChart, VictoryLine, VictoryAxis, VictoryTheme } from "victory";

const LiveGraph = () => {
  const [data, setData] = useState([{ x: 0, y: 50 }]);

  useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => {
        const nextY = Math.random() * 100;
        const newData = [...prev, { x: 0, y: nextY }].slice(-10);
        return newData.map((d, i) => ({ x: i, y: d.y }));
      });
    }, 400);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ width: "500px", margin: "2rem auto" }}>
      <VictoryChart
        theme={VictoryTheme.material}
        domain={{ y: [0, 100] }}
      >
        <VictoryAxis label="Time" />
        <VictoryAxis dependentAxis label="Value" />
        <VictoryLine
          data={data}
          animate={false} // instant updates
          style={{
            data: { stroke: "#4f46e5", strokeWidth: 2 },
          }}
        />
      </VictoryChart>
    </div>
  );
};

export default LiveGraph;
