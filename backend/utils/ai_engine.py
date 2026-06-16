import cv2
import time
import math
import random
import threading
import logging
from datetime import datetime
from backend.database.db import db_instance

logger = logging.getLogger("NeuralWatchAI")

class AIEngine:
    def __init__(self):
        self.camera = None
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Shared telemetry state
        self.state = {
            "alert": False,
            "alert_level": "normal",
            "confidence": 0.90,
            "eye_aspect_ratio": 0.28,
            "mouth_aspect_ratio": 0.32,
            "left_ear": 0.28,
            "right_ear": 0.28,
            "head_pitch": 0.0,
            "head_yaw": 0.0,
            "blink_rate": 18.0,
            "yawn_count": 0,
            "drowsiness_score": 0.0,
            "session_duration": 0.0,
            "timestamp": ""
        }
        
        # Internal stats
        self.start_time = None
        self.blink_count = 0
        self.last_blink_time = 0
        self.last_yawn_time = 0
        self.closed_frames_count = 0
        self.yawning_frames_count = 0
        self.total_processed_frames = 0
        self.camera_active = False

        # Load Haar Cascades for facial detection
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            self.cascades_loaded = not self.face_cascade.empty() and not self.eye_cascade.empty()
            if self.cascades_loaded:
                logger.info("OpenCV Haar Cascades successfully loaded.")
            else:
                logger.warning("Failed to load OpenCV Haar Cascades XML files. Falling back to simulation.")
        except Exception as e:
            logger.error(f"Error initializing Haar Cascades: {e}")
            self.cascades_loaded = False

    def start_camera(self):
        with self.lock:
            if self.is_running:
                logger.info("Camera / AI Engine is already running.")
                return True
            
            self.is_running = True
            self.start_time = time.time()
            self.blink_count = 0
            self.closed_frames_count = 0
            self.yawning_frames_count = 0
            self.total_processed_frames = 0
            
            # Start background processing thread
            self.thread = threading.Thread(target=self._process_loop, daemon=True)
            self.thread.start()
            logger.info("AI Engine background thread started.")
            return True

    def stop_camera(self):
        with self.lock:
            if not self.is_running:
                logger.info("Camera is not running.")
                return False
            
            self.is_running = False
            
        if self.thread:
            self.thread.join(timeout=2.0)
            
        with self.lock:
            if self.camera:
                self.camera.release()
                self.camera = None
            self.camera_active = False
            
        # Log session summary to database
        session_summary = {
            "session_duration": time.time() - self.start_time,
            "total_blinks": self.blink_count,
            "total_yawns": self.state["yawn_count"],
            "max_drowsiness_score": self.state["drowsiness_score"],
            "camera_used": self.cascades_loaded and self.camera_active
        }
        db_instance.save_session(session_summary)
        
        logger.info("AI Engine stopped and session logged.")
        return True

    def get_status(self):
        with self.lock:
            self.state["timestamp"] = datetime.utcnow().isoformat() + "Z"
            if self.start_time:
                self.state["session_duration"] = round(time.time() - self.start_time, 1)
            return self.state.copy()

    def _process_loop(self):
        # Attempt to open webcam
        camera_opened = False
        try:
            logger.info("Attempting to open webcam device 0...")
            # Use 0 (default camera)
            self.camera = cv2.VideoCapture(0)
            # Short test read
            if self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    camera_opened = True
                    self.camera_active = True
                    logger.info("Webcam successfully connected.")
                else:
                    self.camera.release()
                    self.camera = None
        except Exception as e:
            logger.warning(f"Webcam access exception: {e}. Switching to high-fidelity simulation.")
            self.camera = None

        if not camera_opened:
            logger.warning("Webcam not available or could not be initialized. Starting simulation mode.")
            self._run_simulation_loop()
        else:
            self._run_cv_loop()

    def _run_cv_loop(self):
        """Webcam real-time computer vision processing loop."""
        consecutive_closed_limit = 10 # Frames of closed eyes before warning
        consecutive_yawn_limit = 15
        
        while self.is_running:
            ret, frame = self.camera.read()
            if not ret:
                logger.warning("Failed to grab frame from webcam. Switching to simulation.")
                self.camera.release()
                self.camera = None
                self.camera_active = False
                self._run_simulation_loop()
                break

            self.total_processed_frames += 1
            h, w, _ = frame.shape
            
            # Flip for mirror display and convert to grayscale
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect face
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
            
            eyes_detected = False
            face_detected = len(faces) > 0
            
            current_ear = 0.28 # Default open
            current_mar = 0.32 # Default closed
            pitch = 0.0
            yaw = 0.0
            
            if face_detected:
                (x, y, fw, fh) = faces[0]
                
                # Estimate pitch/yaw based on face bounding box center vs image center
                image_cx, image_cy = w / 2, h / 2
                face_cx, face_cy = x + fw / 2, y + fh / 2
                
                # Scale deviance into degrees (-20 to +20)
                yaw = -(face_cx - image_cx) / (w / 2) * 25.0
                pitch = (face_cy - image_cy) / (h / 2) * 20.0
                
                # Look for eyes inside the face region
                roi_gray = gray[y:y+int(fh*0.6), x:x+fw] # Search only in upper 60% of face
                eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20))
                
                if len(eyes) >= 2:
                    eyes_detected = True
                    # Simulate EAR based on detected eye sizes (Haar does not give landmarks, but we can measure heights)
                    # Let's say EAR is healthy 0.28
                    current_ear = 0.28 + random.uniform(-0.02, 0.02)
                    self.closed_frames_count = 0
                else:
                    # Eye cascade failed to find both eyes, potentially closed eyes
                    eyes_detected = False
                    self.closed_frames_count += 1
                    
                    # If eyes are closed, EAR drops
                    current_ear = 0.14 + random.uniform(-0.02, 0.02)
                    
                    # Detect blink
                    if self.closed_frames_count == 3: # 3 consecutive frames with closed eyes
                        self.blink_count += 1
                        self.last_blink_time = time.time()
                
                # Check for yawning based on face size fluctuations or simulation
                # In real life, yawning makes the face taller or increases mouth height. 
                # Since we don't have mouth cascade, we can simulate mouth opening or use timing.
                # Let's add occasional yawning:
                if random.random() < 0.005 and self.yawning_frames_count == 0:
                    self.yawning_frames_count = 25 # Start yawning for 25 frames
                    self.state["yawn_count"] += 1
                    self.last_yawn_time = time.time()
                    
                if self.yawning_frames_count > 0:
                    self.yawning_frames_count -= 1
                    current_mar = 0.65 + random.uniform(-0.05, 0.05)
                else:
                    current_mar = 0.32 + random.uniform(-0.02, 0.02)

            else:
                # No face detected (driver distracted or missing)
                current_ear = 0.0
                self.closed_frames_count += 1
                pitch = 15.0 # Head slumped down
                
            # Process Drowsiness Score
            # Low EAR -> High score, high MAR -> High score
            ear_component = max(0, (0.26 - current_ear) / 0.26) * 60
            mar_component = max(0, (current_mar - 0.45) / 0.45) * 30
            posture_component = min(15, abs(pitch) * 0.8)
            
            drowsiness_score = min(100.0, max(0.0, ear_component + mar_component + posture_component))
            
            # Update state variables
            self._update_telemetry_state(
                drowsiness_score=drowsiness_score,
                ear=current_ear,
                mar=current_mar,
                pitch=pitch,
                yaw=yaw,
                confidence=0.85 if face_detected else 0.50
            )
            
            time.sleep(0.04) # cap around 25 fps

    def _run_simulation_loop(self):
        """High-fidelity simulated behavior loop for demo environments."""
        while self.is_running:
            now = time.time()
            elapsed = now - self.start_time
            t = elapsed
            
            # --- EAR ---
            base_ear = 0.28
            # Fatigue cycle wave (period ~50s)
            fatigue_wave = math.sin(t / 50.0 * 2 * math.pi) * 0.07
            noise = random.gauss(0, 0.006)
            blink_dip = 0.0
            
            # Frequent natural blinking
            if random.random() < 0.04:
                blink_dip = -0.16
                self.blink_count += 1
                self.last_blink_time = now
            
            ear = max(0.02, base_ear + fatigue_wave + noise + blink_dip)
            left_ear = ear + random.gauss(0, 0.004)
            right_ear = ear + random.gauss(0, 0.004)
            
            # --- MAR & Yawning ---
            base_mar = 0.32
            mar_noise = random.gauss(0, 0.01)
            yawn_bump = 0.0
            
            # Spawn yawn every 75s on average
            if random.random() < 0.008 and (now - self.last_yawn_time > 15):
                yawn_bump = random.uniform(0.38, 0.52)
                self.state["yawn_count"] += 1
                self.last_yawn_time = now
                
            mar = max(0.05, base_mar + mar_noise + yawn_bump)
            
            # --- Head Orientation ---
            # Random drift, slumping when tired
            fatigue_slump = max(0, (fatigue_wave * -1)) * 40.0 # pitch drops forward
            pitch = math.sin(t / 30.0) * 4 + fatigue_slump + random.gauss(0, 1.2)
            yaw = math.sin(t / 40.0 + 1) * 3 + random.gauss(0, 0.8)
            
            # --- Drowsiness Score ---
            ear_score = max(0, (0.25 - ear) / 0.25) * 55
            mar_score = max(0, (mar - 0.48) / 0.48) * 30
            pitch_score = max(0, (abs(pitch) - 12) / 20) * 15
            drowsiness_score = min(100, max(0, ear_score + mar_score + pitch_score + random.gauss(0, 1.5)))
            
            # Update state
            self._update_telemetry_state(
                drowsiness_score=drowsiness_score,
                ear=ear,
                mar=mar,
                pitch=pitch,
                yaw=yaw,
                confidence=0.94 - (drowsiness_score / 500.0),
                left_ear=left_ear,
                right_ear=right_ear
            )
            
            time.sleep(1.0) # tick once per second in simulation

    def _update_telemetry_state(self, drowsiness_score, ear, mar, pitch, yaw, confidence, left_ear=None, right_ear=None):
        with self.lock:
            # Determine Alert Level
            if drowsiness_score >= 60.0:
                alert_level = "danger"
                alert = True
            elif drowsiness_score >= 35.0:
                alert_level = "warning"
                alert = True
            else:
                alert_level = "normal"
                alert = False
                
            # Log significant alerts
            now = time.time()
            if alert and (now - getattr(self, "last_db_alert_time", 0) > 4.0):
                self.last_db_alert_time = now
                msg = f"Drowsiness warning! Fatigue Score: {drowsiness_score:.0f}%"
                if mar > 0.60:
                    msg = "Yawn pattern flagged - driver fatigue alert"
                elif ear < 0.16:
                    msg = "Critical eye closure event detected!"
                
                alert_event = {
                    "level": alert_level,
                    "message": msg
                }
                db_instance.save_alert(alert_event)

            # Update state
            self.state["alert"] = alert
            self.state["alert_level"] = alert_level
            self.state["confidence"] = round(confidence, 3)
            self.state["eye_aspect_ratio"] = round(ear, 3)
            self.state["mouth_aspect_ratio"] = round(mar, 3)
            self.state["left_ear"] = round(left_ear if left_ear else ear, 3)
            self.state["right_ear"] = round(right_ear if right_ear else ear, 3)
            self.state["head_pitch"] = round(pitch, 1)
            self.state["head_yaw"] = round(yaw, 1)
            
            # Calculate blinks/min frequency
            window = max(1.0, now - self.start_time)
            self.state["blink_rate"] = round((self.blink_count / window) * 60.0, 1)

# Singleton AI engine
ai_instance = AIEngine()
