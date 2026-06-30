import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

// Use your PC's local network IP for physical devices, and emulator loopback for Android emulators.
// Replace the LOCAL_DEVICE_IP value with your machine's IP if needed.
const LOCAL_DEVICE_IP = '10.168.226.132';
const getBaseUrl = () => {
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000/api/v1'; // Android emulator loopback
  }
  if (Platform.OS === 'web') {
    return 'http://localhost:8000/api/v1';
  }
  const url = `http://${LOCAL_DEVICE_IP}:8000/api/v1`;
  console.log('🔗 API Base URL:', url, 'Platform:', Platform.OS);
  return url;
};

const apiClient = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Log all requests and responses for debugging
apiClient.interceptors.request.use(async (config) => {
  try {
    const token = await SecureStore.getItemAsync('userToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch (error) {
    console.error('SecureStore token fetch failed', error);
  }
  console.log('📤 Request:', config.method?.toUpperCase(), config.url);
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    console.log('📥 Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('❌ Network Error:', {
      message: error.message,
      code: error.code,
      url: error.config?.url,
      timeout: error.config?.timeout,
    });
    return Promise.reject(error);
  }
);

export default apiClient;