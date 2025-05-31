import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Email as EmailIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Business as BuildingIcon
} from '@mui/icons-material';

// Import API functions and types
import { getBuildings, approveBuilding, Building } from '../utils/api';

const BuildingsPage: React.FC = () => {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });

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

  const fetchBuildings = async () => {
    setLoading(true);
    try {
      const response = await getBuildings();
      if (response.success && response.data) {
        setBuildings(response.data);
      } else {
        showNotification(`Error fetching buildings: ${response.error}`, 'error');
      }
    } catch (error) {
      showNotification(`Failed to fetch buildings: ${error}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveBuilding = async (buildingId: number) => {
    try {
      const response = await approveBuilding(buildingId);
      if (response.success) {
        showNotification('Building approved! Outreach process started.', 'success');
        // Refresh buildings list
        fetchBuildings();
      } else {
        showNotification(`Error approving building: ${response.error}`, 'error');
      }
    } catch (error) {
      showNotification(`Failed to approve building: ${error}`, 'error');
    }
  };

  const handleViewDetails = (building: Building) => {
    setSelectedBuilding(building);
    setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setSelectedBuilding(null);
    setDetailsOpen(false);
  };

  const getStatusChip = (building: Building) => {
    if (building.reply_received) {
      return <Chip label="Reply Received" color="success" size="small" />;
    } else if (building.email_sent) {
      return <Chip label="Email Sent" color="primary" size="small" />;
    } else if (building.approved) {
      return <Chip label="Processing" color="warning" size="small" />;
    } else {
      return <Chip label="Pending Approval" color="default" size="small" />;
    }
  };

  useEffect(() => {
    fetchBuildings();
  }, []);

  const approvedBuildings = buildings.filter(b => b.approved);
  const pendingBuildings = buildings.filter(b => !b.approved);
  const emailsSent = buildings.filter(b => b.email_sent).length;
  const repliesReceived = buildings.filter(b => b.reply_received).length;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Discovered Buildings
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Manage buildings discovered through your map searches. Approve buildings to trigger automated outreach.
        </Typography>

        {/* Statistics */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Buildings
                </Typography>
                <Typography variant="h4">
                  {buildings.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Approved
                </Typography>
                <Typography variant="h4" color="primary">
                  {approvedBuildings.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Emails Sent
                </Typography>
                <Typography variant="h4" color="success.main">
                  {emailsSent}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Replies Received
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {repliesReceived}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchBuildings}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* No Buildings State */}
      {!loading && buildings.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body1">
            No buildings found yet. Go to the Map page and draw some bounding boxes to start discovering buildings!
          </Typography>
        </Alert>
      )}

      {/* Buildings Table */}
      {!loading && buildings.length > 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Address</TableCell>
                <TableCell>Building Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Contact</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {buildings.map((building) => (
                <TableRow key={building.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {building.address}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {building.name || (
                      <Typography variant="body2" color="text.secondary" fontStyle="italic">
                        No name available
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={building.building_type} 
                      variant="outlined" 
                      size="small"
                      icon={<BuildingIcon />}
                    />
                  </TableCell>
                  <TableCell>
                    {getStatusChip(building)}
                  </TableCell>
                  <TableCell>
                    {building.contact_email ? (
                      <Box>
                        <Typography variant="body2">
                          {building.contact_name || 'Unknown'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {building.contact_email}
                        </Typography>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary" fontStyle="italic">
                        No contact found
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <IconButton
                        size="small"
                        onClick={() => handleViewDetails(building)}
                        title="View Details"
                      >
                        <InfoIcon />
                      </IconButton>
                      
                      {!building.approved && (
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleApproveBuilding(building.id)}
                          title="Approve Building"
                        >
                          <ApproveIcon />
                        </IconButton>
                      )}
                      
                      {building.email_sent && (
                        <IconButton
                          size="small"
                          color="success"
                          title="Email Sent"
                          disabled
                        >
                          <EmailIcon />
                        </IconButton>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Building Details Dialog */}
      <Dialog open={detailsOpen} onClose={handleCloseDetails} maxWidth="md" fullWidth>
        <DialogTitle>
          Building Details
        </DialogTitle>
        <DialogContent>
          {selectedBuilding && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Address"
                  value={selectedBuilding.address}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Building Name"
                  value={selectedBuilding.name || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Building Type"
                  value={selectedBuilding.building_type}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Contact Name"
                  value={selectedBuilding.contact_name || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Contact Email"
                  value={selectedBuilding.contact_email || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Approved"
                  value={selectedBuilding.approved ? 'Yes' : 'No'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Email Sent"
                  value={selectedBuilding.email_sent ? 'Yes' : 'No'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Reply Received"
                  value={selectedBuilding.reply_received ? 'Yes' : 'No'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDetails}>Close</Button>
          {selectedBuilding && !selectedBuilding.approved && (
            <Button
              variant="contained"
              onClick={() => {
                handleApproveBuilding(selectedBuilding.id);
                handleCloseDetails();
              }}
              startIcon={<ApproveIcon />}
            >
              Approve Building
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
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

export default BuildingsPage; 