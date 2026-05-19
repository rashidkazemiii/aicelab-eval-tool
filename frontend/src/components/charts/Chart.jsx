import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Box, Typography } from '@mui/material';

function Chart({ data, xAxisKey, lines = [], precision = 8 }) {

  // If no data
  if (!data || data.length === 0) {
    return (
      <Box
        sx={{
          display: 'flex',
          height: '100%',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <Typography color="text.secondary">
          No data to display
        </Typography>
      </Box>
    );
  }

  // 🔥 Memoized chart option (VERY important for performance)
  const option = useMemo(() => {

    // X values
    const xData = data.map(item => item[xAxisKey]);

    // Series generation
    const series = lines.map(line => ({
      name: line.label || line.key,
      type: 'line',
      data: data.map(item => item[line.key]),
      showSymbol: false,
      smooth: true,
      lineStyle: {
        width: line.width || 2,
        color: line.color || '#8884d8'
      },
      itemStyle: {
        color: line.color || '#8884d8'
      }
    }));

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          const x = params[0].axisValue;
          const lines = params.map(p => `${p.marker}${p.seriesName}: ${Number(p.value).toFixed(precision)}`).join('<br/>');
          return `${x}<br/>${lines}`;
        }
      },

      legend: {
        top: 10
      },

      grid: {
        left: 50,
        right: 20,
        top: 50,
        bottom: 90 // space for zoom slider
      },

      xAxis: {
        type: 'category',
        data: xData,
        boundaryGap: false
      },

      yAxis: {
        type: 'value'
      },

      // 🔥 Zoom slider (this is the bar you remember)
      dataZoom: [
        {
          type: 'inside'
        },
        {
          type: 'slider'
        }
      ],

      series
    };

  }, [data, xAxisKey, lines]);

  return (
    <ReactECharts
      option={option}
      style={{ height: '100%', width: '100%' }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
}

// 🔥 Prevent unnecessary rerenders from parent
export default React.memo(Chart);