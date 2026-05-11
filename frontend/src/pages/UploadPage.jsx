import React, { useState } from 'react';
import { Box, Typography, Stack, Alert } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

// 1. Import our organized parts
import UploadBox from '../components/upload/UploadBox';
import { useFileUpload } from '../hooks/useFileUpload';
import FileInfo from '../components/upload/FileInfo';
// 2. Import our NEW Common Components
import Button from '../components/common/Button';
import CheckboxGroup from '../components/common/CheckboxGroup';

export default function UploadPage({ onSwitch }) {
  const [file, setFile] = useState(null);
  const [success, setSuccess] = useState(false);

  const { handleUpload, loading, error } = useFileUpload();

  const onFileChange = (e) => {
    setFile(e.target.files[0]);
    setSuccess(false);
  };

  const onImportClick = async () => {
    const isDone = await handleUpload(file);
    if (isDone) setSuccess(true);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 5 }}>
      <Typography variant="h4" sx={{ color: '#1f2a40', mb: 4, fontWeight: 'bold' }}>
        Friction Evaluation
      </Typography>

      <Stack spacing={3} sx={{ width: 450 }}>
        <UploadBox file={file} onFileChange={onFileChange} />


        {file && !success && (
          <FileInfo file={file} onClear={() => setFile(null)} />

          
        )}


        {/* Using our CUSTOM Button component now! */}
        <Button 
          disabled={!file || loading || success}
          onClick={onImportClick}
          sx={{ bgcolor: '#3e4396' }}
        >
          {loading ? "Processing..." : "Import to System"}
        </Button>

        {error && <Alert severity="error">{error}</Alert>}

        {success && (
          <Button 
            onClick={onSwitch}
            startIcon={<PlayArrowIcon />}
            sx={{ bgcolor: '#3e4396' }} // <--- Changed from Green to your Reference Blue
          >
            Analyze & View Results
          </Button>

          
        )}
      </Stack>
    </Box>
  );
}