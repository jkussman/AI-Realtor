import React, { useState, useCallback, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Button, 
  Alert, 
  CircularProgress,
  Snackbar
} from '@mui/material';
import { Send as SendIcon, Clear as ClearIcon } from '@mui/icons-material';
import { MapContainer, TileLayer, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';

// Import API functions
import { processBoundingBoxes } from '../utils/api';

// Fix Leaflet default markers
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// NYC center coordinates
const NYC_CENTER: [number, number] = [40.7831, -73.9712];
const DEFAULT_ZOOM = 12;

interface BoundingBox {
  north: number;
  south: number;
  east: number;
  west: number;
}

const MapPage: React.FC = () => {
  const [drawnItems, setDrawnItems] = useState<L.Layer[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
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

  const onCreated = useCallback((e: any) => {
    const { layer } = e;
    setDrawnItems(prev => [...prev, layer]);
    
    // Show coordinates info
    if (layer instanceof L.Rectangle) {
      const bounds = layer.getBounds();
      showNotification(
        `Rectangle drawn! Bounds: ${bounds.getNorth().toFixed(4)}, ${bounds.getSouth().toFixed(4)}, ${bounds.getEast().toFixed(4)}, ${bounds.getWest().toFixed(4)}`,
        'info'
      );
    }
  }, []);

  const onDeleted = useCallback((e: any) => {
    const layers = e.layers;
    layers.eachLayer((layer: L.Layer) => {
      setDrawnItems(prev => prev.filter(item => item !== layer));
    });
  }, []);

  const onEdited = useCallback((e: any) => {
    // Handle edited layers if needed
    showNotification('Bounding box updated', 'info');
  }, []);

  const convertLayersToBoundingBoxes = (): BoundingBox[] => {
    return drawnItems
      .filter(layer => layer instanceof L.Rectangle)
      .map(layer => {
        const bounds = (layer as L.Rectangle).getBounds();
        return {
          north: bounds.getNorth(),
          south: bounds.getSouth(),
          east: bounds.getEast(),
          west: bounds.getWest()
        };
      });
  };

  const handleSubmitBoundingBoxes = async () => {
    if (drawnItems.length === 0) {
      showNotification('Please draw at least one bounding box on the map', 'error');
      return;
    }

    setIsProcessing(true);
    
    try {
      const boundingBoxes = convertLayersToBoundingBoxes();
      
      showNotification(
        `Submitting ${boundingBoxes.length} bounding box${boundingBoxes.length > 1 ? 'es' : ''} for processing...`,
        'info'
      );

      const response = await processBoundingBoxes(boundingBoxes);
      
      if (response.success) {
        showNotification(
          `Successfully submitted ${boundingBoxes.length} bounding boxes for processing. Check the Buildings page for results.`,
          'success'
        );
      } else {
        showNotification(`Error: ${response.error}`, 'error');
      }
    } catch (error) {
      showNotification(`Failed to submit bounding boxes: ${error}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClearAll = () => {
    setDrawnItems([]);
    showNotification('All bounding boxes cleared', 'info');
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, m: 2, mb: 1 }}>
        <Typography variant="h5" gutterBottom>
          NYC Property Discovery Map
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Draw rectangular bounding boxes on the map to identify areas for building discovery.
          The AI will find residential apartment buildings within your selected areas.
        </Typography>

        {/* Controls */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={isProcessing ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            onClick={handleSubmitBoundingBoxes}
            disabled={isProcessing || drawnItems.length === 0}
          >
            {isProcessing ? 'Processing...' : `Submit ${drawnItems.length} Area${drawnItems.length !== 1 ? 's' : ''}`}
          </Button>
          
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<ClearIcon />}
            onClick={handleClearAll}
            disabled={drawnItems.length === 0}
          >
            Clear All
          </Button>

          <Typography variant="body2" color="text.secondary">
            {drawnItems.length} bounding box{drawnItems.length !== 1 ? 'es' : ''} drawn
          </Typography>
        </Box>

        {drawnItems.length > 0 && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Tip:</strong> You can edit or delete bounding boxes using the controls on the map.
              Each box will be searched for residential apartment buildings.
            </Typography>
          </Alert>
        )}
      </Paper>

      {/* Map */}
      <Box sx={{ flex: 1, m: 2, mt: 1 }}>
        <Paper elevation={2} sx={{ height: '100%', overflow: 'hidden' }}>
          <MapContainer
            center={NYC_CENTER}
            zoom={DEFAULT_ZOOM}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            <FeatureGroup>
              <EditControl
                position="topright"
                onCreated={onCreated}
                onDeleted={onDeleted}
                onEdited={onEdited}
                draw={{
                  rectangle: {
                    shapeOptions: {
                      color: '#1976d2',
                      fillColor: '#1976d2',
                      fillOpacity: 0.2,
                      weight: 2
                    }
                  },
                  polygon: false,
                  circle: false,
                  circlemarker: false,
                  marker: false,
                  polyline: false
                }}
                edit={{
                  edit: true,
                  remove: true
                }}
              />
            </FeatureGroup>
          </MapContainer>
        </Paper>
      </Box>

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

export default MapPage; 