import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Alert } from '@mui/material';
import Chart from '../components/charts/Chart';
import Controls from '../components/analysis/Controls';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { useData } from '../context/DataContext';
import { useCoF } from '../hooks/useCoF';
import { useDisplacement } from '../hooks/useDisplacement';
import { DEFAULTS } from '../constants/defaults';

export default function AnalysisPage() {
  const { analysisData, fileName } = useData();
  const cof  = useCoF();
  const disp = useDisplacement();

  const [inputs, setInputs] = useState({
    filterPoints: DEFAULTS.filterPoints,
    staticRange:  DEFAULTS.staticRange,
    dynamicMin:   DEFAULTS.dynamicMin,
    dynamicMax:   DEFAULTS.dynamicMax,
  });

  useEffect(() => { if (fileName) cof.fetchData(); }, []);

  const handleInputChange = (key) => (e) => setInputs({ ...inputs, [key]: e.target.value });

  return (
    <Box sx={{
      display: 'flex', height: 'calc(100vh - 50px)', width: '100%',
      gap: 1.5, p: 1.5, boxSizing: 'border-box', overflow: 'hidden', bgcolor: '#f4f6f8',
    }}>

      <Controls
        inputs={inputs}
        handleInputChange={handleInputChange}
        fileName={fileName}
        onOffset={cof.offset}
        onFilter={() => cof.filter(inputs.filterPoints)}
        onEvaluate={() => cof.evaluate(inputs.staticRange, inputs.dynamicMin, inputs.dynamicMax)}
        onDispGenerate={disp.generate}
        onDispOffset={disp.offset}
        onDispFilter={() => disp.filter(inputs.filterPoints)}
        onDispEvaluate={disp.evaluate}
        onViewResult={cof.viewResult}
        onSave={cof.save}
        saveStatus={cof.saveStatus}
        loading={cof.loading || disp.loading}
        calculated={cof.calculated}
        offsetApplied={cof.offsetApplied}
        evaluateApplied={cof.evaluateApplied}
        dispOffsetApplied={disp.offsetApplied}
      />

      <Box sx={{
        flexGrow: 1, minWidth: 0, height: '100%',
        display: 'flex', flexDirection: 'column', gap: 1.5, overflowY: 'auto',
      }}>

        {cof.error && <Alert severity="error" sx={{ flexShrink: 0 }}>{cof.error}</Alert>}

        {/* CoF Chart */}
        <Paper elevation={1} sx={{ flexShrink: 0, height: '55vh', p: 2, borderRadius: 3, display: 'flex', flexDirection: 'column' }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#1f2a40', mb: 1 }}>CoF</Typography>
          <Box sx={{ flexGrow: 1, minHeight: 0 }}>
            <ErrorBoundary>
              <Chart data={analysisData} xAxisKey="time" lines={cof.chartLines} markers={cof.cofMarkers} />
            </ErrorBoundary>
          </Box>
        </Paper>

        {/* Displacement Chart */}
        <Paper elevation={1} sx={{ flexShrink: 0, height: '55vh', p: 2, borderRadius: 3, display: 'flex', flexDirection: 'column' }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#1f2a40', mb: 1 }}>Displacement</Typography>
          <Box sx={{ flexGrow: 1, minHeight: 0 }}>
            <ErrorBoundary>
              <Chart data={disp.dispData} xAxisKey="time" lines={disp.dispLines} />
            </ErrorBoundary>
          </Box>
        </Paper>

      </Box>
    </Box>
  );
}
