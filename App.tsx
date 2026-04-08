import { View, Button, StyleSheet } from 'react-native';
import { useState } from 'react';
import * as ImagePicker from 'expo-image-picker';
import { Video, ResizeMode } from 'expo-av';

export default function App() {
  const [video, setVideo] = useState<string | null>(null);

  // 📂 Pick video from gallery
  const pickVideo = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      allowsEditing: false,
    });

    if (!result.canceled) {
      setVideo(result.assets[0].uri);
    }
  };

  // 🎥 Record video
  const recordVideo = async () => {
    let result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
    });

    if (!result.canceled) {
      setVideo(result.assets[0].uri);
    }
  };

  return (
    <View style={styles.container}>
      <Button title="Record Video 🎥" onPress={recordVideo} />
      <Button title="Upload Video 📂" onPress={pickVideo} />

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
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  video: {
    width: 300,
    height: 200,
    marginTop: 20,
  },
});