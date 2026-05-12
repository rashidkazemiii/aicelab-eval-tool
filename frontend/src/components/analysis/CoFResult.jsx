import React from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Box 
} from '@mui/material';

export default function CoFResult({ results }) {
  // Exact styles for the engineering table look
  const cellStyle = {
    padding: '2px 4px',
    fontSize: '0.7rem',
    border: '1px solid #e0e0e0',
    textAlign: 'center',
    height: '24px',
    whiteSpace: 'nowrap'
  };

  const headerStyle = {
    ...cellStyle,
    fontWeight: 'bold',
    bgcolor: '#f5f7fa',
    color: '#333'
  };

  return (
    <TableContainer sx={{ overflowX: 'auto', mt: 1 }}>
      <Table sx={{ minWidth: 800, borderCollapse: 'collapse', border: '1px solid #e0e0e0' }} size="small">
        <TableHead>
          {/* Main Merged Headers */}
          <TableRow>
            <TableCell sx={{ ...headerStyle, width: '80px' }}>Time range</TableCell>
            <TableCell colSpan={5} sx={{ ...headerStyle, bgcolor: '#ebf0ff', color: '#3e4396' }}>
              Static CoF statistics
            </TableCell>
            <TableCell colSpan={5} sx={{ ...headerStyle, bgcolor: '#e6faf5', color: '#2d9d78' }}>
              Dynamic CoF statistics
            </TableCell>
          </TableRow>
          
          {/* Detailed Sub-headers */}
          <TableRow>
            <TableCell sx={headerStyle}>(s)</TableCell>
            {/* Static Group */}
            <TableCell sx={headerStyle}>Static mean CoF</TableCell>
            <TableCell sx={headerStyle}>Standard deviation</TableCell>
            <TableCell sx={headerStyle}>Number of points</TableCell>
            <TableCell sx={headerStyle}>Static CoF sum</TableCell>
            <TableCell sx={headerStyle}>Static CoF variance</TableCell>
            {/* Dynamic Group */}
            <TableCell sx={headerStyle}>Dynamic mean CoF</TableCell>
            <TableCell sx={headerStyle}>Standard deviation</TableCell>
            <TableCell sx={headerStyle}>Number of points</TableCell>
            <TableCell sx={headerStyle}>Dynamic CoF sum</TableCell>
            <TableCell sx={headerStyle}>Dynamic CoF variance</TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          <TableRow>
            {/* Time Data */}
            <TableCell sx={{ ...cellStyle, fontWeight: 'bold' }}>
              {results?.timeRange || '0-45'}
            </TableCell>
            {/* Static Data */}
            <TableCell sx={cellStyle}>{results?.staticMean || '0.12739801'}</TableCell>
            <TableCell sx={cellStyle}>{results?.staticStd || '0.00339333'}</TableCell>
            <TableCell sx={cellStyle}>{results?.staticPoints || '89'}</TableCell>
            <TableCell sx={cellStyle}>{results?.staticSum || '11.3384231'}</TableCell>
            <TableCell sx={cellStyle}>{results?.staticVar || '1.445505856'}</TableCell>
            {/* Dynamic Data */}
            <TableCell sx={cellStyle}>{results?.dynamicMean || '0.12499603'}</TableCell>
            <TableCell sx={cellStyle}>{results?.dynamicStd || '0.00460277'}</TableCell>
            <TableCell sx={cellStyle}>{results?.dynamicPoints || '29006'}</TableCell>
            <TableCell sx={cellStyle}>{results?.dynamicSum || '3625.63486'}</TableCell>
            <TableCell sx={cellStyle}>{results?.dynamicVar || '453.804445'}</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  );
}