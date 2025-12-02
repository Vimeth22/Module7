from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

# 1. Camera Calibration (from Assignment 1)
# These values correspond to the original 1280x720 resolution.
ORIG_FX = 991.396
ORIG_FY = 991.628
ORIG_CX = 671.244
ORIG_CY = 371.286
CALIB_W = 1280
CALIB_H = 720

# 2. Experimental Measurement
# The distance the laptop was moved between the two photos (Left -> Right)
BASELINE = 10.0  # cm

@app.route('/')
def index():
    # NOTE: Your left.jpg and right.jpg images must be placed 
    # in a 'static' folder next to app.py.
    return render_template('index.html')

def get_scaled_intrinsics(img_w, img_h):
    """
    Adjusts the focal length and center point if the user's uploaded 
    photo resolution is different from the calibration resolution.
    """
    scale_x = img_w / CALIB_W
    scale_y = img_h / CALIB_H
    
    fx = ORIG_FX * scale_x
    fy = ORIG_FY * scale_y
    cx = ORIG_CX * scale_x
    cy = ORIG_CY * scale_y
    
    return fx, fy, cx, cy

# --- STEP 1: Calculate Depth (Z) ---
@app.route('/calculate_stereo', methods=['POST'])
def calculate_stereo():
    data = request.get_json()
    
    p_left = data['p_left']
    p_right = data['p_right']
    img_w = data['img_w']
    img_h = data['img_h']

    # Get correct camera matrix for this image size
    fx, fy, cx, cy = get_scaled_intrinsics(img_w, img_h)

    # 1. Calculate Disparity: d = x_L - x_R (in pixels)
    disparity = abs(p_left['x'] - p_right['x'])
    
    if disparity < 1.0:
        return jsonify({"error": "Disparity is too small (d < 1.0). You clicked the same pixel or close to it!"})

    # 2. Apply Stereo Vision Formula: Z = (f * B) / d
    calculated_Z = (fx * BASELINE) / disparity

    print(f"DEBUG: Disparity={disparity:.2f} px | Calculated Z={calculated_Z:.2f} cm")

    return jsonify({
        "Z": round(calculated_Z, 4),
        "disparity": round(disparity, 2)
    })

# --- STEP 2: Calculate Real Size ---
@app.route('/calculate_size', methods=['POST'])
def calculate_size():
    data = request.get_json()
    
    p1 = data['p1']
    p2 = data['p2']
    Z = data['Z']  # Use the Z we just calculated
    img_w = data['img_w']
    img_h = data['img_h']
    
    fx, fy, cx, cy = get_scaled_intrinsics(img_w, img_h)

    # Convert 2D Pixel (u,v) to 3D World (X,Y) at depth Z
    # Formula: X = (pixel_x - center_x) * Z / fx
    X1 = (p1['x'] - cx) * Z / fx
    Y1 = (p1['y'] - cy) * Z / fy
    
    X2 = (p2['x'] - cx) * Z / fx
    Y2 = (p2['y'] - cy) * Z / fy

    # Euclidean distance in the X-Y plane
    dx = X2 - X1
    dy = Y2 - Y1
    real_size = math.sqrt(dx**2 + dy**2)

    return jsonify({
        "size_cm": round(real_size, 4),
        "dX": round(abs(dx), 4),
        "dY": round(abs(dy), 4)
    })

if __name__ == '__main__':
    app.run(debug=True)