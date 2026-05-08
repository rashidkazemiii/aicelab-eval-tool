import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import AnalysisPage from './pages/AnalysisPage';

function App() {
  return (
    <Router>
      <Routes>
        {/* Step 1: The Landing/Upload Page */}
        <Route path="/" element={<UploadPage />} />
        
        {/* Step 2: The Calculation/Analysis Page */}
        <Route path="/analysis" element={<AnalysisPage />} />
      </Routes>
    </Router>
  );
}

export default App;