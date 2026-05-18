import { useState } from 'react';
import { useData } from '../context/DataContext';
import { getData, applyOffset, applyFilter } from '../services/api';

export const useAnalysis = () => {
  const { setAnalysisData } = useData();
  const [loading, setLoading] = useState(false);
  const [chartLines, setChartLines] = useState([]);
  const [offsetApplied, setOffsetApplied] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await getData();
      setAnalysisData(res.data);
      setChartLines([{ key: 'cof', color: '#1e88e5', label: 'CoF' }]);
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
      setChartLines([{ key: 'offset', color: '#1e88e5', label: 'Offset CoF' }]);
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
        { key: 'offset', color: '#1e88e5', label: 'Offset' },
        { key: 'filtered', color: '#e53935', label: 'Filtered' },
      ]);
    } catch (e) {
      console.error('Failed to apply filter:', e);
    } finally {
      setLoading(false);
    }
  };

  return { fetchData, offset, filter, loading, chartLines, offsetApplied };
};
