import React, { useState } from 'react';
import { Box, Paper, Typography, Stack, Divider } from '@mui/material';
import Button from '../components/common/Button';
import Chart from '../components/charts/Chart';
import InputField from '../components/common/InputField';

export default function AnalysisPage() {
  const [cofData, setCofData] = useState([]);
  const [inputs, setInputs] = useState({
    filterPoints: '',
    staticRange: '',
    dynamicRange: '',
    zoomRange: ''
  });

  const handleInputChange = (key) => (e) => {
    setInputs({ ...inputs, [key]: e.target.value });
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      height: '100%', 
      gap: 2, 
      p: 1, 
      boxSizing: 'border-box',
      overflow: 'hidden' 
    }}>
      
      {/* LEFT COLUMN: Controls */}
      <Paper 
        elevation={2} 
        sx={{ 
          width: 280, 
          p: 2, 
          display: 'flex', 
          flexDirection: 'column', 
          borderRadius: 3,
          bgcolor: '#ffffff',
          overflowY: 'auto',
          maxHeight: '100%',
          '&::-webkit-scrollbar': { width: '6px' },
          '&::-webkit-scrollbar-thumb': { bgcolor: '#e0e0e0', borderRadius: '10px' }
        }}
      >
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: '#1f2a40' }}>
          Controls
        </Typography>

        <Stack spacing={3}>
          <Box>
            <Typography variant="caption" sx={{ fontWeight: 'bold', color: '#999', letterSpacing: 1 }}>
              ACTIONS
            </Typography>
            <Stack spacing={1} sx={{ mt: 1 }}>
              {['Trim', 'Offset', 'Filter', 'Evaluate'].map((label) => (
                <Button key={label} fullWidth sx={{ bgcolor: '#3e4396' }}>
                  {label}
                </Button>
              ))}
              <Button fullWidth sx={{ bgcolor: '#4cceac', mt: 1 }}>
                Save
              </Button>
            </Stack>
          </Box>

          <Divider />

          <Box>
            <Typography variant="caption" sx={{ fontWeight: 'bold', color: '#999', letterSpacing: 1 }}>
              PARAMETERS
            </Typography>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <InputField label="Filter points" size="small" value={inputs.filterPoints} onChange={handleInputChange('filterPoints')} />
              <InputField label="Static CoF range (%)" size="small" value={inputs.staticRange} onChange={handleInputChange('staticRange')} />
              <InputField label="Dynamic CoF range (%)" size="small" value={inputs.dynamicRange} onChange={handleInputChange('dynamicRange')} />
              <InputField label="Zoom range (s)" size="small" value={inputs.zoomRange} onChange={handleInputChange('zoomRange')} />
            </Stack>
          </Box>
        </Stack>
      </Paper>

      {/* RIGHT COLUMN: Visualization + Results */}
      <Box sx={{ 
        flexGrow: 1, 
        minWidth: 0, 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: 2 
      }}>
        
        {/* TOP: Visualization Box (70% Height) */}
        <Paper 
          elevation={2} 
          sx={{ 
            flex: 0.7, 
            p: 2, 
            borderRadius: 3, 
            display: 'flex', 
            flexDirection: 'column',
            minHeight: 0 
          }}
        >
          <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold', color: '#1f2a40' }}>
            Analysis Visualization
          </Typography>
          <Box sx={{ flexGrow: 1, minHeight: 0 }}>
            <Chart 
              data={cofData} 
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
          elevation={2} 
          sx={{ 
            flex: 0.3, 
            p: 2, 
            borderRadius: 3, 
            display: 'flex', 
            flexDirection: 'column',
            bgcolor: '#ffffff',
            minHeight: 0,
            overflowY: 'auto'
          }}
        >
          <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold', color: '#1f2a40' }}>
            Results Summary
          </Typography>
          <Box sx={{ color: 'text.secondary', fontSize: '0.9rem' }}>
            {/* You can map your calculation results here later */}
            <Typography variant="body2">No calculations performed yet. Click "Evaluate" to see results.</Typography>
          </Box>
        </Paper>

      </Box>
    </Box>
  );
}