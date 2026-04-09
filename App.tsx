import { View, Button, StyleSheet, Text } from 'react-native';
import { useRef, useState, useEffect } from 'react';
import { CameraView, useCameraPermissions, CameraView as CameraViewType } from 'expo-camera';
import { Video, ResizeMode } from 'expo-av';

export default function App() {
  const cameraRef = useRef<CameraViewType>(null);
  const [video, setVideo] = useState<string | null>(null);
  const [permission, requestPermission] = useCameraPermissions();

  useEffect(() => {
    requestPermission();
  }, []);

  const startRecording = async () => {
    if (!cameraRef.current) {
      console.log("Camera not ready");
      return;
    }

    try {
      const videoData = await cameraRef.current.recordAsync();
      if (videoData?.uri) {
        setVideo(videoData.uri);
        console.log("Recorded:", videoData.uri);
      }
    } catch (e) {
      console.log("Recording error:", e);
    }
  };

  const stopRecording = () => {
    if (cameraRef.current) {
      cameraRef.current.stopRecording();
    }
  };

  if (!permission?.granted) {
    return <Text>No camera permission</Text>;
  }

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={styles.camera}
        mode="video"
      />

      <Button title="Start Recording 🎥" onPress={startRecording} />
      <Button title="Stop Recording ⏹" onPress={stopRecording} />

      {video && (
        <Video
          source={{ uri: video }}
          style={styles.video}
          useNativeControls
          resizeMode={ResizeMode.CONTAIN}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  camera: { flex: 1 },
  video: {
    width: 300,
    height: 200,
    alignSelf: "center"
  }
});