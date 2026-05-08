import React, { useState, useEffect } from 'react';
import { 
  Box, Paper, Typography, Button, Stack, 
  Divider, CircularProgress, TextField, InputAdornment 
} from '@mui/material';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';

function AnalysisPage() {
  const [data, setData] = useState({ zeit: [], raw: [], filtered: [] });
  const [loading, setLoading] = useState(true);
  const [showFiltered, setShowFiltered] = useState(false);

  // Sidebar States (Matching your image)
  const [filterPoints, setFilterPoints] = useState(100);
  const [staticRange, setStaticRange] = useState(15);
  const [dynamicRangeMin, setDynamicRangeMin] = useState(20);
  const [dynamicRangeMax, setDynamicRangeMax] = useState(80);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const response = await axios.get('http://localhost:8000/analyze');
      if (response.data.status === 'success') {
        setData({
          zeit: response.data.zeit,
          raw: response.data.cof_raw,
          filtered: response.data.cof_filtered
        });
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getChartOption = () => {
    const rawSeries = data.zeit.map((t, i) => [parseFloat(t), parseFloat(data.raw[i])]);
    const filteredSeries = data.zeit.map((t, i) => [parseFloat(t), parseFloat(data.filtered[i])]);

    return {
      title: { text: 'Friction Coefficient Analysis', left: 'center' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['Raw CoF', 'Filtered CoF'], top: '30px' },
      grid: { bottom: '15%', right: '5%', left: '5%' },
      xAxis: { type: 'value', name: 'Time (s)' },
      yAxis: { type: 'value', name: 'CoF', scale: true },
      dataZoom: [{ type: 'inside' }, { type: 'slider' }],
      series: [
        {
          name: 'Raw CoF',
          type: 'line',
          symbol: 'none',
          sampling: 'lttb',
          data: rawSeries,
          lineStyle: { color: '#ccc', width: 1, opacity: 0.5 }
        },
        {
          name: 'Filtered CoF',
          type: 'line',
          symbol: 'none',
          sampling: 'lttb',
          data: showFiltered ? filteredSeries : [],
          lineStyle: { color: '#1976d2', width: 2 }
        }
      ]
    };
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#f5f5f5' }}>
      
      {/* SIDEBAR - Styled like your Excel image */}
      <Paper 
        elevation={4} 
        sx={{ 
          width: 300, 
          overflowY: 'auto', 
          p: 2, 
          borderRadius: 0, 
          bgcolor: '#fafafa',
          borderRight: '1px solid #ddd' 
        }}
      >
        <Stack spacing={2}>
          <Button variant="contained" color="success" fullWidth>Save</Button>
          
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', textAlign: 'center', bgcolor: '#eee' }}>CoF</Typography>
          <Button variant="contained" size="small">Trim</Button>
          <Button variant="contained" size="small">Offset</Button>
          <Button variant="contained" size="small" onClick={() => setShowFiltered(true)}>Filter</Button>
          <Button variant="contained" size="small" color="secondary">Evaluate</Button>

          <Divider />

          {/* Settings Fields */}
          <TextField 
            label="Filter Points" 
            type="number" 
            variant="filled"
            size="small"
            value={filterPoints}
            onChange={(e) => setFilterPoints(e.target.value)}
          />

          <TextField 
            label="Static CoF range" 
            type="number" 
            variant="filled"
            size="small"
            value={staticRange}
            InputProps={{ endAdornment: <InputAdornment position="end">%</InputAdornment> }}
            onChange={(e) => setStaticRange(e.target.value)}
          />

          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField 
              label="Dyn Min" 
              type="number" 
              variant="filled"
              size="small"
              value={dynamicRangeMin}
              onChange={(e) => setDynamicRangeMin(e.target.value)}
            />
            <TextField 
              label="Dyn Max" 
              type="number" 
              variant="filled" 
              size="small"
              value={dynamicRangeMax}
              onChange={(e) => setDynamicRangeMax(e.target.value)}
            />
          </Box>

          <Divider />

          {/* Secondary Buttons */}
          <Button variant="outlined" size="small" sx={{ color: '#555', borderColor: '#ccc' }}>Alternative Evaluation</Button>
          <Button variant="outlined" size="small" sx={{ color: '#555', borderColor: '#ccc' }}>Statistics per 1s</Button>
          <Button variant="outlined" size="small" sx={{ color: '#555', borderColor: '#ccc' }}>Direction-wise Statistics</Button>
          <Button variant="outlined" size="small" sx={{ color: '#555', borderColor: '#ccc' }}>Clear Evaluation</Button>
        </Stack>
      </Paper>

      {/* CHART AREA */}
      <Box sx={{ flexGrow: 1, p: 3 }}>
        <Paper sx={{ height: '100%', p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {loading ? (
            <CircularProgress />
          ) : (
            <ReactECharts 
              option={getChartOption()} 
              style={{ height: '100%', width: '100%' }} 
              notMerge={true}
            />
          )}
        </Paper>
      </Box>
    </Box>
  );
}

export default AnalysisPage;