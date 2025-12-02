# Module 7

This module combines **stereo geometry** with **real‑time pose/hand tracking**.  
There are two main components:

1. A **Flask web app** (`app.py` + `index.html`) that lets the user click on stereo images to:
   - Estimate the **depth (Z)** of an object using a calibrated stereo pair (Left / Right images).
   - Measure the **real‑world size** of the object at that depth using pixel distances.
2. A **stand‑alone MediaPipe script** (`pose_tracking.py`) that uses the webcam to track full‑body pose and hands and logs all landmarks to a CSV file.

---

## 1. File Structure

A typical folder layout for this module is:

```text
Module7/
├── app.py               
├── pose_tracking.py
├── templates/
│   └── index.html        
└── static/
    ├── left.jpg          # Left-eye image of the scene
    └── right.jpg         # Right-eye image of the same scene
```

> Note: In Flask, `index.html` should be placed in a `templates/` folder so that `render_template("index.html")` can find it.

---

## 2. Dependencies & Environment

This project assumes **Python 3.8+** and the following key packages:

- `flask` – to serve the Module 7 web interface.
- `opencv-python` (imported as `cv2`) – used in `pose_tracking.py` for webcam capture and display.
- `mediapipe` – for holistic body + hand tracking.
- Standard libraries: `math`, `csv`, `time`, `json` (via Flask), etc.

You can install the main dependencies with:

```bash
pip install flask opencv-python mediapipe
```

If you are using a virtual environment:

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate     # Windows (PowerShell)
pip install flask opencv-python mediapipe
```

---

## 3. Part A – Stereo Depth & Object Size (Web App)

### 3.1. Purpose

The **web app** in `app.py` plus `index.html` lets you:

1. Click a point in the **left** and **right** images of the same scene.
2. Use **stereo disparity** and a known camera calibration to estimate the **depth Z (in cm)**.
3. Use two clicks along the object on the left image to estimate its **real size (in cm)** at that depth.

The HTML front-end (`index.html`) shows:

- A **left-eye view** and **right-eye view** side by side.
- A **status bar** explaining which step the user is currently on.
- A **result panel** that displays the computed depth and size.
- A **Reset button** to restart the measurement process.

### 3.2. Camera Calibration & Scaling

In `app.py`:

- Calibration parameters (`ORIG_FX`, `ORIG_FY`, `ORIG_CX`, `ORIG_CY`, `CALIB_W`, `CALIB_H`) are taken from **Module 1** for a camera resolution of **1280×720**.
- A helper function `get_scaled_intrinsics(img_w, img_h)` scales the intrinsics to match the **actual image resolution** that is used in the webpage. This allows you to reuse the same calibration even if the displayed images are resized.

### 3.3. Depth Calculation (`/calculate_stereo`)

The route:

```python
@app.route('/calculate_stereo', methods=['POST'])
def calculate_stereo():
    ...
```

receives JSON from the frontend with:

- `p_left`  – the clicked point in the left image (in pixel coordinates).
- `p_right` – the corresponding point in the right image.
- `img_w`, `img_h` – the natural width and height of the images.

Using the scaled intrinsics, the code:

1. Computes **disparity** in pixels  
   \\( d = |x_L - x_R| \\)
2. Uses the known **baseline** (physical distance between the two camera positions) and the focal length to estimate  
   \\( Z = \frac{f \cdot B}{d} \\) (in cm, after unit conversion).

The result is returned to the browser as JSON, and the front-end displays:

```text
Calculated Depth (Z): <value> cm
```

### 3.4. Size Measurement (`/calculate_size`)

The route:

```python
@app.route('/calculate_size', methods=['POST'])
def calculate_size():
    ...
```

receives:

- Two 2D pixel points `p1`, `p2` on the **same object** in the left image.
- The previously computed depth `Z`.
- Image width/height for scaling intrinsics.

Using pinhole projection:

- Each point \\((u,v)\\) is converted into a 3D coordinate \\((X,Y,Z)\\) using:
  \\[
  X = \frac{(u - c_x)Z}{f_x}, \quad
  Y = \frac{(v - c_y)Z}{f_y}
  \\]
- Then it computes the Euclidean distance in the X–Y plane:
  \\[
  \text{size} = \sqrt{(X_2 - X_1)^2 + (Y_2 - Y_1)^2}
  \\]

The endpoint returns JSON with:

- `size_cm` – estimated real‑world length between the two clicked points.
- `dX`, `dY` – horizontal and vertical components (in cm).

This is shown in the result panel as:

```text
Depth (Z): <Z> cm
Size: <size_cm> cm
```

### 3.5. Front-End Interaction Flow

From `index.html`, the interaction is:

1. **Step 1**  
   - Click the **center of the object** in the **Left Image**.  
   - A red dot is drawn and the status bar updates.

2. **Step 2**  
   - Click the **same physical point** in the **Right Image**.  
   - The app calls `/calculate_stereo`, computes the depth, and updates the result.

3. **Step 3**  
   - In the **Left Image**, click the **first point** on the object you want to measure (e.g., left edge).

4. **Step 4**  
   - Click the **second point** (e.g., right edge).  
   - The app calls `/calculate_size` and prints the estimated size in cm.

5. **Reset**  
   - Press the **“Reset Measurement”** button to clear dots and start over.

The JavaScript handles coordinate scaling so that clicks on the resized images map back to the **original pixel coordinates**, ensuring the math in `app.py` stays correct. fileciteturn0file0L1-L190

---

## 4. Part B – Real-Time Pose & Hand Tracking (`pose_tracking.py`)

### 4.1. Purpose

`pose_tracking.py` implements **Module 7**.  
It uses **MediaPipe Holistic** to track:

- Full‑body **pose landmarks**
- **Face** landmarks
- **Hand** landmarks (left and right)

All detected landmark coordinates are written to a CSV file for later analysis.

### 4.2. High-Level Workflow

1. Open the default webcam using OpenCV.
2. Initialize `mp_holistic.Holistic()` for joint detection.
3. For each frame:
   - Run Holistic inference to get pose, face, and hand landmarks.
   - Draw landmarks and connections on the frame for visualization.
   - Extract **x, y, z, visibility** values for each landmark.
   - Flatten them into a single row and write to `pose_data.csv` with:
     - Frame index and/or timestamp
     - All landmark values (pose + hands, etc.)
4. Show the video stream in a named window.
5. Stop when the user presses **`q`**.
6. Release the camera, close windows, and close the CSV file.

The script is wrapped with basic `try/except` around the per-frame extraction logic, so occasional decoding errors do not crash the entire stream.

### 4.3. Expected Output

- A window titled something like **“Pose Tracking – Output for P3”** that shows your webcam feed with overlaid pose/hand landmarks.
- A CSV file, typically named **`pose_data.csv`**, storing per-frame landmark data. Each row corresponds to one frame.

---

## 5. How to Run

### 5.1. Running the Stereo Web App

1. Make sure your folder structure is:

   ```text
   Module7/
   ├── app.py
   ├── pose_tracking.py
   ├── templates/
   │   └── index.html
   └── static/
       ├── left.jpg
       └── right.jpg
   ```

2. Place your calibrated stereo pair as:
   - `static/left.jpg`
   - `static/right.jpg`

3. Start the Flask server:

   ```bash
   cd Module7
   python app.py
   ```

4. Open a browser and visit:

   ```text
   http://127.0.0.1:5000/
   ```

5. Follow the **Step 1–4** instructions on the page to:
   - Compute **depth** from stereo clicks.
   - Measure **object size** at that depth.

### 5.2. Running the Pose Tracking Script

1. Ensure your webcam is connected and not used by other programs.
2. From the same environment (with `opencv-python` and `mediapipe` installed), run:

   ```bash
   python pose_tracking.py
   ```

3. A video window will appear:
   - Move so that your entire body (or upper body + hands) is in frame.
   - Landmarks will be drawn on top of the video.
4. When you are done recording, press **`q`**.
5. Check the file **`pose_data.csv`** in your working directory to inspect the recorded data.

## Pose Estimation Output CSV data format Explonation.

- The pose estimation component delivers two forms of output: a visual display and a CSV data file. The visual output presents the live webcam stream with MediaPipe’s pose, hand, and face landmarks superimposed, allowing you to observe the tracked joints in real time. Every frame is simultaneously captured into a CSV file called `pose_data.csv`. Four values—x, y, z, and visibility—represent each landmark, and each row in the CSV represents a single frame. Z is the landmark's depth in relation to the camera, x and y are normalized picture coordinates (ranging from 0 to 1), and visibility is MediaPipe's confidence score that indicates the likelihood that the landmark is accurately detected. As a result, the CSV offers a comprehensive numerical depiction of the subject's evolution throughout time. In your report, you should explain how these data might be utilized for motion analysis—such as tracking arm movement, computing joint angles, or evaluating posture—in addition to showing sample visual frames and excerpts from the CSV file.

---

## 6. Notes for the Report / Write-Up

- Clearly explain how the **calibration parameters** from Module 1 are being reused and rescaled.
- Include the formula for **stereo depth** and show at least one manual numerical example.
- For the size measurement, show how pixel distances are converted back into **metric distances** using the intrinsic parameters and the estimated depth.
- For the pose tracking part, you can:
  - Plot selected landmarks over time from `pose_data.csv`.
  - Discuss stability, noise, and any limitations you observe.


