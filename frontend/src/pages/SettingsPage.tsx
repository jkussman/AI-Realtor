import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  Divider,
  FormControlLabel,
  Switch,
  Card,
  CardContent,
  CardActions,
  Snackbar
} from '@mui/material';
import {
  Save as SaveIcon,
  Science as TestIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon
} from '@mui/icons-material';

// Import API functions
import { testConnection } from '../utils/api';

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState({
    openaiApiKey: '',
    gmailClientId: '',
    gmailClientSecret: '',
    estatedApiKey: '',
    reonmyApiKey: '',
    serpApiKey: '',
    fromEmail: '',
    fromName: '',
    enableNotifications: true,
    autoApprove: false
  });

  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });

  const [testingConnection, setTestingConnection] = useState(false);

  const showNotification = (message: string, severity: 'success' | 'error' | 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };

  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setSettings(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleSwitchChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setSettings(prev => ({
      ...prev,
      [field]: event.target.checked
    }));
  };

  const handleSaveSettings = () => {
    // In a real application, this would save to backend or local storage
    localStorage.setItem('ai-realtor-settings', JSON.stringify(settings));
    showNotification('Settings saved successfully!', 'success');
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    try {
      const response = await testConnection();
      if (response.success) {
        showNotification('API connection successful!', 'success');
      } else {
        showNotification(`Connection failed: ${response.error}`, 'error');
      }
    } catch (error) {
      showNotification(`Connection test failed: ${error}`, 'error');
    } finally {
      setTestingConnection(false);
    }
  };

  const handleLoadSettings = () => {
    const savedSettings = localStorage.getItem('ai-realtor-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(parsed);
        showNotification('Settings loaded from saved data', 'info');
      } catch (error) {
        showNotification('Failed to load saved settings', 'error');
      }
    } else {
      showNotification('No saved settings found', 'info');
    }
  };

  // Load settings on component mount
  React.useEffect(() => {
    handleLoadSettings();
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure API keys and application settings for the AI Realtor system.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* API Configuration */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SecurityIcon sx={{ mr: 1 }} color="primary" />
                <Typography variant="h6">
                  API Configuration
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    label="OpenAI API Key"
                    type="password"
                    fullWidth
                    value={settings.openaiApiKey}
                    onChange={handleInputChange('openaiApiKey')}
                    helperText="Required for AI building analysis and contact generation"
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Gmail Client ID"
                    fullWidth
                    value={settings.gmailClientId}
                    onChange={handleInputChange('gmailClientId')}
                    helperText="OAuth2 client ID for Gmail API"
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Gmail Client Secret"
                    type="password"
                    fullWidth
                    value={settings.gmailClientSecret}
                    onChange={handleInputChange('gmailClientSecret')}
                    helperText="OAuth2 client secret for Gmail API"
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Estated API Key (Optional)"
                    type="password"
                    fullWidth
                    value={settings.estatedApiKey}
                    onChange={handleInputChange('estatedApiKey')}
                    helperText="For enhanced property data"
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Reonomy API Key (Optional)"
                    type="password"
                    fullWidth
                    value={settings.reonmyApiKey}
                    onChange={handleInputChange('reonmyApiKey')}
                    helperText="For commercial property data"
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    label="SerpAPI Key (Optional)"
                    type="password"
                    fullWidth
                    value={settings.serpApiKey}
                    onChange={handleInputChange('serpApiKey')}
                    helperText="For enhanced web search capabilities"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Email Configuration */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Email Configuration
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    label="From Email"
                    type="email"
                    fullWidth
                    value={settings.fromEmail}
                    onChange={handleInputChange('fromEmail')}
                    helperText="Your Gmail address"
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    label="From Name"
                    fullWidth
                    value={settings.fromName}
                    onChange={handleInputChange('fromName')}
                    helperText="Name to appear in emails"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Application Preferences */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Preferences
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableNotifications}
                    onChange={handleSwitchChange('enableNotifications')}
                  />
                }
                label="Enable notifications"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoApprove}
                    onChange={handleSwitchChange('autoApprove')}
                  />
                }
                label="Auto-approve buildings (experimental)"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Actions
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveSettings}
                >
                  Save Settings
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<TestIcon />}
                  onClick={handleTestConnection}
                  disabled={testingConnection}
                >
                  {testingConnection ? 'Testing...' : 'Test API Connection'}
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={handleLoadSettings}
                >
                  Reload Settings
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Help Section */}
        <Grid item xs={12}>
          <Alert severity="info">
            <Typography variant="body2" gutterBottom>
              <strong>Setup Instructions:</strong>
            </Typography>
            <Typography variant="body2" component="div">
              1. Get an OpenAI API key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">platform.openai.com</a>
              <br />
              2. Set up Gmail API credentials in <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer">Google Cloud Console</a>
              <br />
              3. Optional: Get API keys for enhanced data sources (Estated, Reonomy, SerpAPI)
              <br />
              4. Save your settings and test the connection
            </Typography>
          </Alert>
        </Grid>
      </Grid>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={4000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SettingsPage; 