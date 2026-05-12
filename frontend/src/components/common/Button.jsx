import React from 'react';
import { Button as MuiButton } from '@mui/material';

export default function Button({ 
  children, 
  onClick, 
  variant = "contained", 
  color = "primary", 
  fullWidth = false, 
  ...props 
}) {
  return (
    <MuiButton
      variant={variant}
      color={color}
      onClick={onClick}
      fullWidth={fullWidth}
      {...props}
      sx={{
        // Match height to InputField for visual alignment
        height: { xs: '30px', md: '32px' },
        minHeight: { xs: '30px', md: '32px' },
        fontSize: { xs: '0.75rem', md: '0.75rem' },
        
        borderRadius: '8px',
        textTransform: 'none',
        lineHeight: 1,
        letterSpacing: 'normal',
        fontWeight: 500,
        padding: '0 12px',
        boxShadow: 'none',
        '&:hover': {
          boxShadow: 'none',
          filter: 'brightness(0.9)',
        },
        ...props.sx
      }}
    >
      {children}
    </MuiButton>
  );
}