import React, { useState } from 'react';
import { Box, Typography, Button, Paper, Stack } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { useFileUpload } from '../hooks/useFileUpload';

export default function UploadPage({ onSwitch }) {
  const [file, setFile] = useState(null);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 5 }}>
      <Typography variant="h4" sx={{ color: '#4cceac', mb: 4 }}>
        Step 1: Import Your Data
      </Typography>

      <Paper sx={{ p: 5, bgcolor: '#1f2a40', width: '400px', textAlign: 'center' }}>
        <Stack spacing={3}>
          <Button
            variant="outlined"
            component="label"
            startIcon={<CloudUploadIcon />}
            sx={{ color: 'white', borderColor: '#4cceac' }}
          >
            {file ? file.name : "Select File"}
            <input type="file" hidden onChange={(e) => setFile(e.target.files[0])} />
          </Button>

          <Button 
            variant="contained" 
            disabled={!file}
            onClick={() => alert('File picked! Now we can connect to API.')}
          >
            Process Data
          </Button>
          
          <Button onClick={onSwitch} sx={{ color: '#aaa' }}>
            Skip to Analysis (Debug)
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}