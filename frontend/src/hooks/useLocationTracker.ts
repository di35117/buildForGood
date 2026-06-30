import { useEffect } from 'react';
import * as Location from 'expo-location';
import apiClient from '../api/client';

export const useLocationTracker = () => {
  useEffect(() => {
    (async () => {
      // 1. Request permissions
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') return;

      // 2. Watch location and push to backend
      await Location.watchPositionAsync(
        { accuracy: Location.Accuracy.High, distanceInterval: 10 },
        async (location) => {
          try {
            // Sends GPS data to your backend telemetry service
            await apiClient.post('/sensors/telemetry', {
              latitude: location.coords.latitude,
              longitude: location.coords.longitude,
              timestamp: new Date().toISOString(),
            });
          } catch (error) {
            console.error('Telemetry push failed', error);
          }
        }
      );
    })();
  }, []);
};