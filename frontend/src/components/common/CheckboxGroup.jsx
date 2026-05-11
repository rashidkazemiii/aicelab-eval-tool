import React from 'react';
import { Box, Typography, FormControlLabel, Checkbox } from '@mui/material';

export default function CheckboxGroup({ label, options, values, onChange }) {
  return (
    <Box sx={{ bgcolor: '#f8f9ff', p: 2, borderRadius: 2, border: '1px solid #e0e4ff' }}>
      {label && (
        <Typography variant="subtitle2" sx={{ mb: 1, color: '#1f2a40', fontWeight: 'bold' }}>
          {label}
        </Typography>
      )}
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0.5 }}>
        {options.map((opt) => (
          <FormControlLabel
            key={opt.id}
            control={
              <Checkbox 
                checked={!!values[opt.id]} 
                onChange={() => onChange(opt.id)}
                size="small"
                sx={{ 
                  color: '#3e4396', 
                  '&.Mui-checked': { color: '#3e4396' } 
                }}
              />
            }
            label={<Typography variant="caption">{opt.label}</Typography>}
          />
        ))}
      </Box>
    </Box>
  );
}