import React, { useState } from 'react';
import { Box, Typography, Stack, Alert } from '@mui/material';

// Import your components
import UploadBox from '../components/upload/UploadBox';
import { useFileUpload } from '../hooks/useFileUpload';
import FileInfo from '../components/upload/FileInfo';
import Button from '../components/common/Button';

export default function UploadPage({ onSwitch }) {
  const [file, setFile] = useState(null);
  
  // We use the handleUpload function from your custom hook
  const { handleUpload, loading, error } = useFileUpload();

  const onFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const onImportClick = async () => {
    if (!file) return;

    // 1. Upload the file to Python
    const isDone = await handleUpload(file); 
    
    // 2. If successful, immediately trigger the switch to the next tab
    if (isDone) {
      onSwitch(); 
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 5 }}>
      <Typography variant="h4" sx={{ color: '#1f2a40', mb: 4, fontWeight: 'bold' }}>
        Friction Evaluation
      </Typography>

      <Stack spacing={3} sx={{ width: 450 }}>
        {/* Upload Area */}
        <UploadBox file={file} onFileChange={onFileChange} />

        {/* File Details (shows up only when a file is selected) */}
        {file && (
          <FileInfo file={file} onClear={() => setFile(null)} />
        )}

        {/* The single "Master" Button */}
        <Button 
          disabled={!file || loading}
          onClick={onImportClick}
          sx={{ bgcolor: '#3e4396' }}
        >
          {loading ? "Processing..." : "Import"}
        </Button>

        {/* Error message if Python connection fails */}
        {error && <Alert severity="error">{error}</Alert>}
      </Stack>
    </Box>
  );
}