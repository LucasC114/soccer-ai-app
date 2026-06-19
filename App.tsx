import React, { useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Platform,
} from "react-native";
import * as ImagePicker from "expo-image-picker";

// ============================================================
// CHANGE THIS to your fresh localtunnel URL every time you run:
//   npx localtunnel --port 5000
// It will print a URL like: https://xxxxxx.loca.lt
// ============================================================
const SERVER_URL = "https://major-beds-hope.loca.lt";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [coachingTip, setCoachingTip] = useState("");
  const [angleResult, setAngleResult] = useState<number | null>(null);

  const pickAndAnalyzeVideo = async () => {
    const permissionResult =
      await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (permissionResult.granted === false) {
      Alert.alert(
        "Permission Required",
        "We need access to your gallery to analyze videos!"
      );
      return;
    }

    const pickerResult = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      allowsEditing: true,
      quality: 1,
    });

    if (pickerResult.canceled) return;

    const videoUri = pickerResult.assets[0].uri;
    const formData = new FormData();

    // @ts-ignore
    formData.append("video", {
      uri: videoUri,
      type: "video/mp4",
      name: "soccer_kick.mp4",
    });

    try {
      setLoading(true);
      setCoachingTip("AI is analyzing your leg mechanics...");
      setAngleResult(null);

      const response = await fetch(`${SERVER_URL}/analyze`, {
        method: "POST",
        body: formData,
        headers: {
          "Content-Type": "multipart/form-data",
          // localtunnel requires this header to bypass the "friendly" page
          "Bypass-Tunnel-Reminder": "true",
        },
      });

      const data = await response.json();

      if (data.error) {
        setCoachingTip(`Error: ${data.error}`);
      } else {
        setAngleResult(data.max_knee_bend_angle);
        setCoachingTip(data.coaching_tip);
      }
    } catch (error) {
      setCoachingTip(
        "Could not connect to the AI server. Is the Python server running?"
      );
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>⚽ AI Soccer Analyzer</Text>
      <Text style={styles.subtitle}>
        Upload a clip of your kick to get instant form feedback
      </Text>

      <TouchableOpacity
        style={styles.button}
        onPress={pickAndAnalyzeVideo}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? "Analyzing..." : "Select Kick Video"}
        </Text>
      </TouchableOpacity>

      {loading && (
        <ActivityIndicator
          size="large"
          color="#00ff00"
          style={{ marginTop: 30 }}
        />
      )}

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
  container: {
    flex: 1,
    backgroundColor: "#121212",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  title: {
    fontSize: 28,
    color: "#fff",
    fontWeight: "bold",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: "#888",
    textAlign: "center",
    marginBottom: 40,
  },
  button: {
    backgroundColor: "#1DB954",
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 30,
    elevation: 3,
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "bold" },
  card: {
    backgroundColor: "#1E1E1E",
    width: "100%",
    borderRadius: 12,
    padding: 20,
    marginTop: 40,
    borderLeftWidth: 4,
    borderLeftColor: "#1DB954",
  },
  cardTitle: {
    color: "#888",
    fontSize: 12,
    fontWeight: "bold",
    textTransform: "uppercase",
    marginBottom: 8,
  },
  angleText: { color: "#fff", fontSize: 22, fontWeight: "bold", marginBottom: 6 },
  feedbackText: { color: "#ddd", fontSize: 16, lineHeight: 22 },
});
