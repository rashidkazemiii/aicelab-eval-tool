import { useState } from 'react';
import { getDisplacementData, applyDispOffset, applyDispFilter, applyDispEvaluate } from '../services/api';
import { COLORS } from '../constants/colors';
import { DEFAULTS } from '../constants/defaults';

/**
 * Manages the displacement (stroke) processing workflow:
 * generate → offset → filter → evaluate.
 * Independent from the CoF workflow — has its own loading and error state.
 */
export const useDisplacement = () => {
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState(null);
  const [dispData,      setDispData]      = useState([]);
  const [dispLines,     setDispLines]     = useState([]);
  const [offsetApplied, setOffsetApplied] = useState(false);
  const [evalApplied,   setEvalApplied]   = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const res = await getDisplacementData();
      setDispData(res.data);
      setDispLines([{ key: 'stroke', color: COLORS.stroke, label: 'Stroke' }]);
    } catch (e) {
      console.error('generateDisplacement failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const offset = async () => {
    setLoading(true);
    try {
      const res = await applyDispOffset();
      setDispData(res.data);
      setDispLines([
        { key: 'stroke',         color: COLORS.stroke,      label: 'Stroke'         },
        { key: 'stroke_shifted', color: COLORS.strokeShift, label: 'Stroke Shifted' },
      ]);
      setOffsetApplied(true);
    } catch (e) {
      console.error('displacementOffset failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const filter = async (filterPoints) => {
    const window = parseInt(filterPoints) || parseInt(DEFAULTS.filterPoints);
    setLoading(true);
    try {
      const res = await applyDispFilter(window);
      setDispData(res.data);
      setDispLines([
        { key: 'stroke',          color: COLORS.stroke,      label: 'Stroke'          },
        { key: 'stroke_shifted',  color: COLORS.strokeShift, label: 'Stroke Shifted'  },
        { key: 'stroke_filtered', color: COLORS.strokeFilt,  label: 'Stroke Filtered' },
      ]);
    } catch (e) {
      console.error('displacementFilter failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const evaluate = async () => {
    setLoading(true);
    try {
      await applyDispEvaluate();
      setEvalApplied(true);
    } catch (e) {
      console.error('displacementEvaluate failed:', e);
    } finally {
      setLoading(false);
    }
  };

  return {
    generate, offset, filter, evaluate,
    loading, error, dispData, dispLines, offsetApplied, evalApplied,
  };
};
