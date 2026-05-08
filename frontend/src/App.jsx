import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';

function FrictionAnalysis() {
  const [rawData, setRawData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:8000/analyze')
      .then(response => {
        if (response.data.status === 'success') {
          const { zeit, cof_raw, cof_filtered } = response.data;
          
          // Map both datasets
          const raw = zeit.map((t, i) => [parseFloat(t), parseFloat(cof_raw[i])]);
          const filtered = zeit.map((t, i) => [parseFloat(t), parseFloat(cof_filtered[i])]);
          
          setRawData(raw);
          setFilteredData(filtered);
          setLoading(false);
        }
      })
      .catch(err => console.error("API Error:", err));
  }, []);

  const option = {
    title: { text: 'Friction Coefficient: Raw vs Filtered', left: 'center' },
    legend: { data: ['Raw Data', 'Filtered Data'], top: '30px' },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let res = `Time: ${params[0].data[0].toFixed(3)} s`;
        params.forEach(p => {
          res += `<br/>${p.marker} ${p.seriesName}: ${p.data[1].toFixed(5)}`;
        });
        return res;
      }
    },
    toolbox: {
      feature: {
        dataZoom: { yAxisIndex: 'none' },
        restore: {},
        saveAsImage: {}
      }
    },
    xAxis: { type: 'value', name: 'Time (s)' },
    yAxis: { type: 'value', name: 'CoF (μ)', scale: true },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100 }
    ],
    series: [
      {
        name: 'Raw Data',
        type: 'line',
        symbol: 'none',
        sampling: 'lttb',
        data: rawData,
        lineStyle: { color: '#ccc', width: 1, opacity: 0.6 }, // Lighter color for raw
      },
      {
        name: 'Filtered Data',
        type: 'line',
        symbol: 'none',
        sampling: 'lttb',
        data: filteredData,
        lineStyle: { color: '#5470c6', width: 2 }, // Bolder color for filtered
        emphasis: { lineStyle: { width: 3 } }
      }
    ]
  };

  if (loading) return <div>Processing 45,000+ data points...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 4px 15px rgba(0,0,0,0.1)' }}>
        <ReactECharts option={option} style={{ height: '600px', width: '100%' }} />
      </div>
    </div>
  );
}

export default FrictionAnalysis;