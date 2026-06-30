import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, Text, StyleSheet, Alert } from 'react-native';
import apiClient from '../api/client';

export default function IncidentScreen({ navigation }: any) {
  const [description, setDescription] = useState('');

  const submitReport = async () => {
    try {
      // Connects to your backend incident logging system
      await apiClient.post('/incident/log', {
        description,
        timestamp: new Date().toISOString(),
      });
      Alert.alert('Report Submitted', 'Emergency services have been notified.');
      navigation.goBack();
    } catch (error) {
      Alert.alert('Submission Failed', 'Could not upload report to the bridge.');
    }
  };

  return (
    <View style={styles.container}>
      <TextInput 
        style={styles.input} 
        placeholder="Describe the incident..." 
        value={description} 
        onChangeText={setDescription}
        multiline
      />
      <TouchableOpacity style={styles.submitButton} onPress={submitReport}>
        <Text style={styles.buttonText}>Submit Incident Report</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  input: { flex: 1, borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 10, marginBottom: 20 },
  submitButton: { backgroundColor: '#dc2626', padding: 15, borderRadius: 8, alignItems: 'center' },
  buttonText: { color: '#fff', fontWeight: 'bold' }
});