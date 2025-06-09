import React, { useState, useCallback, useEffect } from 'react';
import { MapContainer, TileLayer, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { processBoundingBoxes, getBuildings, Building } from '../utils/api';

// Fix Leaflet default markers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [initialCount, setInitialCount] = useState(0);
  const [shouldPoll, setShouldPoll] = useState(false);

  // Polling effect
  useEffect(() => {
    if (!shouldPoll) return;

    let attempts = 0;
    const maxAttempts = 30;
    const pollInterval = 1000;

    const pollingInterval = setInterval(async () => {
      const buildingsResponse = await getBuildings();
      
      if (buildingsResponse.success && buildingsResponse.data) {
        const currentCount = buildingsResponse.data.length;
        const newBuildingsCount = currentCount - initialCount;
        
        if (newBuildingsCount > 0) {
          setProcessingStatus(
            `Building discovery completed! Found ${newBuildingsCount} new buildings in selected areas. ` +
            `Total buildings in database: ${currentCount}`
          );
          setIsProcessing(false);
          setShouldPoll(false);
          return;
        }
      }

      attempts++;
      
      if (attempts >= maxAttempts) {
        setProcessingStatus('Building discovery timed out. No new buildings were found. Please try a different area.');
        setIsProcessing(false);
        setShouldPoll(false);
      }
    }, pollInterval);

    return () => clearInterval(pollingInterval);
  }, [shouldPoll, initialCount]);

  const handleCreated = useCallback((e: any) => {
    const { layer } = e;
    const bounds = layer.getBounds();
    
    const bbox: BoundingBox = {
      north: bounds.getNorth(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      west: bounds.getWest()
    };
    
    setBoundingBoxes(prev => [...prev, bbox]);
  }, []);

  const handleProcessBoundingBoxes = async () => {
    if (!boundingBoxes.length) {
      setProcessingStatus('Please draw at least one bounding box on the map.');
      return;
    }

    setIsProcessing(true);
    try {
      // Get initial building count
      const initialBuildingsResponse = await getBuildings();
      const count = initialBuildingsResponse.success && initialBuildingsResponse.data ? initialBuildingsResponse.data.length : 0;
      setInitialCount(count);

      const response = await processBoundingBoxes(boundingBoxes);

      if (response.success) {
        setProcessingStatus('Processing buildings...');
        setShouldPoll(true);
      } else {
        setProcessingStatus(`Error: ${response.error}`);
        setIsProcessing(false);
      }
    } catch (error) {
      setProcessingStatus(`Error: ${error}`);
      setIsProcessing(false);
    }
  };

  const clearBoundingBoxes = () => {
    setBoundingBoxes([]);
    setProcessingStatus('');
  };

  return (
    <Box sx={{ height: '100%', display: 'flex' }}>
      {/* Map Container */}
      <Box sx={{ flex: 1, position: 'relative' }}>
        <MapContainer
          center={[40.7829, -73.9654]} // NYC coordinates
          zoom={13}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          <FeatureGroup>
            <EditControl
              position="topright"
              onCreated={handleCreated}
              draw={{
                rectangle: true,
                polygon: false,
                circle: false,
                circlemarker: false,
                marker: false,
                polyline: false
              }}
              edit={{
                edit: false,
                remove: true
              }}
            />
          </FeatureGroup>
        </MapContainer>
      </Box>

      {/* Sidebar */}
      <Paper 
        elevation={3} 
        sx={{ 
          width: 350, 
          p: 3, 
          display: 'flex', 
          flexDirection: 'column',
          maxHeight: '100%',
          overflow: 'auto'
        }}
      >
        <Typography variant="h5" gutterBottom>
          Building Discovery
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Draw rectangles on the map to define areas for building discovery. 
          Focus on residential neighborhoods in NYC.
        </Typography>

        {/* Bounding Boxes List */}
        <Typography variant="h6" gutterBottom>
          Selected Areas ({boundingBoxes.length})
        </Typography>
        
        <List sx={{ mb: 2, maxHeight: 200, overflow: 'auto' }}>
          {boundingBoxes.map((bbox, index) => (
            <ListItem key={index} dense>
              <ListItemText
                primary={`Area ${index + 1}`}
                secondary={`${bbox.north.toFixed(4)}, ${bbox.west.toFixed(4)} to ${bbox.south.toFixed(4)}, ${bbox.east.toFixed(4)}`}
              />
            </ListItem>
          ))}
        </List>

        {boundingBoxes.length === 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Draw rectangles on the map to select areas for building discovery.
          </Alert>
        )}

        {/* Action Buttons */}
        <Box sx={{ mt: 'auto', pt: 2 }}>
          <Button
            variant="contained"
            fullWidth
            startIcon={isProcessing ? <CircularProgress size={20} /> : <SearchIcon />}
            onClick={handleProcessBoundingBoxes}
            disabled={isProcessing || boundingBoxes.length === 0}
            sx={{ mb: 1 }}
          >
            {isProcessing ? 'Processing...' : 'Start Building Discovery'}
          </Button>
          
          <Button
            variant="outlined"
            fullWidth
            onClick={clearBoundingBoxes}
            disabled={isProcessing}
          >
            Clear All Areas
          </Button>
        </Box>

        {/* Status */}
        {processingStatus && (
          <Alert 
            severity={isProcessing ? "info" : "success"} 
            sx={{ mt: 2 }}
          >
            {processingStatus}
          </Alert>
        )}
      </Paper>
    </Box>
  );
};

export default MapPage; 