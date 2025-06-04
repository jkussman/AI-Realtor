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
  Business as BuildingIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

// Import API functions and types
import { getBuildings, approveBuilding, deleteBuilding, deleteAllBuildings, Building } from '../utils/api';

const BuildingsPage: React.FC = () => {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteAllDialogOpen, setDeleteAllDialogOpen] = useState(false);
  const [buildingToDelete, setBuildingToDelete] = useState<Building | null>(null);
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

  const handleDeleteClick = (building: Building) => {
    setBuildingToDelete(building);
    setDeleteDialogOpen(true);
  };

  const handleDeleteCancel = () => {
    setBuildingToDelete(null);
    setDeleteDialogOpen(false);
  };

  const handleDeleteConfirm = async () => {
    if (!buildingToDelete) return;

    try {
      const response = await deleteBuilding(buildingToDelete.id);
      if (response.success) {
        showNotification(`Building "${buildingToDelete.address}" deleted successfully!`, 'success');
        // Refresh buildings list
        fetchBuildings();
      } else {
        showNotification(`Error deleting building: ${response.error}`, 'error');
      }
    } catch (error) {
      showNotification(`Failed to delete building: ${error}`, 'error');
    } finally {
      setBuildingToDelete(null);
      setDeleteDialogOpen(false);
    }
  };

  const handleDeleteAllClick = () => {
    setDeleteAllDialogOpen(true);
  };

  const handleDeleteAllCancel = () => {
    setDeleteAllDialogOpen(false);
  };

  const handleDeleteAllConfirm = async () => {
    try {
      const response = await deleteAllBuildings();
      if (response.success) {
        showNotification(response.data?.message || 'All buildings deleted successfully!', 'success');
        // Refresh buildings list
        fetchBuildings();
      } else {
        showNotification(`Error deleting all buildings: ${response.error}`, 'error');
      }
    } catch (error) {
      showNotification(`Failed to delete all buildings: ${error}`, 'error');
    } finally {
      setDeleteAllDialogOpen(false);
    }
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
          {buildings.length > 0 && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDeleteAllClick}
              disabled={loading}
            >
              Delete All Buildings
            </Button>
          )}
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
                <TableCell>Co-op/Mixed Use</TableCell>
                <TableCell>Apartments</TableCell>
                <TableCell>2BR Info</TableCell>
                <TableCell>Amenities</TableCell>
                <TableCell>Status</TableCell>
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
                    {building.neighborhood && (
                      <Typography variant="caption" color="text.secondary">
                        {building.neighborhood}
                      </Typography>
                    )}
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
                    {building.year_built && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        Built {building.year_built}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Box>
                      {building.is_coop && (
                        <Chip label="Co-op" size="small" color="primary" sx={{ mr: 0.5, mb: 0.5 }} />
                      )}
                      {building.is_mixed_use && (
                        <Chip label="Mixed Use" size="small" color="secondary" sx={{ mr: 0.5, mb: 0.5 }} />
                      )}
                      {!building.is_coop && !building.is_mixed_use && (
                        <Typography variant="body2" color="text.secondary">
                          Rental
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {building.total_apartments ? `${building.total_apartments} total` : 'Unknown'}
                    </Typography>
                    {building.stories && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {building.stories} stories
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Box>
                      {building.two_bedroom_apartments ? (
                        <Typography variant="body2">
                          {building.two_bedroom_apartments} 2BR units
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No 2BR info
                        </Typography>
                      )}
                      {building.recent_2br_rent && (
                        <Typography variant="caption" color="success.main" display="block">
                          ${building.recent_2br_rent.toLocaleString()}/mo
                        </Typography>
                      )}
                      {building.rent_range_2br && !building.recent_2br_rent && (
                        <Typography variant="caption" color="success.main" display="block">
                          {building.rent_range_2br}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box>
                      {building.has_laundry && (
                        <Chip label="Laundry" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                      )}
                      {building.amenities && building.amenities.length > 0 && (
                        <Typography variant="caption" color="text.secondary">
                          +{building.amenities.length} amenities
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    {getStatusChip(building)}
                    {building.recent_availability && (
                      <Chip label="Available" size="small" color="success" sx={{ ml: 0.5 }} />
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

                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteClick(building)}
                        title="Delete Building"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleDeleteCancel}>
        <DialogTitle>
          <Typography variant="h6" color="error">
            Delete Building
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to do this? It will be deleted forever.
          </Typography>
          {buildingToDelete && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="body2" fontWeight="medium">
                Building to delete:
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {buildingToDelete.address}
              </Typography>
              {buildingToDelete.name && (
                <Typography variant="body2" color="text.secondary">
                  {buildingToDelete.name}
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
            startIcon={<DeleteIcon />}
          >
            Delete Forever
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete All Confirmation Dialog */}
      <Dialog open={deleteAllDialogOpen} onClose={handleDeleteAllCancel}>
        <DialogTitle>
          Delete All Buildings
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to do this? All {buildings.length} buildings will be deleted forever.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteAllCancel} color="primary">
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteAllConfirm} 
            color="error" 
            variant="contained"
            startIcon={<DeleteIcon />}
          >
            Delete All Forever
          </Button>
        </DialogActions>
      </Dialog>

      {/* Building Details Dialog */}
      <Dialog open={detailsOpen} onClose={handleCloseDetails} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Typography variant="h5">Building Details</Typography>
          {selectedBuilding && (
            <Typography variant="subtitle1" color="text.secondary">
              {selectedBuilding.address}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedBuilding && (
            <Grid container spacing={3} sx={{ mt: 1 }}>
              {/* Basic Information */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom color="primary">
                  Basic Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="Building Name"
                  value={selectedBuilding.name || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="Neighborhood"
                  value={selectedBuilding.neighborhood || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="Year Built"
                  value={selectedBuilding.year_built || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="Building Type"
                  value={selectedBuilding.building_type}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="Building Style"
                  value={selectedBuilding.building_style || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="Stories"
                  value={selectedBuilding.stories || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>

              {/* Building Classification */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom color="primary">
                  Building Classification
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {selectedBuilding.is_coop && (
                    <Chip label="Co-op" color="primary" />
                  )}
                  {selectedBuilding.is_mixed_use && (
                    <Chip label="Mixed Use" color="secondary" />
                  )}
                  {!selectedBuilding.is_coop && !selectedBuilding.is_mixed_use && (
                    <Chip label="Rental Building" color="default" />
                  )}
                  {selectedBuilding.recent_availability && (
                    <Chip label="Currently Available" color="success" />
                  )}
                </Box>
              </Grid>

              {/* Apartment Information */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom color="primary">
                  Apartment Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="Total Apartments"
                  value={selectedBuilding.total_apartments || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="2-Bedroom Apartments"
                  value={selectedBuilding.two_bedroom_apartments || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="Recent 2BR Rent"
                  value={selectedBuilding.recent_2br_rent ? `$${selectedBuilding.recent_2br_rent.toLocaleString()}/month` : 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              {selectedBuilding.rent_range_2br && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="2BR Rent Range"
                    value={selectedBuilding.rent_range_2br}
                    fullWidth
                    InputProps={{ readOnly: true }}
                  />
                </Grid>
              )}

              {/* Amenities & Features */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom color="primary">
                  Amenities & Features
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Laundry Facilities"
                  value={selectedBuilding.has_laundry ? 
                    (selectedBuilding.laundry_type ? 
                      selectedBuilding.laundry_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
                      'Available') : 
                    'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Pet Policy"
                  value={selectedBuilding.pet_policy ? 
                    selectedBuilding.pet_policy.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
                    'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              {selectedBuilding.amenities && selectedBuilding.amenities.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="body2" gutterBottom>
                    Building Amenities:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedBuilding.amenities.map((amenity, index) => (
                      <Chip key={index} label={amenity} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Grid>
              )}

              {/* Management & Contact */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom color="primary">
                  Management & Contact Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Management Company"
                  value={selectedBuilding.management_company || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Contact Information"
                  value={selectedBuilding.contact_info || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Property Manager"
                  value={selectedBuilding.property_manager || 'Not available'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>

              {/* Additional Notes */}
              {selectedBuilding.rental_notes && (
                <>
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom color="primary">
                      Additional Rental Information
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="Rental Notes"
                      value={selectedBuilding.rental_notes}
                      fullWidth
                      multiline
                      rows={3}
                      InputProps={{ readOnly: true }}
                    />
                  </Grid>
                </>
              )}

              {/* System Information */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom color="primary">
                  System Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  label="Approved"
                  value={selectedBuilding.approved ? 'Yes' : 'No'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  label="Email Sent"
                  value={selectedBuilding.email_sent ? 'Yes' : 'No'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  label="Reply Received"
                  value={selectedBuilding.reply_received ? 'Yes' : 'No'}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  label="Contact Email"
                  value={selectedBuilding.contact_email || 'Not available'}
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