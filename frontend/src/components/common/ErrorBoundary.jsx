import React from 'react';
import { Box, Typography } from '@mui/material';

/**
 * Catches rendering errors in child components so a chart crash
 * doesn't take down the entire Analysis page.
 */
export class ErrorBoundary extends React.Component {
  state = { hasError: false, message: '' };

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error.message };
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <Typography color="error" variant="body2">
            Rendering error: {this.state.message}
          </Typography>
        </Box>
      );
    }
    return this.props.children;
  }
}
