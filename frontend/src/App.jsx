import React, { useState } from 'react';
import { Box, CssBaseline } from '@mui/material';
import { DataProvider } from './context/DataContext';

// 1. IMPORT YOUR COMPONENTS
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';

// 2. IMPORT YOUR PAGES
import UploadPage from './pages/UploadPage';
import AnalysisPage from './pages/AnalysisPage';

function App() {
  const [activeTab, setActiveTab] = useState('upload');

  return (
    <DataProvider>
      <Box sx={{ display: 'flex', bgcolor: '#141b2d', minHeight: '100vh' }}>
        <CssBaseline />
        <Navbar />
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        
        <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8, color: 'white' }}>
          {/* 3. CONDITIONAL RENDERING LOGIC */}
          {activeTab === 'upload' ? (
            <UploadPage onSwitch={() => setActiveTab('analysis')} />
          ) : (
            <AnalysisPage />
          )}
        </Box>
      </Box>
    </DataProvider>
  );
}

export default App;