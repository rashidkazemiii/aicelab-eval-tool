import React, { useRef, useEffect } from 'react'; // Added useRef and useEffect
import { Box, Typography, Paper } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

export default function UploadBox({ file, onFileChange }) {
  const inputRef = useRef(null); // Create a reference to the hidden input

  // 1. This "Watcher" clears the actual input when you press the Clear button
  useEffect(() => {
    if (!file && inputRef.current) {
      inputRef.current.value = ""; // This is the "Magic" line that allows re-uploading
    }
  }, [file]);

  const handleDrop = (e) => {
    e.preventDefault(); // Stop browser from opening the file
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      // We manually call the same function used by the input click
      onFileChange({ target: { files: e.dataTransfer.files } });
    }
  };
  return (
    <Paper
      variant="outlined"
      onDragOver={(e) => e.preventDefault()} // Critical: allows dropping
      onDrop={handleDrop}                   // Grabs the file
      sx={{
        p: 5,
        border: '2px dashed #3e4396',
        bgcolor: '#ffffff',
        cursor: 'pointer',
        textAlign: 'center',
        '&:hover': { bgcolor: '#f8f9ff' }
      }}
      component="label" 
    >
      {/* 2. Attach the ref here */}
      <input 
        type="file" 
        hidden 
        ref={inputRef} 
        onChange={onFileChange} 
      />
      
      <CloudUploadIcon sx={{ fontSize: 60, color: '#3e4396', mb: 2 }} />
      
      <Typography variant="h6" color="#333">
        {file ? file.name : "Click or Drag & Drop File"}
      </Typography>

      <Typography variant="body2" color="#666">
        Supported formats: .txt, .csv (OFT Lab Export)
      </Typography>

    </Paper>
  );
}