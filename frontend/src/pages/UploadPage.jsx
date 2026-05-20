import React, { useState } from 'react';
import { Box, Typography, Stack, Alert, ToggleButtonGroup, ToggleButton } from '@mui/material';

import UploadBox from '../components/upload/UploadBox';
import { useFileUpload } from '../hooks/useFileUpload';
import FileInfo from '../components/upload/FileInfo';
import Button from '../components/common/Button';

const FILE_TYPES = ['OFT', 'SRV', 'SRV_FSA'];

export default function UploadPage({ onSwitch }) {
  const [file, setFile]         = useState(null);
  const [dataType, setDataType] = useState('OFT');

  const { handleUpload, loading, error } = useFileUpload();

  const onFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const onImportClick = async () => {
    if (!file) return;
    const isDone = await handleUpload(file, dataType);
    if (isDone) onSwitch();
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 5 }}>
      <Typography variant="h4" sx={{ color: '#1f2a40', mb: 4, fontWeight: 'bold' }}>
        Friction Evaluation
      </Typography>

      <Stack spacing={3} sx={{ width: 450 }}>
        {/* Upload Area */}
        <UploadBox file={file} onFileChange={onFileChange} />

        {/* File Type Selector */}
        <Box>
          <Typography variant="body2" sx={{ mb: 0.5, color: '#555', fontWeight: 500 }}>
            File Type
          </Typography>
          <ToggleButtonGroup
            value={dataType}
            exclusive
            onChange={(_, val) => { if (val) setDataType(val); }}
            size="small"
            fullWidth
          >
            {FILE_TYPES.map(type => (
              <ToggleButton
                key={type}
                value={type}
                sx={{
                  textTransform: 'none',
                  fontWeight: 600,
                  '&.Mui-selected': { bgcolor: '#3e4396', color: '#fff', '&:hover': { bgcolor: '#3e4396' } },
                }}
              >
                {type}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>

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