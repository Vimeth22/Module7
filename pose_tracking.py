"""
Real-Time Pose & Hand Tracking and Data Logging (pose_tracking.py)

This script utilizes Google's MediaPipe Holistic model to perform comprehensive, 
real-time tracking of the human body (Pose) and hands. All extracted 3D 
landmark coordinates and visibility data are saved to a CSV file for subsequent 
analysis, fulfilling the requirements for Module 7, Problem 3.
"""

import cv2
import mediapipe as mp
import csv
import time

# --- CONFIGURATION CONSTANTS ---
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5
OUTPUT_CSV_FILE = 'pose_data.csv'
WINDOW_TITLE = 'Module 7 | Pose Tracking - Data Logging Active'

# Initialize MediaPipe Solutions
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
# mp_hands is used implicitly for connection names

# --- CUSTOM DRAWING STYLES (Aesthetic Improvement) ---
# Define clean, professional colors for visualization
POSE_DRAWING_SPEC = mp_drawing.DrawingSpec(color=(63, 81, 181), thickness=2, circle_radius=2) # Indigo
HAND_DRAWING_SPEC = mp_drawing.DrawingSpec(color=(0, 150, 136), thickness=2, circle_radius=2) # Teal
POSE_CONNECTIONS_SPEC = mp_drawing.DrawingSpec(color=(255, 179, 0), thickness=2) # Amber

# --- FUNCTION TO EXTRACT DATA ---
def extract_full_data(results):
    """
    Extracts all coordinates and visibility for Pose and Right Hand landmarks.
    
    The structure ensures a fixed-length row, filling missing data with 0.0s.
    (Output structure remains identical)
    """
    row = [time.time()]
    
    # 1. Pose Landmarks (33 landmarks * 4 values: x, y, z, visibility)
    if results.pose_landmarks:
        for landmark in results.pose_landmarks.landmark:
            row.extend([landmark.x, landmark.y, landmark.z, landmark.visibility])
    else:
        row.extend([0.0] * 132) 

    # 2. Right Hand Landmarks (21 landmarks * 3 values: x, y, z)
    if results.right_hand_landmarks:
        for landmark in results.right_hand_landmarks.landmark:
            row.extend([landmark.x, landmark.y, landmark.z])
    else:
        row.extend([0.0] * 63)
        
    return row

# --- CSV HEADER GENERATION ---
def generate_header():
    """
    Dynamically creates a comprehensive CSV header for all logged data fields.
    (Output structure remains identical)
    """
    header = ['timestamp']
    
    # Pose Headers (33 landmarks: x, y, z, vis)
    for lm in mp_holistic.PoseLandmark:
        header.extend([f'{lm.name}_{c}' for c in ('x', 'y', 'z', 'vis')])
        
    # Right Hand Headers (21 landmarks: x, y, z)
    for i in range(21): 
        header.extend([f'RIGHT_HAND_{i}_{c}' for c in ('x', 'y', 'z')])
        
    return header

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    
    # Setup CSV file for writing
    try:
        csv_file = open(OUTPUT_CSV_FILE, 'w', newline='')
        writer = csv.writer(csv_file)
        writer.writerow(generate_header())
    except IOError as e:
        print(f"ERROR: Could not open {OUTPUT_CSV_FILE}. Check permissions.")
        exit()

    cap = cv2.VideoCapture(0) # Initialize default webcam
    print(f"--- Pose Tracker Initialized ---")
    print(f"Live tracking active. Data is being saved to {OUTPUT_CSV_FILE}.")
    print("Press 'q' in the video window to quit.")

    # Set up the Holistic model with constants
    with mp_holistic.Holistic(
        min_detection_confidence=MIN_DETECTION_CONFIDENCE, 
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    ) as holistic:
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from camera.")
                break
            
            # 1. FLIP FRAME FOR MIRROR EFFECT (COOLER OUTPUT)
            frame = cv2.flip(frame, 1)

            # Convert the BGR image to RGB and process it
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(image_rgb)
            
            # --- Draw Landmarks (Professional Visualization) ---
            # 1. Pose
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                                      POSE_DRAWING_SPEC, POSE_CONNECTIONS_SPEC)
            # 2. Left Hand
            mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS,
                                      HAND_DRAWING_SPEC, HAND_DRAWING_SPEC)
            # 3. Right Hand
            mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS,
                                      HAND_DRAWING_SPEC, HAND_DRAWING_SPEC)

            # --- Add Status Overlay (COOLER OUTPUT) ---
            tracking_status = f"FPS: {cap.get(cv2.CAP_PROP_FPS):.1f} | Tracking: "
            
            # Check for detected elements to update status
            if results.pose_landmarks:
                tracking_status += "BODY | "
            if results.right_hand_landmarks:
                 tracking_status += "R_HAND | "
            if results.left_hand_landmarks:
                 tracking_status += "L_HAND | "
            
            # Draw status bar at the top left
            cv2.putText(frame, 
                        tracking_status.strip(' |'), 
                        (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, 
                        "DATALOG: Active (Press 'q' to save/exit)", 
                        (10, frame.shape[0] - 10), # Bottom Left Corner
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)


            # --- Save Data to CSV ---
            try:
                row = extract_full_data(results)
                writer.writerow(row)
            except Exception:
                pass

            # Display the resulting frame
            cv2.imshow(WINDOW_TITLE, frame)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    # --- Cleanup ---
    cap.release()
    cv2.destroyAllWindows()
    csv_file.close()
    print("--- Tracking Complete ---")
    print(f"Data logging finished. Results saved to {OUTPUT_CSV_FILE}.")