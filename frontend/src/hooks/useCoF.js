import { useState } from 'react';
import { useData } from '../context/DataContext';
import { getData, applyOffset, applyFilter, applyEvaluate, getResult, viewResult as openResult } from '../services/api';
import { buildCofMarkers } from '../utils/chartTransforms';
import { COLORS } from '../constants/colors';
import { DEFAULTS } from '../constants/defaults';

/**
 * Manages the CoF processing workflow: fetch → offset → filter → evaluate.
 * Each action updates analysisData in global context and chartLines locally.
 */
export const useCoF = () => {
  const { setAnalysisData } = useData();

  const [loading,         setLoading]         = useState(false);
  const [error,           setError]           = useState(null);
  const [chartLines,      setChartLines]      = useState([]);
  const [calculated,      setCalculated]      = useState(false);
  const [offsetApplied,   setOffsetApplied]   = useState(false);
  const [evaluateApplied, setEvaluateApplied] = useState(false);
  const [cofMarkers,      setCofMarkers]      = useState([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await getData();
      setAnalysisData(res.data);
      setChartLines([{ key: 'cof', color: COLORS.cof, label: 'CoF' }]);
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
      setChartLines([{ key: 'cof_shifted', color: COLORS.cofShifted, label: 'CoF Shifted' }]);
      setOffsetApplied(true);
    } catch (e) {
      console.error('offset failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const filter = async (filterPoints) => {
    const window = parseInt(filterPoints) || parseInt(DEFAULTS.filterPoints);
    setLoading(true);
    try {
      const res = await applyFilter(window);
      setAnalysisData(res.data);
      setChartLines([
        { key: 'cof_shifted', color: COLORS.cofShifted, label: 'CoF Shifted' },
        { key: 'filtered',    color: COLORS.filtered,   label: 'Filtered'    },
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
        static_cof_range:        parseFloat(staticRange) || parseFloat(DEFAULTS.staticRange),
        beginning_dynamic_range: parseFloat(dynamicMin)  || parseFloat(DEFAULTS.dynamicMin),
        ending_dynamic_range:    parseFloat(dynamicMax)  || parseFloat(DEFAULTS.dynamicMax),
      });
      setEvaluateApplied(true);
      const res = await getResult();
      setCofMarkers(buildCofMarkers(res.data.filter(r => r != null)));
    } catch (e) {
      setError(e?.response?.data?.error || e.message || 'Evaluate failed');
      console.error('evaluate failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const viewResult = () => openResult();

  return {
    fetchData, offset, filter, evaluate, viewResult,
    loading, error, chartLines, calculated, offsetApplied, evaluateApplied, cofMarkers,
  };
};
