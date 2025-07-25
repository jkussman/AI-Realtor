import axios from 'axios';

// API base URL - this will use the proxy in package.json for local development
const API_BASE_URL = '/api';

// Types
export interface BoundingBox {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface Building {
  id: number;
  name?: string;
  address: string;
  standardized_address?: string;
  latitude?: string;
  longitude?: string;
  building_type: string;
  bounding_box?: Record<string, any>;
  approved: boolean;
  contact_email?: string;
  contact_name?: string;
  contact_phone?: string;
  website?: string;
  email_sent: boolean;
  reply_received: boolean;
  created_at: string;
  updated_at: string;
  
  // Contact confidence information
  contact_email_confidence?: number;
  contact_source?: string;
  contact_source_url?: string;
  contact_verified?: boolean;
  contact_last_verified?: string;
  verification_notes?: string;
  verification_flags?: string[];
  
  // Basic building info
  property_manager?: string;
  number_of_units?: number;
  year_built?: number;
  square_footage?: number;
  
  // Detailed rental information
  is_coop: boolean;
  is_mixed_use: boolean;
  total_apartments?: number;
  two_bedroom_apartments?: number;
  recent_2br_rent?: number;
  rent_range_2br?: string;
  has_laundry: boolean;
  laundry_type?: string;
  amenities?: string[];
  pet_policy?: string;
  building_style?: string;
  management_company?: string;
  contact_info?: Record<string, any>;
  recent_availability: boolean;
  rental_notes?: string;
  neighborhood?: string;
  stories?: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Configure axios defaults
axios.defaults.timeout = 30000; // 30 seconds
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Request interceptor for logging
axios.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    if (error.response) {
      // Server responded with error status
      console.error('Error Status:', error.response.status);
      console.error('Error Data:', error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('No response received:', error.request);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * Process bounding boxes to find buildings
 */
export const processBoundingBoxes = async (boundingBoxes: BoundingBox[]): Promise<ApiResponse> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/process-bbox`, {
      bounding_boxes: boundingBoxes
    });
    
    return {
      success: true,
      data: response.data,
      message: response.data.message
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to process bounding boxes'
    };
  }
};

/**
 * Get all buildings
 */
export const getBuildings = async (): Promise<ApiResponse<Building[]>> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/buildings`);
    
    return {
      success: true,
      data: response.data
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to fetch buildings'
    };
  }
};

/**
 * Get a specific building by ID
 */
export const getBuilding = async (buildingId: number): Promise<ApiResponse> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/buildings/${buildingId}`);
    
    return {
      success: true,
      data: response.data
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to fetch building'
    };
  }
};

/**
 * Approve a building and trigger outreach
 */
export const approveBuilding = async (buildingId: number): Promise<ApiResponse> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/approve-building`, {
      building_id: buildingId
    });
    
    return {
      success: true,
      data: response.data,
      message: response.data.message
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to approve building'
    };
  }
};

/**
 * Delete a specific building by ID
 */
export const deleteBuilding = async (buildingId: number): Promise<ApiResponse> => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/buildings/${buildingId}`);
    
    return {
      success: true,
      data: response.data,
      message: response.data.message
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to delete building'
    };
  }
};

/**
 * Delete all buildings
 */
export const deleteAllBuildings = async (): Promise<ApiResponse> => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/buildings`);
    
    return {
      success: true,
      data: response.data,
      message: response.data.message
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to delete all buildings'
    };
  }
};

/**
 * Check email status
 */
export const checkEmailStatus = async (): Promise<ApiResponse> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/email-status`);
    
    return {
      success: true,
      data: response.data,
      message: response.data.message
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to check email status'
    };
  }
};

/**
 * Test API connection
 */
export const testConnection = async (): Promise<ApiResponse> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/`);
    
    return {
      success: true,
      data: response.data,
      message: 'API connection successful'
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to connect to API'
    };
  }
};

/**
 * Utility function to handle API errors consistently
 */
export const handleApiError = (error: any): string => {
  if (error.response) {
    // Server responded with error status
    return error.response.data?.detail || error.response.data?.message || `Error ${error.response.status}`;
  } else if (error.request) {
    // Request made but no response
    return 'No response from server. Please check your connection.';
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred';
  }
};

/**
 * Format date strings from API responses
 */
export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  } catch {
    return dateString;
  }
};

export default {
  processBoundingBoxes,
  getBuildings,
  getBuilding,
  approveBuilding,
  deleteBuilding,
  deleteAllBuildings,
  checkEmailStatus,
  testConnection,
  handleApiError,
  formatDate
}; 