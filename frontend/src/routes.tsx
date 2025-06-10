import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';

// Import pages
import MapPage from './pages/MapPage';
import BuildingsPage from './pages/BuildingsPage';
import SettingsPage from './pages/SettingsPage';

const AppRoutes: React.FC = () => {
  return (
    <Box component="main" sx={{ flex: 1, overflow: 'auto' }}>
      <Routes>
        <Route path="/" element={<MapPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/buildings" element={<BuildingsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Box>
  );
};

export default AppRoutes; 