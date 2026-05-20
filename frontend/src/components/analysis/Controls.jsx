import React from 'react';
import { Box, Paper, Typography, Stack, Divider, CircularProgress } from '@mui/material';
import Button from '../common/Button';
import InputField from '../common/InputField';

export default function Controls({
  inputs, handleInputChange,
  fileName,
  onOffset, onFilter, onEvaluate,
  onDispGenerate, onDispOffset, onDispFilter, onDispEvaluate,
  onViewResult,
  loading, calculated, offsetApplied, dispOffsetApplied,
}) {
  const busy = loading;

  return (
    <Paper
      elevation={1}
      sx={{
        width: '180px', minWidth: '180px', p: 2,
        display: 'flex', flexDirection: 'column',
        borderRadius: 3, bgcolor: '#ffffff',
        height: '100%', boxSizing: 'border-box', overflowY: 'auto',
      }}
    >
      <Typography sx={{ mb: 0.5, fontWeight: 'bold', color: '#1f2a40', fontSize: '0.9rem' }}>
        Controls
      </Typography>

      <Stack spacing={1.5}>

        {/* ── File Name ─────────────────────────────────────── */}
        {fileName && (
          <Typography sx={{ fontSize: '0.65rem', color: '#888', fontStyle: 'italic', wordBreak: 'break-all' }}>
            {fileName}
          </Typography>
        )}

        <Divider />

        {/* ── Parameters ────────────────────────────────────── */}
        <Box>
          <Typography sx={{ fontWeight: 'bold', color: '#999', fontSize: '0.6rem', mb: 0.5 }}>
            PARAMETERS
          </Typography>
          <Stack spacing={1}>
            <InputField label="Filter points" value={inputs.filterPoints} onChange={handleInputChange('filterPoints')} />
            <InputField label="Static CoF range (%)" value={inputs.staticRange} onChange={handleInputChange('staticRange')} />
            <InputField label="Dyn CoF Min (%)" value={inputs.dynamicMin} onChange={handleInputChange('dynamicMin')} />
            <InputField label="Dyn CoF Max (%)" value={inputs.dynamicMax} onChange={handleInputChange('dynamicMax')} />
          </Stack>
        </Box>

        <Divider />

        {/* ── CoF Actions ───────────────────────────────────── */}
        <Box>
          <Typography sx={{ fontWeight: 'bold', color: '#999', fontSize: '0.6rem', mb: 0.5 }}>
            CoF ACTIONS
          </Typography>
          <Stack spacing={0.5}>
            <Button fullWidth sx={{ bgcolor: '#3e4396' }} disabled>
              Trim
            </Button>
            <Button fullWidth sx={{ bgcolor: '#3e4396' }} onClick={onOffset} disabled={busy || !calculated}>
              {busy ? <CircularProgress size={16} color="inherit" /> : 'Offset'}
            </Button>
            <Button fullWidth sx={{ bgcolor: '#3e4396' }} onClick={onFilter} disabled={busy || !offsetApplied}>
              {busy ? <CircularProgress size={16} color="inherit" /> : 'Filter'}
            </Button>
            <Button fullWidth sx={{ bgcolor: '#3e4396' }} onClick={onEvaluate} disabled={busy || !offsetApplied}>
              {busy ? <CircularProgress size={16} color="inherit" /> : 'Evaluate'}
            </Button>
          </Stack>
        </Box>

        <Divider />

        {/* ── Displacement ──────────────────────────────────── */}
        <Box>
          <Typography sx={{ fontWeight: 'bold', color: '#999', fontSize: '0.6rem', mb: 0.5 }}>
            DISPLACEMENT
          </Typography>
          <Stack spacing={0.5}>
            <Button fullWidth sx={{ bgcolor: '#5c6bc0' }} onClick={onDispOffset} disabled={busy || !calculated}>
              {busy ? <CircularProgress size={16} color="inherit" /> : 'Offset'}
            </Button>
            <Button fullWidth sx={{ bgcolor: '#5c6bc0' }} onClick={onDispFilter} disabled={busy || !dispOffsetApplied}>
              {busy ? <CircularProgress size={16} color="inherit" /> : 'Filter'}
            </Button>
            <Button fullWidth sx={{ bgcolor: '#5c6bc0' }} onClick={onDispEvaluate} disabled={busy || !calculated}>
              {busy ? <CircularProgress size={16} color="inherit" /> : 'Evaluate'}
            </Button>
            <Button fullWidth sx={{ bgcolor: '#5c6bc0' }} onClick={onDispGenerate} disabled={busy || !calculated}>
              {busy ? <CircularProgress size={16} color="inherit" /> : 'Generate'}
            </Button>
          </Stack>
        </Box>

        <Divider />

        {/* ── View Result ───────────────────────────────────── */}
        <Button fullWidth sx={{ bgcolor: '#4cceac' }} onClick={onViewResult}>
          View Results
        </Button>

        {/* ── Save ──────────────────────────────────────────── */}
        <Button fullWidth sx={{ bgcolor: '#2e7d32' }} disabled>
          Save
        </Button>

      </Stack>
    </Paper>
  );
}
