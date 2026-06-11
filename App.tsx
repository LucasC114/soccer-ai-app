import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [coachingTip, setCoachingTip] = useState('');
  const [angleResult, setAngleResult] = useState<number | null>(null);

  const pickAndAnalyzeVideo = async () => {
    // 1. Ask the user for permission to access their photos/videos
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (permissionResult.granted === false) {
      Alert.alert("Permission Required", "We need access to your gallery to analyze videos!");
      return;
    }

    // 2. Open the gallery to select a video
    const pickerResult = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      allowsEditing: true,
      quality: 1,
    });

    // If the user backs out without picking a video, do nothing
    if (pickerResult.canceled) return;

    // 3. Prepare the video file data to send to Python
    const videoUri = pickerResult.assets[0].uri;
    const formData = new FormData();
    
    // @ts-ignore
    formData.append('video', {
      uri: videoUri,
      type: 'video/mp4',
      name: 'soccer_kick.mp4',
    });

    try {
      setLoading(true);
      setCoachingTip('AI is analyzing your leg mechanics...');
      setAngleResult(null);
      
      // 4. Send the video to your Flask backend
      // NOTE: "10.0.2.2" is a special shortcut for computer emulators.
      // If you use a physical iPhone/Android, change this to your computer's local IP address!
      const response = await fetch('https://cruel-steaks-fry.loca.lt', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const data = await response.json();
      
      // 5. Update the screen with the AI's response data
      if (data.error) {
        setCoachingTip(`Error: ${data.error}`);
      } else {
        setAngleResult(data.max_knee_bend_angle);
        setCoachingTip(data.coaching_tip);
      }

    } catch (error) {
      setCoachingTip('Could not connect to the AI server.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>⚽ AI Soccer Analyzer</Text>
      <Text style={styles.subtitle}>Upload a clip of your kick to get instant form feedback</Text>

      <TouchableOpacity style={styles.button} onPress={pickAndAnalyzeVideo} disabled={loading}>
        <Text style={styles.buttonText}>{loading ? 'Analyzing...' : 'Select Kick Video'}</Text>
      </TouchableOpacity>

      {loading && <ActivityIndicator size="large" color="#00ff00" style={{ marginTop: 30 }} />}

      {coachingTip ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>AI Coach Feedback:</Text>
          {angleResult !== null && (
            <Text style={styles.angleText}>Max Knee Bend: {angleResult}°</Text>
          )}
          <Text style={styles.feedbackText}>{coachingTip}</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212', alignItems: 'center', justifyContent: 'center', padding: 24 },
  title: { fontSize: 28, color: '#fff', fontWeight: 'bold', marginBottom: 8 },
  subtitle: { fontSize: 14, color: '#888', textAlign: 'center', marginBottom: 40 },
  button: { backgroundColor: '#1DB954', paddingVertical: 16, paddingHorizontal: 32, borderRadius: 30, elevation: 3 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  card: { backgroundColor: '#1E1E1E', width: '100%', borderRadius: 12, padding: 20, marginTop: 40, borderLeftWidth: 4, borderLeftColor: '#1DB954' },
  cardTitle: { color: '#888', fontSize: 12, fontWeight: 'bold', textTransform: 'uppercase', marginBottom: 8 },
  angleText: { color: '#fff', fontSize: 22, fontWeight: 'bold', marginBottom: 6 },
  feedbackText: { color: '#ddd', fontSize: 16, lineHeight: 22 },
});