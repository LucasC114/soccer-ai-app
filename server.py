import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, request, jsonify
import os
import urllib.request
from flask import send_file

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
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps is None:
        fps = 30

    print("FPS:", fps)
    print("WIDTH:", width)
    print("HEIGHT:", height)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(
        "output_skeleton.mp4",
        fourcc,
        fps,
        (width, height)
    )

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

                h, w, _ = frame.shape
                #Draw skeleton points
                for landmark in landmarks:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

                connections = [
                    (11, 13), (13, 15),  # left arm
                    (12, 14), (14, 16),  # right arm
                    (11, 12),            # shoulders
                    (11, 23), (12, 24),  # torso
                    (23, 24),            # hips
                    (23, 25), (25, 27),  # left leg
                    (24, 26), (26, 28),  # right leg
                ]

                for start, end in connections:
                    x1 = int(landmarks[start].x * w)
                    y1 = int(landmarks[start].y * h)

                    x2 = int(landmarks[end].x * w)
                    y2 = int(landmarks[end].y * h)

                    cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)
                #Knee angle calculation
                hip = [landmarks[24].x, landmarks[24].y]
                knee = [landmarks[26].x, landmarks[26].y]
                ankle = [landmarks[28].x, landmarks[28].y]

                current_angle = calculate_angle(hip, knee, ankle)
                knee_angles.append(current_angle)
                out.write(frame)
        out.release()
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
@app.route("/get-video", methods=["GET"])
def get_video():
    return send_file("output_skeleton.mp4", mimetype="video/mp4")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)