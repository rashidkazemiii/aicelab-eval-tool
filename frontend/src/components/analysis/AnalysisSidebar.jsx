import React from 'react';
import { Box, Button, Paper, Typography, Stack, TextField, Divider } from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';

export default function AnalysisSidebar() {
  
  // A helper function to create the button groups without needing a separate file
  const renderGroup = (title, buttons, color = "primary") => (
    <Paper variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2 }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1.5, textAlign: 'center', color: '#1f2a40' }}>
        {title}
      </Typography>
      <Stack spacing={1}>
        {buttons.map((btn) => (
          <Button 
            key={btn} 
            variant="contained" 
            color={color} 
            size="small" 
            sx={{ textTransform: 'none', boxShadow: 'none' }}
          >
            {btn}
          </Button>
        ))}
      </Stack>
    </Paper>
  );

  return (
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column' }}>
      
      {/* 1. Main Action Button */}
      <Button 
        variant="contained" 
        color="success" 
        fullWidth
        startIcon={<SaveIcon />}
        sx={{ mb: 3, py: 1.5, fontWeight: 'bold', fontSize: '1rem' }}
      >
        Save
      </Button>

      {/* 2. CoF Group */}
      {renderGroup("CoF", ['Trim', 'Offset', 'Filter', 'Evaluate'])}

      {/* 3. Displacement Group (Grey/Darker style) */}
      {renderGroup("Displacement", ['Offset', 'Filter', 'Evaluate', 'Generate'], "inherit")}

      {/* 4. Statistics Group */}
      {renderGroup("Analysis & Statistics", [
        'Alternative evaluation', 
        'Statistics per 1 second', 
        'Direction-wise statistics', 
        'Integral CoF', 
        'Clear Evaluation'
      ], "inherit")}

      {/* 5. Parameters / Settings Section */}
      <Paper variant="outlined" sx={{ p: 2, bgcolor: '#fdfdfd' }}>
        <Typography variant="caption" display="block" sx={{ mb: 2, fontWeight: 'bold', color: 'text.secondary', textAlign: 'center' }}>
          PARAMETERS
        </Typography>
        <Stack spacing={2}>
          <TextField label="Filter points" defaultValue="100" size="small" type="number" variant="standard" />
          <TextField label="Static CoF range (%)" defaultValue="15" size="small" type="number" variant="standard" />
          <TextField label="Dynamic CoF range (%)" defaultValue="15" size="small" type="number" variant="standard" />
          <TextField label="Zoom range" defaultValue="80" size="small" type="number" variant="standard" />
        </Stack>
      </Paper>
      
    </Box>
  );
}