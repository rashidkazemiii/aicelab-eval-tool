import React, { useState } from 'react';
import { Box, Button, Typography, Paper, Stack, Alert, CircularProgress } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { useNavigate } from 'react-router-dom';

function UploadPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(''); // 'success', 'error', or ''
  const navigate = useNavigate();

  // Mock upload function
  const handleImport = (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setLoading(true);
    setStatus('');

    // Simulate a 1.5 second network delay
    setTimeout(() => {
      setLoading(false);
      setStatus('success');
    }, 1500);
  };

  const handleClear = () => {
    setFile(null);
    setStatus('');
  };

  const handleCalculate = () => {
    // Navigates to the analysis page (Make sure your App.jsx has this route)
    navigate('/analysis');
  };

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        backgroundColor: '#f5f7fa' 
      }}
    >
      <Paper 
        elevation={6} 
        sx={{ 
          p: 5, 
          width: '450px', 
          textAlign: 'center',
          borderRadius: '16px' 
        }}
      >
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, color: '#1a237e' }}>
          Friction Lab
        </Typography>
        <Typography variant="body2" sx={{ mb: 4, color: '#666' }}>
          OFT Data Analysis & Peak Detection
        </Typography>

        <Stack spacing={3}>
          {/* Custom Styled Upload Button */}
          <Button
            variant="contained"
            component="label"
            size="large"
            startIcon={loading ? <CircularProgress size={24} color="inherit" /> : <CloudUploadIcon />}
            disabled={loading}
            sx={{ py: 1.5, fontSize: '1.1rem', textTransform: 'none' }}
          >
            {loading ? 'Processing File...' : 'Select Data File'}
            <input type="file" hidden onChange={handleImport} />
          </Button>

          {file && (
            <Box sx={{ p: 2, bgcolor: '#e8f0fe', borderRadius: '8px', border: '1px dashed #1976d2' }}>
              <Typography variant="subtitle2" color="primary">
                📄 {file.name}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {(file.size / 1024).toFixed(2)} KB
              </Typography>
            </Box>
          )}

          {status === 'success' && (
            <Alert severity="success" variant="filled">
              File analyzed and ready for calculation!
            </Alert>
          )}

          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            <Button 
              variant="text" 
              color="inherit" 
              fullWidth
              startIcon={<DeleteIcon />}
              onClick={handleClear}
              disabled={!file || loading}
            >
              Clear
            </Button>

            <Button 
              variant="contained" 
              color="success" 
              fullWidth
              size="large"
              endIcon={<PlayArrowIcon />}
              onClick={handleCalculate}
              disabled={status !== 'success'}
              sx={{ fontWeight: 'bold' }}
            >
              Calculate
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}

export default UploadPage;