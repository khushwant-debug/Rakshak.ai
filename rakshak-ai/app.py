import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, Response, request, jsonify
from detector import CarDetector
from alerts import Alerts
from database import Database
import cv2
import threading
import time
import os
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Use an absolute path for uploads (folder inside the app directory)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
detector = CarDetector()
alerts = Alerts()
db = Database()

accident_event = threading.Event()
current_accident_status = {'accident': False, 'severity': 0}

def generate_frames(source):
    try:
        if source not in ['webcam'] and not source.startswith('rtsp://'):
            source = os.path.join(app.config['UPLOAD_FOLDER'], source)
        for frame, car_count, accident_flag, severity in detector.process_video(source):
            # If detector signals an accident, update status and trigger alerts/logging in background
            if accident_flag:
                current_accident_status['accident'] = True
                current_accident_status['severity'] = severity
                # start background handler thread so the stream isn't blocked
                threading.Thread(target=handle_accident, args=(severity,), daemon=True).start()

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        print(f"Error in generate_frames: {e}")
        # Yield a blank frame or error message
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank_frame, "Video source error", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        ret, buffer = cv2.imencode('.jpg', blank_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def handle_accident(severity):
    try:
        alerts.play_siren()
        alerts.send_sms()
        db.log_accident(severity=severity)
    except Exception as e:
        print(f"Error in handle_accident: {e}")
    # keep accident flag true for a short period so frontend can show alert
    time.sleep(5)
    current_accident_status['accident'] = False
    current_accident_status['severity'] = 0
    accident_event.clear()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/video_feed')
def video_feed():
    source = request.args.get('source', 'webcam')
    return Response(generate_frames(source), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'filename': filename})

@app.route('/accident_status')
def accident_status():
    return jsonify(current_accident_status)

@app.route('/logs')
def get_logs():
    logs = db.get_logs()
    return jsonify(logs)

@app.route('/stats')
def get_stats():
    count = db.get_accident_count()
    return jsonify({'accident_count': count})

if __name__ == '__main__':
    app.run(debug=True)
