import React from 'react';
import { Box, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Typography } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AssessmentIcon from '@mui/icons-material/Assessment';

export default function Sidebar({ activeTab, setActiveTab }) {
  const menuItems = [
    { id: 'upload', text: 'Upload Data', icon: <UploadFileIcon /> },
    { id: 'analysis', text: 'Friction Analysis', icon: <AssessmentIcon /> },
  ];

  return (
    <Box sx={{ 
      width: 240, 
      height: '100vh', 
      bgcolor: '#1f2a40', 
      borderRight: '1px solid #2d3748', 
      pt: 8,
      position: 'fixed', // Pins sidebar to the left
      left: 0,
      top: 0,
      zIndex: 1200 // Sits under the Navbar but above main content
    }}>
      <Typography variant="overline" sx={{ px: 3, color: '#4cceac', fontWeight: 'bold' }}>
        MENU
      </Typography>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.id} disablePadding>
            <ListItemButton 
              selected={activeTab === item.id}
              onClick={() => setActiveTab(item.id)}
              sx={{
                '&.Mui-selected': { bgcolor: '#3e4396', color: '#fff' },
                color: '#a3a3a3', py: 1.5
              }}
            >
              <ListItemIcon sx={{ color: 'inherit' }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );
}