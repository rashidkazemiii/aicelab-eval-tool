import React from 'react';
import { Box, CssBaseline } from '@mui/material';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

// Standard Dashboard Constants
const SIDEBAR_WIDTH = 240;
const NAVBAR_HEIGHT = 64;

export default function Layout({ children, activeTab, setActiveTab }) {
  return (
    <Box sx={{ display: 'flex', bgcolor: '#f5f7fa', minHeight: '100vh' }}>
      <CssBaseline />
      
      {/* 1. Fixed Navbar */}
      <Navbar />
      
      {/* 2. Fixed Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* 3. Main Content: Moves to the right of Sidebar and below Navbar */}
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          p: 3, 
          mt: `${NAVBAR_HEIGHT}px`, // Pushed down by Navbar height
          ml: `${SIDEBAR_WIDTH}px`, // Pushed right by Sidebar width
          height: `calc(100vh - ${NAVBAR_HEIGHT}px)`, // Exactly fits remaining height
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden' // Prevents double scrollbars
        }}
      >
        {children}
      </Box>
    </Box>
  );
}