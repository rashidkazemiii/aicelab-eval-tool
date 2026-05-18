import React from 'react';
import { Box, Paper, Typography, Stack, Divider, CircularProgress } from '@mui/material';
import Button from '../common/Button';
import InputField from '../common/InputField';

export default function Controls({ inputs, handleInputChange, onOffset, onFilter, onEvaluate, onExport, onExportDynamic, loading, offsetApplied, evaluateApplied }) {
  return (
    <Paper
        elevation={1}
        sx={{
        width: '180px',
        minWidth: '180px',
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 3,
        bgcolor: '#ffffff',
        height: '100%',
        boxSizing: 'border-box',
        overflowY: 'auto'
        }}
    >
      <Typography sx={{ mb: 1.5, fontWeight: 'bold', color: '#1f2a40', fontSize: { xs: '0.8rem', md: '0.9rem' } }}>
        Controls
      </Typography>

      <Stack spacing={{ xs: 1.5, md: 2 }}>
        <Box>
          <Typography sx={{ fontWeight: 'bold', color: '#999', fontSize: '0.6rem', mb: 1 }}>
            ACTIONS
          </Typography>
          <Stack spacing={0.5}>
            <Button fullWidth sx={{ bgcolor: '#3e4396' }} disabled={loading || !offsetApplied}>
              Trim
            </Button>
            <Button fullWidth sx={{ bgcolor: '#3e4396' }} onClick={onOffset} disabled={loading}>
              {loading ? <CircularProgress size={16} color="inherit" /> : 'Offset'}
            </Button>
            <Button fullWidth sx={{ bgcolor: '#3e4396' }} onClick={onFilter} disabled={loading || !offsetApplied}>
              {loading ? <CircularProgress size={16} color="inherit" /> : 'Filter'}
            </Button>
            <Button fullWidth sx={{ bgcolor: '#3e4396' }} onClick={onEvaluate} disabled={loading || !offsetApplied}>
              Evaluate
            </Button>
            <Button fullWidth sx={{ bgcolor: '#4cceac', mt: 0.5 }} disabled={loading || !offsetApplied}>
              Save
            </Button>
          </Stack>
        </Box>

        <Divider />

        <Box>
          <Typography sx={{ fontWeight: 'bold', color: '#999', fontSize: '0.6rem', mb: 1 }}>
            PARAMETERS
          </Typography>
          <Stack spacing={1.5}>
            <InputField
              label="Filter points"
              value={inputs.filterPoints}
              onChange={handleInputChange('filterPoints')}
            />
            <InputField
              label="Static CoF range (%)"
              value={inputs.staticRange}
              onChange={handleInputChange('staticRange')}
            />
            <InputField
              label="Dyn CoF Min (%)"
              value={inputs.dynamicMin}
              onChange={handleInputChange('dynamicMin')}
            />
            <InputField
              label="Dyn CoF Max (%)"
              value={inputs.dynamicMax}
              onChange={handleInputChange('dynamicMax')}
            />
          </Stack>
        </Box>

        <Divider />

        <Button fullWidth sx={{ bgcolor: '#e67e22' }} onClick={onExport} disabled={loading || !offsetApplied}>
          Export
        </Button>
        <Button fullWidth sx={{ bgcolor: '#e67e22' }} onClick={onExportDynamic} disabled={loading || !evaluateApplied}>
          Export Dynamic
        </Button>
      </Stack>
    </Paper>
  );
}
