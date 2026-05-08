import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';

function FrictionAnalysis() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetching from your backend (assuming it returns the OFT07935.txt data)
    axios.get('http://localhost:8000/analyze')
      .then(response => {
        if (response.data.status === 'success') {
          // Mapping your Zeit (Time) and Reibungszahl (Friction) columns
          const chartData = response.data.zeit.map((t, i) => [
            parseFloat(t), 
            parseFloat(response.data.reibungszahl[i])
          ]);
          setData(chartData);
          setLoading(false);
        }
      });
  }, []);

  const option = {
    title: { text: 'Friction Coefficient Analysis', left: 'center' },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const [time, value] = params[0].data;
        return `Time: ${time.toFixed(3)} s<br/>Friction (μ): ${value.toFixed(5)}`;
      }
    },
    // TOOLBOX: This is the key for verifying peaks
    toolbox: {
      feature: {
        dataZoom: { yAxisIndex: 'none' }, // Enables the Box Zoom tool
        restore: {}, // Reset button
        saveAsImage: {}
      }
    },
    xAxis: {
      type: 'value',
      name: 'Time (s)',
      tickLine: { show: true }
    },
    yAxis: {
      type: 'value',
      name: 'Friction (μ)',
      scale: true // Auto-focuses on the data range
    },
    // DATA ZOOM: Slider and Mouse-wheel support
    dataZoom: [
      { type: 'inside', start: 0, end: 100 }, // Mouse wheel zoom
      { type: 'slider', start: 0, end: 100 }  // Bottom slider
    ],
    series: [
      {
        name: 'Friction Coefficient',
        type: 'line',
        symbol: 'none', // Keeps it clean
        sampling: 'lttb', // Optimization for large datasets
        data: data,
        lineStyle: { color: '#5470c6', width: 1 },
        // Highlights the peaks when you hover
        emphasis: { lineStyle: { width: 2 } }
      }
    ]
  };

  if (loading) return <div>Loading 45,000 data points...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 4px 15px rgba(0,0,0,0.1)' }}>
        <ReactECharts 
          option={option} 
          style={{ height: '600px', width: '100%' }} 
          notMerge={true}
          lazyUpdate={true}
        />
        <div style={{ marginTop: '10px', textAlign: 'center', color: '#666', fontSize: '14px' }}>
          <strong>How to verify peaks:</strong> Click the 🔍 icon in the top right, then click and drag a rectangle over any peak to zoom in instantly.
        </div>
      </div>
    </div>
  );
}

export default FrictionAnalysis;