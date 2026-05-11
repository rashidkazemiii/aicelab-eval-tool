import React from 'react';
import { Paper, Typography, Box, IconButton } from '@mui/material';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import DeleteOutlineIcon from '@mui/icons-material/Delete';

export default function FileInfo({ file, onClear }) {
  if (!file) return null;

  // Convert size to a readable format (KB or MB)
  const fileSize = file.size > 1024 * 1024 
    ? (file.size / (1024 * 1024)).toFixed(2) + ' MB'
    : (file.size / 1024).toFixed(2) + ' KB';

  return (
    <Paper 
      variant="outlined" 
      sx={{ 
        p: 2, 
        bgcolor: '#f8f9ff', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        border: '1px solid #e0e4ff'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <InsertDriveFileIcon sx={{ color: '#3e4396' }} />
        <Box>
          <Typography variant="body2" fontWeight="bold" sx={{ color: '#1f2a40' }}>
            {file.name}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            {fileSize} • {file.type || 'System File'}
          </Typography>
        </Box>
      </Box>

      {/* Optional: A small trash icon to clear the file */}
      <IconButton size="small" onClick={onClear} color="error">
        <DeleteOutlineIcon fontSize="small" />
      </IconButton>
    </Paper>
  );
}