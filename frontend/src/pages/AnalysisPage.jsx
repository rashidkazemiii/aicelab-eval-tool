import React, { useState } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import Chart from '../components/charts/Chart';
import Controls from '../components/analysis/Controls';
import { useData } from '../context/DataContext';

export default function AnalysisPage() {
  const { analysisData } = useData();
  const [inputs, setInputs] = useState({
    filterPoints: '',
    staticRange: '',
    dynamicMin: '',
    dynamicMax: '',
    zoomRange: ''
  });

  const handleInputChange = (key) => (e) => {
    setInputs({ ...inputs, [key]: e.target.value });
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      // Subtract navbar height (50px) to fill the screen perfectly
      height: 'calc(100vh - 50px)', 
      width: '100%',
      gap: 1.5, // Space between sidebar and chart
      p: 1.5,   // Space between edges and components
      boxSizing: 'border-box',
      overflow: 'hidden',
      bgcolor: '#f4f6f8' // Light grey background makes the white panels stand out
    }}>
      
      {/* LEFT COLUMN: Controls */}
      {/* Remove the extra <Box> wrapper that was here. Controls now sits directly in the flex container. */}
      <Controls 
        inputs={inputs} 
        handleInputChange={handleInputChange} 
      />

      {/* RIGHT COLUMN: Visualization + Results */}
      <Box sx={{ 
        flexGrow: 1, // THIS fills the "free space" on the right
        minWidth: 0, 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: 1.5 
      }}>
        
        {/* TOP: Visualization Box (70% Height) */}
        <Paper 
          elevation={1} 
          sx={{ 
            flex: 0.7, 
            p: 2, 
            borderRadius: 3, 
            display: 'flex', 
            flexDirection: 'column',
            minHeight: 0 // Allows the chart to shrink/grow correctly
          }}
        >
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold', color: '#1f2a40' }}>
            Analysis Visualization
          </Typography>
          <Box sx={{ flexGrow: 1, minHeight: 0 }}>
            <Chart 
              data={analysisData}
              xAxisKey="zeit" 
              lines={[
                { key: 'raw', color: '#bdc3c7', label: 'Raw' },
                { key: 'filtered', color: '#3e4396', label: 'Filtered' }
              ]} 
            />
          </Box>
        </Paper>

        {/* BOTTOM: Result Box (30% Height) */}
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