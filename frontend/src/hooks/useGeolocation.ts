'use client';

import { useState, useEffect, useCallback } from 'react';

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface GeolocationState {
  coords: Coordinates | null;
  loading: boolean;
  error: string | null;
  permissionGranted: boolean;
}

// Fallback to New Delhi coordinates if GPS permission denied or unavailable
const DEFAULT_COORDS: Coordinates = {
  latitude: 28.6139,
  longitude: 77.2090,
};

export function useGeolocation() {
  const [state, setState] = useState<GeolocationState>({
    coords: null,
    loading: true,
    error: null,
    permissionGranted: false,
  });

  const requestLocation = useCallback(() => {
    if (typeof window === 'undefined' || !navigator.geolocation) {
      setState({
        coords: DEFAULT_COORDS,
        loading: false,
        error: 'Geolocation is not supported by your browser',
        permissionGranted: false,
      });
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setState({
          coords: {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          },
          loading: false,
          error: null,
          permissionGranted: true,
        });
      },
      (error) => {
        console.warn('Geolocation error:', error.message);
        setState({
          coords: DEFAULT_COORDS,
          loading: false,
          error: error.message,
          permissionGranted: false,
        });
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    );
  }, []);

  useEffect(() => {
    requestLocation();
  }, [requestLocation]);

  const setManualCoords = (latitude: number, longitude: number) => {
    setState({
      coords: { latitude, longitude },
      loading: false,
      error: null,
      permissionGranted: true,
    });
  };

  return {
    ...state,
    requestLocation,
    setManualCoords,
  };
}
