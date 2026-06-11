import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# 1. Setup the NEW MediaPipe Pose tracking for Python 3.14+
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# We use the standard model selection for basic pose tracking
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_buffer=None), # MediaPipe will auto-load standard weights
    running_mode=VisionRunningMode.VIDEO
)

def calculate_angle(a, b, c):
    """Calculates the angle between three points (Hip, Knee, Ankle)"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return int(angle)

@app.route('/analyze', methods=['POST'])
def analyze_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
        
    video_file = request.files['video']
    video_path = "./temp_video.mp4"
    video_file.save(video_path)

    cap = cv2.VideoCapture(video_path)
    knee_angles = []
    frames_processed = 0

    # Open the MediaPipe detector
    with PoseLandmarker.create_from_options(options) as landmarker:
        while True:
            success, frame = cap.read()
            if not success:
                break
                
            frames_processed += 1
            
            # Convert frame to MediaPipe Image format
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Get timestamp in milliseconds
            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            
            # Detect landmarks
            detection_result = landmarker.detect_for_video(mp_image, timestamp_ms)
            
            # Check if landmarks were found
            if detection_result.pose_landmarks:
                # Grab the first person detected
                landmarks = detection_result.pose_landmarks[0]
                
                # Right Hip is index 24, Right Knee is index 26, Right Ankle is index 28 in new system
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

    return jsonify({
        "message": "Analysis complete!",
        "total_frames": frames_processed,
        "max_knee_bend_angle": max_bend,
        "coaching_tip": feedback
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)