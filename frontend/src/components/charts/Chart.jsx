import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Box, Typography } from '@mui/material';
import { DEFAULTS } from '../../constants/defaults';

function Chart({ data, xAxisKey, lines = [], markers = [], precision = DEFAULTS.chartPrecision }) {

  if (!data || data.length === 0) {
    return (
      <Box sx={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
        <Typography color="text.secondary">No data to display</Typography>
      </Box>
    );
  }

  const option = useMemo(() => {

    const lineSeries = lines.map(line => ({
      name: line.label || line.key,
      type: 'line',
      data: data.map(item => [item[xAxisKey], item[line.key]]),
      showSymbol: false,
      lineStyle: { width: line.width || 2, color: line.color || '#8884d8' },
      itemStyle: { color: line.color || '#8884d8' },
    }));

    const scatterSeries = markers.map(m => ({
      name: m.label,
      type: 'scatter',
      data: m.data,
      symbolSize: m.size || 7,
      itemStyle: { color: m.color },
      tooltip: {
        trigger: 'item',
        formatter: (p) =>
          `${p.marker}${p.seriesName}<br/>t = ${Number(p.value[0]).toFixed(3)} s<br/>CoF = ${Number(p.value[1]).toFixed(precision)}`,
      },
    }));

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          if (!params.length) return '';
          const x = Array.isArray(params[0].value) ? params[0].value[0] : params[0].axisValue;
          const rows = params
            .map(p => {
              const y = Array.isArray(p.value) ? p.value[1] : p.value;
              return `${p.marker}${p.seriesName}: ${Number(y).toFixed(precision)}`;
            })
            .join('<br/>');
          return `${Number(x).toFixed(3)} s<br/>${rows}`;
        },
      },
      legend: { top: 10 },
      grid: { left: 55, right: 20, top: 50, bottom: 90 },
      xAxis: { type: 'value', min: 'dataMin', max: 'dataMax', name: 's', nameLocation: 'end' },
      yAxis: { type: 'value' },
      dataZoom: [{ type: 'inside' }, { type: 'slider' }],
      series: [...lineSeries, ...scatterSeries],
    };

  }, [data, xAxisKey, lines, markers]);

  return (
    <ReactECharts
      option={option}
      style={{ height: '100%', width: '100%' }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
}

export default React.memo(Chart);
