import React, { useState } from 'react';
import { DataProvider } from './context/DataContext';

// 1. Import the Layout
import Layout from './components/layout/Layout';

// 2. Import your Pages
import UploadPage  from './pages/UploadPage';
import AnalysisPage from './pages/AnalysisPage';
import HistoryPage  from './pages/HistoryPage';

function App() {
  const [activeTab, setActiveTab] = useState('upload');

  return (
    <DataProvider>
      {/* 3. Wrap everything in the Layout */}
      <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
        
        {/* This logic block is the "children" passed to Layout */}
        {activeTab === 'upload'   && <UploadPage onSwitch={() => setActiveTab('analysis')} />}
        {activeTab === 'analysis' && <AnalysisPage />}
        {activeTab === 'history'  && <HistoryPage />}
        
      </Layout>
    </DataProvider>
  );
}

export default App;