import React, { useState } from "react";
import { VideoView, useVideoPlayer } from "expo-video";import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import * as ImagePicker from "expo-image-picker";

// ============================================================
// CHANGE THIS to your fresh localtunnel URL every time you run:
//   npx localtunnel --port 5000
// It will print a URL like: https://xxxxxx.loca.lt
// ============================================================
const SERVER_URL = "https://pink-paths-march.loca.lt";

export default function App() {
  const [fps, setFps] = useState(30);
  const [totalFrames, setTotalFrames] = useState(0);
  const [loading, setLoading] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [coachingTip, setCoachingTip] = useState("");
  const [loadupData, setLoadupData] = useState<any>(null);
  const [contactData, setContactData] = useState<any>(null);
  const [followthroughData, setFollowthroughData] = useState<any>(null);
  const [shotType, setShotType] = useState<"power" | "finesse" | null>(null);
  const [kickingLeg, setKickingLeg] = useState<"left" | "right" | null>(null);
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [contactTime, setContactTime] = useState<number | null>(null);
  const player = useVideoPlayer(videoUri ?? "", (player) => {
    player.pause();
  });

  const analyzeVideo = async () => {
    if (!videoUri || contactTime === null) {
      Alert.alert("Select a contact frame first!");
      return;
    }

    const formData = new FormData();

    // @ts-ignore
    formData.append("video", {
      uri: videoUri,
      type: "video/mp4",
      name: "soccer_kick.mp4",
    });

    formData.append("shotType", shotType!);
    formData.append("kickingLeg", kickingLeg!);
    formData.append("contactTime", String(contactTime));

    try {
      setLoading(true);
      setCoachingTip("AI is analyzing your leg mechanics...");
      
      const response = await fetch(`${SERVER_URL}/analyze`, {
        method: "POST",
        body: formData,
        headers: {
          "Content-Type": "multipart/form-data",
          "Bypass-Tunnel-Reminder": "true",
        },
      });

      console.log("Status:", response.status);
      const data = await response.json();
      console.log("Video Info:", data);
      
      setFps(data.fps);
      setTotalFrames(data.totalFrames);

      if (data.error) {
        setCoachingTip(`Error: ${data.error}`);
      } else {
        setLoadupData(data.loadup);
        setContactData(data.contact);
        setFollowthroughData(data.followthrough);

        setCoachingTip(data.coaching_tip);
      }

    } 
    catch (error) {
      setCoachingTip(
        "Could not connect to the AI server. Is the Python server running?"
      );
      console.error(error);

    } finally {
      setLoading(false);
    }
  };

  const pickAndAnalyzeVideo = async () => {     //Now only picks video
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

    const selectedVideoUri = pickerResult.assets[0].uri;
    setVideoUri(selectedVideoUri);
    player.replace(selectedVideoUri); 
    const formData = new FormData();

    // @ts-ignore
    formData.append("video", {
      uri: selectedVideoUri,
      type: "video/mp4",
      name: "soccer_kick.mp4",
    });

    const response = await fetch(`${SERVER_URL}/video-info`, {
      method: "POST",
      body: formData,
      headers: {
        "Content-Type": "multipart/form-data",
        "Bypass-Tunnel-Reminder": "true",
      },
    });

    const data = await response.json();

    setFps(data.fps);
    setTotalFrames(data.totalFrames);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>⚽ AI Soccer Analyzer</Text>

      <Text style={styles.subtitle}>
        Upload a clip of your kick to get instant form feedback
      </Text>

      {shotType === null ? (
        <>
          <TouchableOpacity
            style={styles.button}
            onPress={() => {
            setShotType("power");
          }}
          >
            <Text style={styles.buttonText}>⚡ Power Shot</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, { marginTop: 20 }]}
            onPress={() => setShotType("finesse")}
          >
            <Text style={styles.buttonText}>🎯 Finesse Shot</Text>
          </TouchableOpacity>
        </>
      ) : kickingLeg === null ? (
        <>
          <Text
            style={{
              color: "white",
              fontSize: 22,
              marginBottom: 25,
            }}
          >
            Which foot are you kicking with?
          </Text>

          <TouchableOpacity
            style={styles.button}
            onPress={() => setKickingLeg("right")}
          >
            <Text style={styles.buttonText}>
              ➡️ Right Foot
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, { marginTop: 20 }]}
            onPress={() => setKickingLeg("left")}
          >
            <Text style={styles.buttonText}>
              ⬅️ Left Foot
            </Text>
          </TouchableOpacity>
        </>
      ) : (
        <>
          <TouchableOpacity
            style={styles.button}
            onPress={pickAndAnalyzeVideo}
            disabled={loading}
          >
            <Text style={styles.buttonText}>
              {loading ? "Analyzing..." : "Select Kick Video"}
            </Text>
          </TouchableOpacity>

          {videoUri && (
            <>
              <VideoView
                player={player}
                style={{
                  width: 340,
                  height: 200,
                  marginTop: 25,
                  borderRadius: 12,
                }}
                allowsFullscreen={false}
                allowsPictureInPicture={false}
                nativeControls
              />

              <View
                style={{
                  flexDirection: "row",
                  justifyContent: "space-between",
                  width: 340,
                  marginTop: 20,
                }}
              >
                <TouchableOpacity
                  style={styles.button}
                  onPress={() => {
                    const newFrame = Math.max(0, currentFrame - 1);
                    setCurrentFrame(newFrame);
                    player.currentTime = newFrame / fps;
                  }}
                >
                  <Text style={styles.buttonText}>⏪ Previous</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.button}
                  onPress={() => {
                    const newFrame = Math.min(totalFrames - 1, currentFrame + 1);
                    setCurrentFrame(newFrame);
                    player.currentTime = newFrame / fps;
                  }}
                >
                  <Text style={styles.buttonText}>Next ⏩</Text>
                </TouchableOpacity>
              </View>

              <Text
                style={{
                  color: "white",
                  marginTop: 15,
                  fontSize: 18,
                }}
              >
                Frame: {currentFrame} / {totalFrames}
              </Text>

              <TouchableOpacity
                style={[styles.button, { marginTop: 10 }]}
                onPress={() => {
                  setContactTime(currentFrame / fps);
                }}
              >
                <Text style={styles.buttonText}>
                  📍 Set Contact Point
                </Text>
              </TouchableOpacity>

              {contactTime !== null && (
                <Text style={{color:"lime", marginTop:10}}>
                  Contact Time: {contactTime.toFixed(2)}s
                </Text>
              )}

              <TouchableOpacity
                style={[styles.button, { marginTop: 20 }]}
                onPress={analyzeVideo}
              >
                <Text style={styles.buttonText}>
                  🔍 Analyze Video
                </Text>
              </TouchableOpacity>
            </>
          )}
        </>
      )}

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

          {loadupData && (
            <>
              <Text style={styles.angleText}>
                Load-up:
              </Text>

              <Text style={styles.angleText}>
                Knee: {loadupData.knee_angle}°
              </Text>

              <Text style={styles.angleText}>
                Hip: {loadupData.hip_angle}°
              </Text>

              <Text style={styles.angleText}>
                Ankle: {loadupData.ankle_angle}°
              </Text>

              <Text style={styles.angleText}>
                Trunk Lean: {loadupData.trunk_lean}°
              </Text>


              <Text style={styles.angleText}>
                Contact:
              </Text>

              <Text style={styles.angleText}>
                Knee: {contactData.knee_angle}°
              </Text>

              <Text style={styles.angleText}>
                Hip: {contactData.hip_angle}°
              </Text>

              <Text style={styles.angleText}>
                Ankle: {contactData.ankle_angle}°
              </Text>

              <Text style={styles.angleText}>
                Trunk Lean: {contactData.trunk_lean}°
              </Text>

              <Text style={styles.angleText}>
                Follow-through:
              </Text>

              <Text style={styles.angleText}>
                Knee: {followthroughData.knee_angle}°
              </Text>

              <Text style={styles.angleText}>
                Hip: {followthroughData.hip_angle}°
              </Text>

              <Text style={styles.angleText}>
                Ankle: {followthroughData.ankle_angle}°
              </Text>

              <Text style={styles.angleText}>
                Trunk Lean: {followthroughData.trunk_lean}°
              </Text>
            </>
          )}

          <Text style={styles.feedbackText}>
            {coachingTip}
          </Text>
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
