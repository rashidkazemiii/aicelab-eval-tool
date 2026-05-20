import { useState } from 'react';
import { useData } from '../context/DataContext';
import {
  getData, applyOffset, applyFilter, applyEvaluate, viewResult as openResult, getResult,
  getDisplacementData, applyDispOffset, applyDispFilter, applyDispEvaluate,
} from '../services/api';

export const useAnalysis = () => {
  const { setAnalysisData } = useData();

  const [loading,          setLoading]          = useState(false);
  const [error,            setError]            = useState(null);
  const [chartLines,       setChartLines]       = useState([]);
  const [calculated,       setCalculated]       = useState(false);
  const [offsetApplied,    setOffsetApplied]    = useState(false);
  const [evaluateApplied,  setEvaluateApplied]  = useState(false);
  const [cofMarkers,       setCofMarkers]       = useState([]);

  // Displacement state
  const [dispData,          setDispData]          = useState([]);
  const [dispLines,         setDispLines]         = useState([]);
  const [dispOffsetApplied, setDispOffsetApplied] = useState(false);
  const [dispEvalApplied,   setDispEvalApplied]   = useState(false);

  // ── CoF flow ──────────────────────────────────────────────────────────────

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await getData();
      setAnalysisData(res.data);
      setChartLines([{ key: 'cof', color: '#1e88e5', label: 'CoF' }]);
      setCalculated(true);
    } catch (e) {
      console.error('fetchData failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const offset = async () => {
    setLoading(true);
    try {
      const res = await applyOffset();
      setAnalysisData(res.data);
      setChartLines([{ key: 'cof_shifted', color: '#43a047', label: 'CoF Shifted' }]);
      setOffsetApplied(true);
    } catch (e) {
      console.error('offset failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const filter = async (filterPoints) => {
    const window = parseInt(filterPoints) || 25;
    setLoading(true);
    try {
      const res = await applyFilter(window);
      setAnalysisData(res.data);
      setChartLines([
        { key: 'cof_shifted', color: '#43a047', label: 'CoF Shifted' },
        { key: 'filtered',    color: '#e53935', label: 'Filtered'    },
      ]);
    } catch (e) {
      console.error('filter failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const evaluate = async (staticRange, dynamicMin, dynamicMax) => {
    setLoading(true);
    setError(null);
    try {
      await applyEvaluate({
        static_cof_range:        parseFloat(staticRange) || 10,
        beginning_dynamic_range: parseFloat(dynamicMin)  || 20,
        ending_dynamic_range:    parseFloat(dynamicMax)  || 80,
      });
      setEvaluateApplied(true);
      const res = await getResult();
      const rows = res.data.filter(r => r != null);
      const pt = (t, v) => t != null && v != null ? [t, v] : null;
      setCofMarkers([
        { label: 'Static CoF',    color: '#e91e63', size: 7,  data: rows.map(r => pt(r.staticCoFTime,    r.staticCoF)).filter(Boolean) },
        { label: 'Dynamic CoF',   color: '#ff9800', size: 7,  data: rows.map(r => pt(r.dynamicCoFTime,   r.dynamicCoF)).filter(Boolean) },
        { label: 'Dyn CoF Start', color: '#4caf50', size: 6,  data: rows.map(r => pt(r.startdynamicTime, r.startdynamicCoF)).filter(Boolean) },
        { label: 'Dyn CoF End',   color: '#9c27b0', size: 6,  data: rows.map(r => pt(r.enddynamicTime,   r.enddynamicCoF)).filter(Boolean) },
        { label: 'CoF Minima',    color: '#f44336', size: 8,  data: rows.map(r => pt(r['Min Zeit'],       r['Min CoF'])).filter(Boolean) },
      ]);
    } catch (e) {
      const msg = e?.response?.data?.error || e.message || 'Evaluate failed';
      setError(msg);
      console.error('evaluate failed:', e);
    } finally {
      setLoading(false);
    }
  };

  // ── Displacement flow ─────────────────────────────────────────────────────

  const generateDisplacement = async () => {
    setLoading(true);
    try {
      const res = await getDisplacementData();
      setDispData(res.data);
      setDispLines([{ key: 'stroke', color: '#ff9800', label: 'Stroke' }]);
    } catch (e) {
      console.error('generateDisplacement failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const displacementOffset = async () => {
    setLoading(true);
    try {
      const res = await applyDispOffset();
      setDispData(res.data);
      setDispLines([
        { key: 'stroke',         color: '#ff9800', label: 'Stroke'         },
        { key: 'stroke_shifted', color: '#ab47bc', label: 'Stroke Shifted' },
      ]);
      setDispOffsetApplied(true);
    } catch (e) {
      console.error('displacementOffset failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const displacementFilter = async (filterPoints) => {
    const window = parseInt(filterPoints) || 25;
    setLoading(true);
    try {
      const res = await applyDispFilter(window);
      setDispData(res.data);
      setDispLines([
        { key: 'stroke',          color: '#ff9800', label: 'Stroke'          },
        { key: 'stroke_shifted',  color: '#ab47bc', label: 'Stroke Shifted'  },
        { key: 'stroke_filtered', color: '#26c6da', label: 'Stroke Filtered' },
      ]);
    } catch (e) {
      console.error('displacementFilter failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const displacementEvaluate = async () => {
    setLoading(true);
    try {
      await applyDispEvaluate();
      setDispEvalApplied(true);
    } catch (e) {
      console.error('displacementEvaluate failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const viewResult = () => openResult();

  return {
    // CoF
    fetchData, offset, filter, evaluate, viewResult,
    loading, error, chartLines, calculated, offsetApplied, evaluateApplied, cofMarkers,
    // Displacement
    generateDisplacement, displacementOffset, displacementFilter, displacementEvaluate,
    dispData, dispLines, dispOffsetApplied, dispEvalApplied,
  };
};
