import { useState } from 'react';
import { useData } from '../context/DataContext';
import { getData, applyOffset, applyFilter, applyEvaluate, exportResult, exportDynamic } from '../services/api';

export const useAnalysis = () => {
  const { setAnalysisData } = useData();
  const [loading, setLoading] = useState(false);
  const [chartLines, setChartLines] = useState([]);
  const [calculated, setCalculated] = useState(false);
  const [offsetApplied, setOffsetApplied] = useState(false);
  const [evaluateApplied, setEvaluateApplied] = useState(false);
  const [minimaData, setMinimaData] = useState([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await getData();
      setAnalysisData(res.data);
      setChartLines([{ key: 'cof', color: '#1e88e5', label: 'CoF' }]);
      setCalculated(true);
    } catch (e) {
      console.error('Failed to fetch data:', e);
    } finally {
      setLoading(false);
    }
  };

  const offset = async () => {
    setLoading(true);
    try {
      const res = await applyOffset();
      setAnalysisData(res.data);
      setChartLines([
        { key: 'cof_shifted', color: '#43a047', label: 'CoF Shifted' },
      ]);
      setOffsetApplied(true);
    } catch (e) {
      console.error('Failed to apply offset:', e);
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
        { key: 'filtered', color: '#e53935', label: 'Filtered' },
      ]);
    } catch (e) {
      console.error('Failed to apply filter:', e);
    } finally {
      setLoading(false);
    }
  };

  const evaluate = async (staticRange, dynamicMin, dynamicMax) => {
    setLoading(true);
    try {
      const res = await applyEvaluate({
        static_cof_range: parseFloat(staticRange) || 10,
        beginning_dynamic_range: parseFloat(dynamicMin) || 20,
        ending_dynamic_range: parseFloat(dynamicMax) || 80,
      });
      setMinimaData(res.data);
      setEvaluateApplied(true);
    } catch (e) {
      console.error('Failed to evaluate:', e);
    } finally {
      setLoading(false);
    }
  };

  const triggerDownload = (data, filename) => {
    const url = window.URL.createObjectURL(new Blob([data]));
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => window.URL.revokeObjectURL(url), 1000);
  };

  const exportData = async () => {
    try {
      const res = await exportResult();
      triggerDownload(res.data, 'df_result.csv');
    } catch (e) {
      console.error('Failed to export result:', e);
    }
  };

  const exportDynamicData = async () => {
    try {
      const res = await exportDynamic();
      triggerDownload(res.data, 'df_dynamicCoF.csv');
    } catch (e) {
      console.error('Failed to export dynamic CoF:', e);
    }
  };

  return { fetchData, offset, filter, evaluate, exportData, exportDynamicData, loading, chartLines, calculated, offsetApplied, evaluateApplied, minimaData };
};
