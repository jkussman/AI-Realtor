import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Building, getBuildings } from '../utils/api';

interface BuildingsContextType {
  buildings: Building[];
  loading: boolean;
  error: string | null;
  fetchBuildings: () => Promise<void>;
  startPolling: () => void;
  stopPolling: () => void;
}

const BuildingsContext = createContext<BuildingsContextType | undefined>(undefined);

export const BuildingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shouldPoll, setShouldPoll] = useState(false);
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  const fetchBuildings = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getBuildings();
      if (response.success && response.data) {
        setBuildings(response.data);
        setError(null);
      } else {
        setError(response.error || 'Failed to fetch buildings');
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch buildings');
    } finally {
      setLoading(false);
    }
  }, []);

  const startPolling = useCallback(() => {
    setShouldPoll(true);
  }, []);

  const stopPolling = useCallback(() => {
    setShouldPoll(false);
  }, []);

  useEffect(() => {
    // Initial fetch
    fetchBuildings();
  }, [fetchBuildings]);

  useEffect(() => {
    if (!shouldPoll) {
      if (pollInterval) {
        clearInterval(pollInterval);
        setPollInterval(null);
      }
      return;
    }

    // Start polling every 10 seconds
    const interval = setInterval(() => {
      fetchBuildings();
    }, 10000);

    setPollInterval(interval);

    return () => {
      clearInterval(interval);
      setPollInterval(null);
    };
  }, [shouldPoll, fetchBuildings]);

  const value = {
    buildings,
    loading,
    error,
    fetchBuildings,
    startPolling,
    stopPolling,
  };

  return (
    <BuildingsContext.Provider value={value}>
      {children}
    </BuildingsContext.Provider>
  );
};

export const useBuildings = () => {
  const context = useContext(BuildingsContext);
  if (context === undefined) {
    throw new Error('useBuildings must be used within a BuildingsProvider');
  }
  return context;
}; 