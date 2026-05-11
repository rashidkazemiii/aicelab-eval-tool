import React, { useState } from 'react';
import { Box, Paper, Typography, Stack, Divider } from '@mui/material';
import Button from '../components/common/Button';
import Chart from '../components/charts/Chart';

export default function AnalysisPage() {
  const [cofData, setCofData] = useState([]);
  const [dispData, setDispData] = useState([]);

  // Helper for half-screen sections
  const AnalysisSection = ({ title, buttons, data, xAxisKey, lines }) => (
    <Paper 
      elevation={2} 
      sx={{ 
        p: 2, 
        height: 'calc(50vh - 40px)', // Fits two sections perfectly on one screen
        borderRadius: 3, 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden' // Prevents internal scrolling
      }}
    >
      <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold', color: '#1f2a40' }}>
        {title}
      </Typography>

      <Box sx={{ display: 'flex', flexGrow: 1, gap: 2, minHeight: 0 }}>
        {/* LEFT: Vertical Buttons */}
        <Stack 
          spacing={1} 
          sx={{ 
            width: '140px', 
            justifyContent: 'flex-start'
          }}
        >
          {buttons.map((label) => (
            <Button 
              key={label} 
              variant="contained" 
              fullWidth
              size="small"
              sx={{ 
                bgcolor: label === 'Evaluate' || label === 'Generate' ? '#3e4396' : '#f5f5f5',
                color: label === 'Evaluate' || label === 'Generate' ? '#fff' : '#333',
                fontSize: '0.75rem',
                fontWeight: 'bold',
                textTransform: 'none',
                boxShadow: 'none',
                '&:hover': { bgcolor: label === 'Evaluate' || label === 'Generate' ? '#2c317a' : '#e0e0e0' }
              }}
              onClick={() => console.log(`${title} - ${label} clicked`)}
            >
              {label}
            </Button>
          ))}
        </Stack>

        <Divider orientation="vertical" flexItem />

        {/* RIGHT: Chart Area */}
        <Box sx={{ flexGrow: 1, height: '100%', minWidth: 0 }}>
          <Chart data={data} xAxisKey={xAxisKey} lines={lines} />
        </Box>
      </Box>
    </Paper>
  );

  return (
    <Box 
      sx={{ 
        p: 2, 
        bgcolor: '#f0f2f5', 
        height: '100vh', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: 2,
        overflow: 'hidden' // Disables scrolling on the main page
      }}
    >
      <AnalysisSection 
        title="CoF Analysis"
        buttons={['Trim', 'Offset', 'Filter', 'Evaluate']}
        data={cofData}
        xAxisKey="zeit"
        lines={[
          { key: 'raw', color: '#bdc3c7', label: 'Raw', width: 1 },
          { key: 'filtered', color: '#3e4396', label: 'Filtered', width: 2 }
        ]}
      />

      <AnalysisSection 
        title="Displacement Analysis (µm)"
        buttons={['Offset', 'Filter', 'Evaluate', 'Generate']}
        data={dispData}
        xAxisKey="zeit"
        lines={[
          { key: 'raw', color: '#bdc3c7', label: 'Raw', width: 1 },
          { key: 'filtered', color: '#27ae60', label: 'Filtered', width: 2 }
        ]}
      />
    </Box>
  );
}