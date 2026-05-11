import React from 'react';
import { Box, CssBaseline } from '@mui/material';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function Layout({ children, activeTab, setActiveTab }) {
  return (
    <Box sx={{ display: 'flex', bgcolor: '#f5f7fa', minHeight: '100vh' }}>
      <CssBaseline />
      <Navbar />
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        {/* This is where UploadPage or AnalysisPage will be "injected" */}
        {children}
      </Box>
    </Box>
  );
}