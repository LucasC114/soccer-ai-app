from flask import Flask, request, jsonify
import cv2
import mediapipe as mp

app = Flask(__name__)

# load MediaPipe pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

@app.route("/analyze", methods=["POST"])
def analyze_video():
    # get video from request
    file = request.files["video"]
    path = "video.mp4"
    file.save(path)

    cap = cv2.VideoCapture(path)

    frames_with_pose = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        # convert for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        # check if body detected
        if results.pose_landmarks:
            frames_with_pose += 1

    cap.release()

    return jsonify({
        "frames_with_pose": frames_with_pose,
        "message": "Video analyzed successfully"
    })

if __name__ == "__main__":
    app.run(debug=True)