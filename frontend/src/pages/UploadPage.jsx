import React, { useState } from 'react';
import { Box, Typography, Stack, Alert, CircularProgress } from '@mui/material';
import UploadBox from '../components/upload/UploadBox';
import FileInfo from '../components/upload/FileInfo';
import Button from '../components/common/Button';
import { useFileUpload } from '../hooks/useFileUpload';
import { useData } from '../context/DataContext';
import { calculate } from '../services/api';

export default function UploadPage({ onSwitch }) {
  const [file, setFile] = useState(null);
  const [isReady, setIsReady] = useState(false); // Track if backend finished
  const { handleUpload, loading, error } = useFileUpload();
  const { setFileName } = useData();

  // 1. Upload happens automatically when file is chosen
  const onFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setFileName(selectedFile.name);
    setIsReady(false); // Reset for new file

    const success = await handleUpload(selectedFile);
    if (success) {
      setIsReady(true); // Backend printed "OK", we are ready to move
    }
  };

  const handleClear = () => {
    setFile(null);
    setIsReady(false);
  };

  // 2. Page switch happens ONLY when clicking the button
  const onImportClick = async () => {
    if (!isReady) return;
    try {
      await calculate();
      onSwitch();
    } catch (err) {
      console.error('Calculate failed:', err);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 5 }}>
      <Typography variant="h6" sx={{ color: '#1f2a40', mb: 4, fontWeight: 'bold' }}>
        Upload your file and press Import to continue
      </Typography>

      <Stack spacing={3} sx={{ width: 450 }}>
        <UploadBox 
          file={file} 
          onFileChange={onFileChange} 
        />

        {file && (
          <FileInfo file={file} onClear={() => { setFile(null); setIsReady(false); }} />
        )}

        <Button
          // Button is disabled if no file, if still uploading, or if upload failed
          disabled={!file || loading || !isReady}
          onClick={onImportClick}
          sx={{ bgcolor: '#3e4396', color: 'white' }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : 'Calculate'}
        </Button>

        {error && <Alert severity="error">{error}</Alert>}
        
        {isReady && !loading && (
          <Alert severity="success">File processed successfully. Ready to Import.</Alert>
        )}
      </Stack>
    </Box>
  );
}