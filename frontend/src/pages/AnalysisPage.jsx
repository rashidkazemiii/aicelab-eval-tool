import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import Chart from '../components/charts/Chart';
import Controls from '../components/analysis/Controls';
import { useData } from '../context/DataContext';
import { useAnalysis } from '../hooks/useAnalysis';

export default function AnalysisPage() {
  const { analysisData, fileName } = useData();
  const { fetchData, offset, filter, loading, chartLines, offsetApplied } = useAnalysis();

  const [inputs, setInputs] = useState({
    filterPoints: '25',
    staticRange: '',
    dynamicMin: '',
    dynamicMax: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const handleInputChange = (key) => (e) => {
    setInputs({ ...inputs, [key]: e.target.value });
  };

  return (
    <Box sx={{
      display: 'flex',
      height: 'calc(100vh - 50px)',
      width: '100%',
      gap: 1.5,
      p: 1.5,
      boxSizing: 'border-box',
      overflow: 'hidden',
      bgcolor: '#f4f6f8'
    }}>

      <Controls
        inputs={inputs}
        handleInputChange={handleInputChange}
        onOffset={offset}
        onFilter={() => filter(inputs.filterPoints)}
        loading={loading}
        offsetApplied={offsetApplied}
      />

      <Box sx={{
        flexGrow: 1,
        minWidth: 0,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5
      }}>

        <Paper
          elevation={1}
          sx={{
            flex: 0.7,
            p: 2,
            borderRadius: 3,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#1f2a40' }}>
              Analysis Visualization
            </Typography>
            {fileName && (
              <Typography variant="caption" sx={{ color: '#888', fontStyle: 'italic' }}>
                {fileName}
              </Typography>
            )}
          </Box>
          <Box sx={{ flexGrow: 1, minHeight: 0 }}>
            <Chart
              data={analysisData}
              xAxisKey="zeit"
              lines={chartLines}
            />
          </Box>
        </Paper>

        <Paper
          elevation={1}
          sx={{
            flex: 0.3,
            p: 2,
            borderRadius: 3,
            display: 'flex',
            flexDirection: 'column',
            bgcolor: '#ffffff',
            minHeight: 0,
            overflow: 'hidden'
          }}
        >
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold', color: '#1f2a40' }}>
            Results Summary
          </Typography>
          <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
}
