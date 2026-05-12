import React from 'react';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';

export default function Navbar() {
  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        height: 50, // Explicit fixed height
        zIndex: 1201, // Highest layer
        bgcolor: '#1f2a40', 
        boxShadow: 'none', 
        borderBottom: '1px solid #2d3748' 
      }}
    >
      <Toolbar>
        <Typography variant="h6" sx={{ color: '#4cceac', fontWeight: 'bold' }}>
          FRICTION LAB <span style={{ color: '#fff', fontSize: '0.8rem', marginLeft: '10px' }}>v1.0</span>
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Typography variant="body2" sx={{ color: '#aaa' }}>User: MD Luffy</Typography>
      </Toolbar>
    </AppBar>
  );
}