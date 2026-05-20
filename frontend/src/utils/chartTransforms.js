/**
 * Pure functions for transforming API result data into chart-ready structures.
 * No React dependencies — works in any JS runtime (web, mobile, Node).
 */
import { COLORS } from '../constants/colors';

const makePoint = (t, v) => (t != null && v != null ? [t, v] : null);

/**
 * Converts raw evaluate result rows into scatter marker series for the CoF chart.
 * @param {Object[]} rows - Array of result objects from GET /result/json
 * @returns {Object[]} Marker series ready for the Chart component
 */
export function buildCofMarkers(rows) {
  return [
    {
      label: 'Static CoF',
      color: COLORS.staticCof,
      size:  11,
      data:  rows.map(r => makePoint(r.staticCoFTime,    r.staticCoF)).filter(Boolean),
    },
    {
      label: 'Dynamic CoF',
      color: COLORS.dynamicCof,
      size:  11,
      data:  rows.map(r => makePoint(r.dynamicCoFTime,   r.dynamicCoF)).filter(Boolean),
    },
    {
      label: 'Dyn CoF Start',
      color: COLORS.dynStart,
      size:  9,
      data:  rows.map(r => makePoint(r.startdynamicTime, r.startdynamicCoF)).filter(Boolean),
    },
    {
      label: 'Dyn CoF End',
      color: COLORS.dynEnd,
      size:  9,
      data:  rows.map(r => makePoint(r.enddynamicTime,   r.enddynamicCoF)).filter(Boolean),
    },
    {
      label: 'CoF Minima',
      color: COLORS.minima,
      size:  12,
      data:  rows.map(r => makePoint(r['Min Zeit'], r['Min CoF'])).filter(Boolean),
    },
  ];
}
