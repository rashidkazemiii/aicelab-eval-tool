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
        },
        ...props.sx
      }}
      {...props}
    />
  );
}