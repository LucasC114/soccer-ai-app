import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, request, jsonify
import os
import base64
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

def calculate_trunk_lean(shoulder, hip):
    dx = shoulder[0] - hip[0]
    dy = hip[1] - shoulder[1]

    angle = np.degrees(np.arctan2(dx, dy))

    return round(angle, 1)

@app.route("/video-info", methods=["POST"])
def video_info():

    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video = request.files["video"]
    path = "./temp_info.mp4"
    video.save(path)

    cap = cv2.VideoCapture(path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.release()

    return jsonify({
        "fps": fps,
        "totalFrames": total_frames
    })
@app.route("/analyze", methods=["POST"])
def analyze_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    shot_type = request.form.get("shotType")
    print ("Shot Type:", shot_type)

    kicking_leg = request.form.get("kickingLeg")
    print("Kicking Leg:", kicking_leg)

    contact_time = float(request.form.get("contactTime"))
    print("Contact time:", contact_time)

    video_file = request.files["video"]
    video_path = "./temp_video.mp4"
    video_file.save(video_path)

    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    contact_frame = int(contact_time * fps)
    before_seconds = 0.3
    after_seconds = 0.2

    start_frame = max(0, int(contact_frame - before_seconds * fps))
    end_frame = int(contact_frame + after_seconds * fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    if fps == 0 or fps is None:
        fps = 30

    print("Contact frame:", contact_frame)

    # Analyze 0.3 seconds before and 0.2 seconds after contact
    frames_before = int(fps * 0.3)
    frames_after = int(fps * 0.2)

    start_frame = max(0, int(contact_frame) - frames_before)
    end_frame = int(contact_frame) + frames_after

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    # Store biomechanics data
    knee_data = []
    hip_data = []
    ankle_data = []
    trunk_data = []

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
        while cap.get(cv2.CAP_PROP_POS_FRAMES) <= end_frame:
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

                # ---------- Select kicking leg ----------
                if kicking_leg == "right":
                    shoulder = [landmarks[12].x, landmarks[12].y]
                    hip = [landmarks[24].x, landmarks[24].y]
                    knee = [landmarks[26].x, landmarks[26].y]
                    ankle = [landmarks[28].x, landmarks[28].y]
                    foot = [landmarks[32].x, landmarks[32].y]
                else:
                    shoulder = [landmarks[11].x, landmarks[11].y]
                    hip = [landmarks[23].x, landmarks[23].y]
                    knee = [landmarks[25].x, landmarks[25].y]
                    ankle = [landmarks[27].x, landmarks[27].y]
                    foot = [landmarks[31].x, landmarks[31].y]

                # ---------- Calculate joint angles ----------
                # ---------- Trunk lean ----------
                trunk_lean = calculate_trunk_lean(
                    shoulder,
                    hip
                )

                knee_angle = calculate_angle(
                    hip,
                    knee,
                    ankle
                )

                hip_angle = calculate_angle(
                    shoulder,
                    hip,
                    knee
                )

                ankle_angle = calculate_angle(
                    knee,
                    ankle,
                    foot
                )

                # Save measurements for this frame
                knee_data.append({
                    "frame": int(cap.get(cv2.CAP_PROP_POS_FRAMES)),
                    "knee": knee_angle
                })

                hip_data.append({
                    "frame": int(cap.get(cv2.CAP_PROP_POS_FRAMES)),
                    "hip": hip_angle
                })

                ankle_data.append({
                    "frame": int(cap.get(cv2.CAP_PROP_POS_FRAMES)),
                    "ankle": ankle_angle
                })

                trunk_data.append({
                    "frame": int(cap.get(cv2.CAP_PROP_POS_FRAMES)),
                    "trunk": trunk_lean
                })
                out.write(frame)
        out.release()
        cap.release()

    if knee_data:

        # Load-up = deepest knee bend
        loadup_index = knee_data.index(
            min(knee_data, key=lambda x: x["knee"])
        )

        loadup_frame = knee_data[loadup_index]["frame"]

        # Find matching values from other data lists
        loadup = {
            "knee": knee_data[loadup_index]["knee"],
            "hip": hip_data[loadup_index]["hip"],
            "ankle": ankle_data[loadup_index]["ankle"],
            "trunk": trunk_data[loadup_index]["trunk"],
        }


        # Contact frame
        contact_index = next(
            (
                i for i, x in enumerate(knee_data)
                if x["frame"] >= contact_frame
            ),
            len(knee_data)-1
        )

        contact = {
            "knee": knee_data[contact_index]["knee"],
            "hip": hip_data[contact_index]["hip"],
            "ankle": ankle_data[contact_index]["ankle"],
            "trunk": trunk_data[contact_index]["trunk"],
        }


        # Follow-through = last analyzed frame
        follow_index = len(knee_data)-1

        followthrough = {
            "knee": knee_data[follow_index]["knee"],
            "hip": hip_data[follow_index]["hip"],
            "ankle": ankle_data[follow_index]["ankle"],
            "trunk": trunk_data[follow_index]["trunk"],
        }


        if loadup["knee"] > 140:
            feedback = "Try bending your knee more before striking for extra power!"
        else:
            feedback = "Good knee flexion during load-up."

    else:

        loadup = {"knee":0}
        contact = {"knee":0}
        followthrough = {"knee":0}

        feedback = "Could not detect leg clearly in the video."

    return jsonify({

        "message": "Analysis complete!",

        "loadup": {
            "knee_angle": loadup["knee"],
            "hip_angle": loadup["hip"],
            "ankle_angle": loadup["ankle"],
            "trunk_lean": loadup["trunk"],
        },

        "contact": {
            "knee_angle": contact["knee"],
            "hip_angle": contact["hip"],
            "ankle_angle": contact["ankle"],
            "trunk_lean": contact["trunk"],
        },

        "followthrough": {
            "knee_angle": followthrough["knee"],
            "hip_angle": followthrough["hip"],
            "ankle_angle": followthrough["ankle"],
            "trunk_lean": followthrough["trunk"],
        },

        "coaching_tip": feedback,

    })
@app.route("/extract-frames", methods=["POST"])
def extract_frames():

    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    video_path = "./frame_video.mp4"
    video_file.save(video_path)

    cap = cv2.VideoCapture(video_path)

    frames = []
    frame_number = 0

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps == 0:
        fps = 30

    while True:
        success, frame = cap.read()

        if not success:
            break

        # Take every 3rd frame
        if frame_number % 3 == 0:

            # Make smaller preview
            frame = cv2.resize(frame, (160, 90))

            success, buffer = cv2.imencode(".jpg", frame)

            if success:
                image_base64 = base64.b64encode(buffer).decode("utf-8")

                frames.append({
                    "frame": frame_number,
                    "time": frame_number / fps,
                    "image": image_base64
                })

        frame_number += 1

    cap.release()

    return jsonify({
        "fps": fps,
        "totalFrames": frame_number,
        "frames": frames
    })
@app.route("/get-video", methods=["GET"])
def get_video():
    return send_file("output_skeleton.mp4", mimetype="video/mp4")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)