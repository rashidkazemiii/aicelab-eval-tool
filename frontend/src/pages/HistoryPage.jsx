import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, IconButton, Tooltip, Chip, CircularProgress,
  Alert, Dialog, DialogTitle, DialogContent, DialogActions, Button,
} from '@mui/material';
import DeleteIcon     from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { getHistory, getTestCycles, deleteTest } from '../services/api';

// ── helpers ──────────────────────────────────────────────────────────────────

const fmt = (v, d = 5) =>
  v == null || (typeof v === 'number' && isNaN(v)) ? '—' : Number(v).toFixed(d);

const fmtDate = (iso) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
};

const TYPE_COLOR = { OFT: '#4cceac', SRV: '#6870fa', SRV_FSA: '#f0a500' };


// ── columns for the combined result table (matches RESULT_COL_MAP order) ─────

// Per-cycle columns (left group)
const CYCLE_COLS = [
  { key: 'static_cof_time',  label: 'Static CoF time (s)',  digits: 3 },
  { key: 'static_cof',       label: 'Static CoF',           digits: 5 },
  { key: 'dynamic_cof_time', label: 'Dynamic CoF time (s)', digits: 3 },
  { key: 'dynamic_cof',      label: 'Dynamic CoF',          digits: 5 },
  { key: 'dynamic_sd',       label: 'Standard deviation',   digits: 5 },
  { key: 'dynamic_n',        label: 'Number of points',     digits: 0 },
  { key: 'dynamic_sigma',    label: 'Dynamic CoF sum',      digits: 5 },
  { key: 'dynamic_variance', label: 'Dynamic CoF variance', digits: 7 },
];

// Aggregate columns (right group) — drawn from result row at same index
const AGG_COLS = [
  { key: 'time_range',       label: 'Time range (s)',       digits: 3 },
  { key: 'static_mean_cof',  label: 'Static mean CoF',      digits: 5 },
  { key: 'static_sd',        label: 'Std dev (static)',     digits: 5 },
  { key: 'static_n',         label: '# points (static)',    digits: 0 },
  { key: 'static_sum',       label: 'Static CoF sum',       digits: 5 },
  { key: 'static_variance',  label: 'Static CoF variance',  digits: 7 },
  { key: 'dynamic_mean_cof', label: 'Dynamic mean CoF',     digits: 5 },
  { key: 'dynamic_sd',       label: 'Std dev (dynamic)',    digits: 5 },
  { key: 'dynamic_n',        label: '# points (dynamic)',   digits: 0 },
  { key: 'dynamic_sum',      label: 'Dynamic CoF sum',      digits: 5 },
  { key: 'dynamic_variance', label: 'Dynamic CoF variance', digits: 7 },
];

// header cell style helpers
const TH_CYCLE = { bgcolor: '#1f2a40', color: '#fff', fontWeight: 'bold',
  fontSize: '0.72rem', whiteSpace: 'nowrap', textAlign: 'right',
  borderRight: '1px solid #374151' };
const TH_AGG   = { bgcolor: '#2d3748', color: '#c8d5f5', fontWeight: 'bold',
  fontSize: '0.72rem', whiteSpace: 'nowrap', textAlign: 'right' };
const TH_FIRST = { ...TH_CYCLE, textAlign: 'left' };

// ── per-cycle dialog ─────────────────────────────────────────────────────────

function CyclesDialog({ testId, fileName, results, open, onClose }) {
  const [cycles,  setCycles]  = useState([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    if (!open || testId == null) return;
    setLoading(true);
    setError(null);
    getTestCycles(testId)
      .then(r => setCycles(r.data))
      .catch(() => setError('Could not load cycle data.'))
      .finally(() => setLoading(false));
  }, [open, testId]);

  const totalCols = 1 + CYCLE_COLS.length + AGG_COLS.length;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xl" fullWidth>
      <DialogTitle sx={{ bgcolor: '#1f2a40', color: '#4cceac', fontFamily: 'monospace' }}>
        Evaluation Result — {fileName}
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {loading && <Box sx={{ p: 4, textAlign: 'center' }}><CircularProgress /></Box>}
        {error   && <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>}

        {!loading && !error && (
          <TableContainer sx={{ maxHeight: '75vh' }}>
            <Table size="small" stickyHeader sx={{ fontFamily: 'monospace' }}>
              <TableHead>
                {/* ── group header row ── */}
                <TableRow>
                  <TableCell sx={{ ...TH_FIRST, bgcolor: '#1f2a40', borderBottom: 'none' }} />
                  <TableCell colSpan={CYCLE_COLS.length}
                    sx={{ bgcolor: '#1f2a40', color: '#4cceac', fontWeight: 'bold',
                      fontSize: '0.7rem', textAlign: 'center', letterSpacing: '0.08em',
                      borderRight: '2px solid #4a5568', borderBottom: 'none' }}>
                    PER-CYCLE
                  </TableCell>
                  <TableCell colSpan={AGG_COLS.length}
                    sx={{ bgcolor: '#2d3748', color: '#c8d5f5', fontWeight: 'bold',
                      fontSize: '0.7rem', textAlign: 'center', letterSpacing: '0.08em',
                      borderBottom: 'none' }}>
                    AGGREGATE
                  </TableCell>
                </TableRow>
                {/* ── column header row ── */}
                <TableRow>
                  <TableCell sx={{ ...TH_FIRST, borderRight: '1px solid #374151' }}>
                    Cycle
                  </TableCell>
                  {CYCLE_COLS.map((c, i) => (
                    <TableCell key={c.key}
                      sx={{ ...TH_CYCLE,
                        borderRight: i === CYCLE_COLS.length - 1
                          ? '2px solid #4a5568' : '1px solid #374151' }}>
                      {c.label}
                    </TableCell>
                  ))}
                  {AGG_COLS.map(c => (
                    <TableCell key={c.key} sx={TH_AGG}>{c.label}</TableCell>
                  ))}
                </TableRow>
              </TableHead>

              <TableBody>
                {cycles.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={totalCols}
                      sx={{ textAlign: 'center', color: '#aaa', py: 4 }}>
                      No data available
                    </TableCell>
                  </TableRow>
                ) : cycles.map((c) => {
                  // aggregate row aligned by index (row 0 = step/result 0, etc.)
                  const agg = results?.[c.cycle_index] ?? null;
                  const isAggRow = agg != null;

                  return (
                    <TableRow key={c.cycle_index}
                      sx={{
                        bgcolor: isAggRow ? '#f0f4ff' : 'inherit',
                        '&:hover': { bgcolor: '#eef2ff' },
                      }}>
                      {/* cycle number */}
                      <TableCell sx={{
                        fontFamily: 'monospace', fontSize: '0.78rem',
                        fontWeight: isAggRow ? 'bold' : 'normal',
                        borderRight: '1px solid #e0e0e0',
                      }}>
                        {c.cycle_index + 1}
                      </TableCell>

                      {/* per-cycle values */}
                      {CYCLE_COLS.map((col, i) => (
                        <TableCell key={col.key}
                          sx={{
                            fontFamily: 'monospace', fontSize: '0.78rem',
                            textAlign: 'right',
                            borderRight: i === CYCLE_COLS.length - 1
                              ? '2px solid #b0b8cc' : '1px solid #f0f0f0',
                          }}>
                          {col.digits === 0
                            ? (c[col.key] ?? '—')
                            : fmt(c[col.key], col.digits)}
                        </TableCell>
                      ))}

                      {/* aggregate values — shown only on aligned result row */}
                      {AGG_COLS.map(col => (
                        <TableCell key={col.key}
                          sx={{
                            fontFamily: 'monospace', fontSize: '0.78rem',
                            textAlign: 'right',
                            color: isAggRow ? '#1a237e' : '#bbb',
                            borderRight: '1px solid #f0f0f0',
                          }}>
                          {isAggRow
                            ? (col.digits === 0
                                ? (agg[col.key] ?? '—')
                                : fmt(agg[col.key], col.digits))
                            : '—'}
                        </TableCell>
                      ))}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DialogContent>

      <DialogActions sx={{ bgcolor: '#f4f6f8' }}>
        <Button onClick={onClose} variant="contained"
          sx={{ bgcolor: '#3e4396', '&:hover': { bgcolor: '#2d3270' } }}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// ── expandable test row ───────────────────────────────────────────────────────

function TestRow({ test, onDelete }) {
  const [cycleOpen, setCycleOpen] = useState(false);
  const multiStep = test.results?.length > 1;
  const baseName  = test.file_name?.split(/[\\/]/).pop();

  return (
    <>
      {/* ── main info row ── */}
      <TableRow hover>
        <TableCell sx={{ color: '#888', fontSize: '0.75rem' }}>{test.id}</TableCell>

        <TableCell sx={{ fontFamily: 'monospace', maxWidth: 200,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          <Tooltip title={test.file_name}>
            <span>{baseName}</span>
          </Tooltip>
        </TableCell>

        <TableCell>
          <Chip label={test.data_type} size="small"
            sx={{ bgcolor: TYPE_COLOR[test.data_type] ?? '#888',
                  color: '#fff', fontWeight: 'bold', fontSize: '0.7rem' }} />
        </TableCell>

        <TableCell sx={{ whiteSpace: 'nowrap', fontSize: '0.8rem' }}>
          {fmtDate(test.uploaded_at)}
        </TableCell>

        <TableCell sx={{ fontSize: '0.8rem', color: '#555' }}>
          {`w=${test.filter_window}  s=${test.static_range}%  d=${test.dynamic_min}–${test.dynamic_max}%`}
        </TableCell>

        <TableCell sx={{ fontSize: '0.75rem', color: '#888' }}>
          {multiStep ? `${test.results.length} steps` : '1 step'}
        </TableCell>

        <TableCell sx={{ whiteSpace: 'nowrap' }}>
          <Tooltip title="View per-cycle data">
            <IconButton size="small" onClick={() => setCycleOpen(true)}
              sx={{ color: '#3e4396' }}>
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton size="small" onClick={() => onDelete(test.id)}
              sx={{ color: '#c0392b' }}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </TableCell>
      </TableRow>

      <CyclesDialog
        open={cycleOpen}
        testId={test.id}
        fileName={baseName}
        results={test.results}
        onClose={() => setCycleOpen(false)}
      />
    </>
  );
}

// ── main page ─────────────────────────────────────────────────────────────────

export default function HistoryPage() {
  const [tests,   setTests]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    getHistory()
      .then(r => setTests(r.data))
      .catch(() => setError('Could not load history. Is the backend running?'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this test from the database?')) return;
    await deleteTest(id);
    load();
  };

  return (
    <Box sx={{ p: 3, height: '100%', overflowY: 'auto' }}>

      <Typography variant="h5" sx={{ color: '#1f2a40', fontWeight: 'bold', mb: 3 }}>
        Test History
      </Typography>

      {error   && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading && <Box sx={{ textAlign: 'center', mt: 8 }}><CircularProgress /></Box>}

      {!loading && !error && tests.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center', color: '#888' }}>
          No tests saved yet. Run an evaluation first.
        </Paper>
      )}

      {!loading && !error && tests.length > 0 && (
        <TableContainer component={Paper} elevation={1} sx={{ borderRadius: 3 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                {['ID', 'File', 'Type', 'Date', 'Parameters', 'Steps', ''].map(h => (
                  <TableCell key={h}
                    sx={{ bgcolor: '#1f2a40', color: '#fff',
                      fontWeight: 'bold', whiteSpace: 'nowrap' }}>
                    {h}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {tests.map(t => (
                <TestRow key={t.id} test={t} onDelete={handleDelete} />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

    </Box>
  );
}
