import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';

// Import pages
import MapPage from './pages/MapPage';
import BuildingsPage from './pages/BuildingsPage';
import SettingsPage from './pages/SettingsPage';

// Import components
import Navigation from './components/Navigation';

// Create Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
          {/* Header */}
          <AppBar position="static" elevation={1}>
            <Toolbar>
              <HomeIcon sx={{ mr: 2 }} />
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                AI Realtor - NYC Property Prospecting
              </Typography>
            </Toolbar>
          </AppBar>

          {/* Main Content */}
          <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
            {/* Navigation Sidebar */}
            <Navigation />

            {/* Page Content */}
            <Box component="main" sx={{ flex: 1, overflow: 'auto' }}>
              <Routes>
                <Route path="/" element={<MapPage />} />
                <Route path="/map" element={<MapPage />} />
                <Route path="/buildings" element={<BuildingsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Routes>
            </Box>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App; 