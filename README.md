# Impact Detection Using a Self-Trained YOLO Model

## Overview

This project implements a real-time impact/explosion detection system using a self-trained YOLOv3 model. It combines computer vision, GPS localization, geospatial calculations, and automated alerting to detect explosions from a live video feed and estimate real-world coordinates.

The system is designed to work with:

- A physical camera or an OBS virtual camera
- Drone GPS coordinates or IP-based PC location
- Google Maps APIs for reverse geocoding
- Email alerts for real-time notifications

This architecture is suitable for surveillance, defense, disaster response, and aerial monitoring applications.

## Key Features

- Real-time explosion detection using a custom-trained YOLOv3 model
- Live camera feed support
  - Physical webcam
  - OBS Virtual Camera
- Dual location sources
  - Drone GPS coordinates
  - IP-based PC geolocation (Google Geolocation API)
- GPS coordinate estimation for detected impact locations
- Reverse geocoding using Google Maps API
- Automated email alerts with Google Maps links
- Cursor-to-GPS mapping for manual analysis
- Cooldown mechanism to prevent repeated alerts

## System Architecture

- Video capture from camera source
- Explosion detection using YOLOv3
- Geospatial computation of impact coordinates
- Reverse geocoding via Google Maps API
- Email notification with location details
- Real-time visualization and user interaction

## Technologies Used

- Python
- OpenCV
- YOLOv3 (custom trained)
- NumPy
- Google Maps API
- Google Geolocation API
- Geopy
- SMTP (Email notifications)

## Project Structure

```
Impact-Detection-YOLO/
├── yolov3_training_last.weights
├── yolov3_testing.cfg
├── main.py
└── README.md
```

> Note: Update the weight and configuration file paths according to your local setup.

## Setup Instructions

### 1. Install dependencies

```bash
pip install opencv-python numpy geopy googlemaps requests
```

### 2. Configure API keys

Update the following in the source code:

```python
GOOGLE_MAPS_API_KEY = "YOUR_API_KEY"
```

Ensure the following APIs are enabled:

- Google Maps API
- Google Geolocation API

### 3. Configure email alerts

```python
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
```

Use a Gmail App Password instead of your main account password.

### 4. YOLO model setup

Update paths to the trained YOLO model:

```python
cv2.dnn.readNet(
    "path/to/yolov3_training_last.weights",
    "path/to/yolov3_testing.cfg"
)
```

Detected classes:

```python
classes = ["Explosion"]
```

## Running the Application

```bash
python main.py
```

At runtime, select:

- Location source (PC IP-based or Drone GPS)
- Camera source (Webcam or OBS Virtual Camera)

Press `q` or `ESC` to exit.

## GPS and Impact Coordinate Estimation

The system estimates explosion coordinates using:

- Camera field of view (horizontal and vertical)
- Bounding box center
- Drone GPS position
- Bearing-based geodesic calculations

Coordinates are approximate and depend on camera calibration and distance estimation.

## Cursor-to-GPS Mapping

The mouse cursor position on the video feed can be mapped to real-world GPS coordinates using:

- Camera altitude
- Pitch, roll, and yaw angles
- Camera field of view
- Image and frame resolution scaling

This is useful for manual inspection and spatial analysis.

## Alert Cooldown Logic

```python
cooldown_period = 60  # seconds
```

This prevents repeated email alerts for continuous detections.

## Important Notes

- Coordinate accuracy depends on camera calibration, altitude, and distance assumptions
- Intended for research, simulation, and controlled testing environments
- Not recommended for autonomous real-world deployment without validation

## Disclaimer

This project is intended for educational and research purposes only. The author is not responsible for misuse of this software.
