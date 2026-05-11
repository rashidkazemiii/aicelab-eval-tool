import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { Box, Typography } from '@mui/material';

export default function Chart({ data, xAxisKey, lines = [] }) {
  // If no data is provided yet
  if (!data || data.length === 0) {
    return (
      <Box sx={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
        <Typography color="text.secondary">No data to display</Typography>
      </Box>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
        <XAxis 
          dataKey={xAxisKey} 
          tick={{ fontSize: 11 }} 
          tickLine={false}
          axisLine={{ stroke: '#eee' }}
        />
        <YAxis 
          tick={{ fontSize: 11 }} 
          tickLine={false}
          axisLine={{ stroke: '#eee' }}
        />
        <Tooltip 
          contentStyle={{ fontSize: '12px', borderRadius: '8px', border: 'none', boxShadow: '0px 4px 10px rgba(0,0,0,0.1)' }}
        />
        <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
        
        {lines.map((line, index) => (
          <Line
            key={index}
            type="monotone"
            dataKey={line.key}
            stroke={line.color || "#8884d8"}
            dot={false}
            strokeWidth={line.width || 2}
            name={line.label || line.key}
            animationDuration={300}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}