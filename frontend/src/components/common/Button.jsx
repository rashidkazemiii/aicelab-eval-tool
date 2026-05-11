import React from 'react';
import { Button as MuiButton } from '@mui/material';

export default function Button({ children, onClick, variant = "contained", color = "primary", ...props }) {
  return (
    <MuiButton
      variant={variant}
      onClick={onClick}
      sx={{
        borderRadius: '8px',
        textTransform: 'none', // Prevents all-caps text
        fontWeight: 'bold',
        px: 4,
        py: 1,
        ...props.sx // Allows you to add extra styles if needed
      }}
      {...props}
    >
      {children}
    </MuiButton>
  );
}