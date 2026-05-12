import React from 'react';
import { Box, Paper, Typography, Stack, Divider } from '@mui/material';
import Button from '../common/Button';
import InputField from '../common/InputField';

export default function Controls({ inputs, handleInputChange }) {
  return (
    <Paper 
        elevation={1} 
        sx={{ 
        width: '180px', // Locked width as requested
        minWidth: '180px', // Prevent flex-shrink
        p: 2, 
        display: 'flex', 
        flexDirection: 'column', 
        borderRadius: 3,
        bgcolor: '#ffffff',
        height: '100%', // Fill the vertical space
        boxSizing: 'border-box',
        overflowY: 'auto'
        }}
    >
      <Typography sx={{ mb: 1.5, fontWeight: 'bold', color: '#1f2a40', fontSize: { xs: '0.8rem', md: '0.9rem' } }}>
        Controls
      </Typography>

      <Stack spacing={{ xs: 1.5, md: 2 }}>
        <Box>
          <Typography sx={{ fontWeight: 'bold', color: '#999', fontSize: '0.6rem', mb: 1 }}>
            ACTIONS
          </Typography>
          <Stack spacing={0.5}>
            {['Trim', 'Offset', 'Filter', 'Evaluate'].map((label) => (
              <Button key={label} fullWidth sx={{ bgcolor: '#3e4396' }}>
                {label}
              </Button>
            ))}
            <Button fullWidth sx={{ bgcolor: '#4cceac', mt: 0.5 }}>
              Save
            </Button>
          </Stack>
        </Box>

        <Divider />

        <Box>
          <Typography sx={{ fontWeight: 'bold', color: '#999', fontSize: '0.6rem', mb: 1 }}>
            PARAMETERS
          </Typography>
          <Stack spacing={1.5}>
            <InputField 
              label="Filter points" 
              value={inputs.filterPoints} 
              onChange={handleInputChange('filterPoints')} 
            />
            <InputField 
              label="Static CoF range (%)" 
              value={inputs.staticRange} 
              onChange={handleInputChange('staticRange')} 
            />
            <InputField 
              label="Dyn CoF Min (%)" 
              value={inputs.dynamicMin} 
              onChange={handleInputChange('dynamicMin')} 
            />
            <InputField 
              label="Dyn CoF Max (%)" 
              value={inputs.dynamicMax} 
              onChange={handleInputChange('dynamicMax')} 
            />
            <InputField 
              label="Zoom range (s)" 
              value={inputs.zoomRange} 
              onChange={handleInputChange('zoomRange')} 
            />
          </Stack>
        </Box>
      </Stack>
    </Paper>
  );
}