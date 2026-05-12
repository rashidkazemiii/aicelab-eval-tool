import React from 'react';
import { TextField } from '@mui/material';

export default function InputField({ label, value, onChange, type = "text", ...props }) {
  return (
    <TextField
      label={label}
      value={value}
      onChange={onChange}
      type={type}
      variant="outlined"
      fullWidth
      sx={{
        '& .MuiOutlinedInput-root': {
          borderRadius: '8px',
          bgcolor: 'white',
          // Minimum height set to 30px even on smallest screens
          height: { xs: '30px', md: '32px' },
          // Font size floor at 0.75rem (~12px)
          fontSize: { xs: '0.75rem', md: '0.75rem' },
        },
        '& .MuiInputLabel-root': {
          fontSize: { xs: '0.7rem', md: '0.75rem' },
          lineHeight: '1',
        },
        '& .MuiInputLabel-shrink': {
          fontSize: { xs: '0.75rem', md: '0.85rem' },
          transform: 'translate(14px, -8px) scale(0.75)',
        },
        ...props.sx
      }}
      {...props}
    />
  );
}