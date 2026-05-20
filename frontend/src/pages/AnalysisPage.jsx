import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Alert } from '@mui/material';
import Chart from '../components/charts/Chart';
import Controls from '../components/analysis/Controls';
import { useData } from '../context/DataContext';
import { useAnalysis } from '../hooks/useAnalysis';

export default function AnalysisPage() {
  const { analysisData, fileName } = useData();
  const {
    fetchData, offset, filter, evaluate, viewResult,
    loading, error, chartLines, calculated, offsetApplied, cofMarkers,
    generateDisplacement, displacementOffset, displacementFilter, displacementEvaluate,
    dispData, dispLines, dispOffsetApplied,
  } = useAnalysis();

  const [inputs, setInputs] = useState({
    filterPoints: '25',
    staticRange:  '10',
    dynamicMin:   '20',
    dynamicMax:   '80',
  });

  useEffect(() => { if (fileName) fetchData(); }, []);

  const handleInputChange = (key) => (e) => setInputs({ ...inputs, [key]: e.target.value });

  return (
    <Box sx={{
      display: 'flex', height: 'calc(100vh - 50px)', width: '100%',
      gap: 1.5, p: 1.5, boxSizing: 'border-box', overflow: 'hidden', bgcolor: '#f4f6f8',
    }}>

      <Controls
        inputs={inputs}
        handleInputChange={handleInputChange}
        onOffset={offset}
        onFilter={() => filter(inputs.filterPoints)}
        onEvaluate={() => evaluate(inputs.staticRange, inputs.dynamicMin, inputs.dynamicMax)}
        onDispGenerate={generateDisplacement}
        onDispOffset={displacementOffset}
        onDispFilter={() => displacementFilter(inputs.filterPoints)}
        onDispEvaluate={displacementEvaluate}
        fileName={fileName}
        onViewResult={viewResult}
        loading={loading}
        calculated={calculated}
        offsetApplied={offsetApplied}
        dispOffsetApplied={dispOffsetApplied}
      />

      <Box sx={{ flexGrow: 1, minWidth: 0, height: '100%', display: 'flex', flexDirection: 'column', gap: 1.5, overflowY: 'auto' }}>

        {error && <Alert severity="error" sx={{ flexShrink: 0 }}>{error}</Alert>}

        {/* CoF Chart */}
        <Paper elevation={1} sx={{ flexShrink: 0, height: '55vh', p: 2, borderRadius: 3, display: 'flex', flexDirection: 'column' }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#1f2a40', mb: 1 }}>
            CoF
          </Typography>
          <Box sx={{ flexGrow: 1, minHeight: 0 }}>
            <Chart data={analysisData} xAxisKey="zeit" lines={chartLines} markers={cofMarkers} />
          </Box>
        </Paper>

        {/* Displacement Chart */}
        <Paper elevation={1} sx={{ flexShrink: 0, height: '55vh', p: 2, borderRadius: 3, display: 'flex', flexDirection: 'column' }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#1f2a40', mb: 1 }}>
            Displacement
          </Typography>
          <Box sx={{ flexGrow: 1, minHeight: 0 }}>
            <Chart data={dispData} xAxisKey="zeit" lines={dispLines} />
          </Box>
        </Paper>

      </Box>
    </Box>
  );
}
