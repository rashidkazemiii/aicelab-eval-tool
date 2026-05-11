import React from 'react';
import { Paper, Stack, TextField, Typography } from '@mui/material';

export default function AnalysisSettings() {
  return (
    <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
      <Typography variant="caption" display="block" sx={{ mb: 1, fontWeight: 'bold', color: 'text.secondary' }}>
        PARAMETERS
      </Typography>
      <Stack spacing={2}>
        <TextField label="Filter points" defaultValue="100" size="small" type="number" />
        <TextField label="Static CoF range (%)" defaultValue="15" size="small" type="number" />
        <TextField label="Dynamic CoF range (%)" defaultValue="15" size="small" type="number" />
        <TextField label="Zoom range" defaultValue="80" size="small" type="number" />
      </Stack>
    </Paper>
  );
}