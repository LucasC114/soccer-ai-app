import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, request, jsonify
import os
import urllib.request

app = Flask(__name__)

# Download MediaPipe Pose Landmarker model if not present
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
MODEL_PATH = "./pose_landmarker_lite.task"

if not os.path.exists(MODEL_PATH):
    print("Downloading pose model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Model downloaded.")

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.VIDEO
)


def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return int(angle)


@app.route("/analyze", methods=["POST"])
def analyze_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    video_path = "./temp_video.mp4"
    video_file.save(video_path)

    cap = cv2.VideoCapture(video_path)
    knee_angles = []
    frames_processed = 0

    with PoseLandmarker.create_from_options(options) as landmarker:
        while True:
            success, frame = cap.read()
            if not success:
                break

            frames_processed += 1

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))

            detection_result = landmarker.detect_for_video(mp_image, timestamp_ms)

            if detection_result.pose_landmarks:
                landmarks = detection_result.pose_landmarks[0]

                hip = [landmarks[24].x, landmarks[24].y]
                knee = [landmarks[26].x, landmarks[26].y]
                ankle = [landmarks[28].x, landmarks[28].y]

                current_angle = calculate_angle(hip, knee, ankle)
                knee_angles.append(current_angle)

        cap.release()

    if knee_angles:
        max_bend = min(knee_angles)
        if max_bend > 140:
            feedback = "Try bending your knee more before striking for extra power!"
        else:
            feedback = "Good knee flexion! Great load-up for the shot."
    else:
        max_bend = 0
        feedback = "Could not detect leg clearly in the video."

    return jsonify(
        {
            "message": "Analysis complete!",
            "total_frames": frames_processed,
            "max_knee_bend_angle": max_bend,
            "coaching_tip": feedback,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
