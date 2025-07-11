import cv2
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from geopy.distance import geodesic
from geopy.point import Point
import googlemaps
import time
import requests
import math


# Location source selection
print("Select location source:")
print("1. PC's Location (IP-based)")
print("2. Drone's GPS Coordinates")
location_choice = input("Enter your choice (1/2): ")


# Google Maps API Key
GOOGLE_MAPS_API_KEY = ""
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Email credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "aairconfisys@gmail.com"
EMAIL_PASSWORD = "nsya zbgo cyqx bxjj"  # Use an App Password

# Load YOLO model
net = cv2.dnn.readNet(
    r"C:\Project\Confidential Project (Military)\trained 1\yolov3_training_last.weights",
    r"C:\Project\Confidential Project (Military)\trained 1\yolov3_testing.cfg"
)

classes = ["Explosion"]

layer_names = net.getLayerNames()
if isinstance(net.getUnconnectedOutLayers(), np.ndarray):
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
else:
    output_layers = [layer_names[net.getUnconnectedOutLayers() - 1]]

box_color = (255, 255, 255)
stroke_color = (0, 0, 0)
text_color = (255, 255, 255)

# Camera input selection
print("Select input source:")
print("1. Physical Camera (Default webcam)")
print("2. OBS Virtual Camera")
choice = input("Enter your choice (1/2): ")

if choice == "1":
    cap = cv2.VideoCapture(0)
elif choice == "2":
    virtual_cam_index = input("Enter the camera index for OBS Virtual Camera (usually 1 or higher): ")
    cap = cv2.VideoCapture(int(virtual_cam_index))
else:
    print("Invalid choice. Exiting...")
    exit()

if not cap.isOpened():
    print("Error: Could not open the selected camera.")
    exit()
    
# Global variable to store the last coordinates
last_coords = None

# Initialize previous coordinates
previous_lat, previous_lng = None, None

def get_gps_coordinates():
    
    global previous_lat, previous_lng  # Use global variables to track the previous coordinates
    
    if location_choice == "2":
        try:
            lat = 19.230154
            lng = 72.839063
            
            if lat != previous_lat or lng != previous_lng:
                print(f"Retrieved GPS coordinates: Latitude {lat}, Longitude {lng}")
                previous_lat, previous_lng = lat, lng  # Update the previous coordinates
                
            return lat, lng
        except ValueError:
            print("Invalid GPS coordinates. Please enter valid latitude and longitude values.")
            return None
    else:
        try:
            # Retrieve GPS coordinates using Google's Geolocation API
            url = "https://www.googleapis.com/geolocation/v1/geolocate"
            payload = {"considerIp": True}
            headers = {"Content-Type": "application/json"}
            
            # Include your Google Maps API Key
            params = {"key": GOOGLE_MAPS_API_KEY}
            response = requests.post(url, json=payload, params=params)

            if response.status_code == 200:
                data = response.json()
                lat = data['location']['lat']
                lng = data['location']['lng']
                
                if lat != previous_lat or lng != previous_lng:
                    print(f"Retrieved GPS coordinates: Latitude {lat}, Longitude {lng}")
                    previous_lat, previous_lng = lat, lng  # Update the previous coordinates
                    
                return lat, lng
            else:
                print(f"Error with Google Geolocation API: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            print(f"Error retrieving location: {e}")
            return None



def get_location_details(lat, lng):
    """
    Retrieve detailed address information for the provided latitude and longitude using Google Maps API.
    """
    try:
        reverse_geocode_result = gmaps.reverse_geocode((lat, lng))
        if reverse_geocode_result:
            return reverse_geocode_result[0]['formatted_address']
        return "Unknown Location"
    except Exception as e:
        print(f"Error with Google Maps API: {e}")
        return "Unknown Location"

def calculate_target_coordinates(drone_coords, distance, bearing):
    """
    Calculate target GPS coordinates based on starting point (drone_coords),
    distance (in meters), and bearing (in degrees).
    """
    try:
        origin = Point(latitude=drone_coords[0], longitude=drone_coords[1])
        # Convert distance from meters to kilometers
        distance_km = distance / 1000.0
        # Calculate the destination point
        destination = geodesic(kilometers=distance_km).destination(origin, bearing)
        return destination.latitude, destination.longitude
    except Exception as e:
        print(f"Error calculating target coordinates: {e}")
        return drone_coords  # Return original coordinates on error


def generate_google_maps_link(lat, lng):
    return f"https://www.google.com/maps?q={lat},{lng}"

def send_email(drone_coords, target_coords=None):
    recipient = "uploadanythingua2@gmail.com"
    subject = "Explosion Detected!"
    if target_coords:
        body = (f"An explosion has been detected at:\n"
                f"Latitude: {target_coords['latitude']}\n"
                f"Longitude: {target_coords['longitude']}\n"
                f"Address: {target_coords['address']}\n"
                f"Google Maps: {generate_google_maps_link(target_coords['latitude'], target_coords['longitude'])}")
    else:
        body = f"An explosion has been detected at the following GPS coordinates: {drone_coords}"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Multi-event handling variables
last_alert_time = 0
cooldown_period = 60  # seconds

# Camera specifications
camera_fov_horizontal = 96   # degrees
camera_fov_vertical = 73   # degrees

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame. Exiting...")
        break

    # Get the GPS coordinates in real-time
    drone_coords = get_gps_coordinates()

    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, score_threshold=0.5, nms_threshold=0.3)

    if len(indexes) > 0:
        indexes = indexes.flatten() if isinstance(indexes, np.ndarray) else indexes
        for i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 5)
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 3, text_color, 3)

            if drone_coords:
                # Calculate explosion-specific coordinates
                box_center_x = x + w / 2
                box_center_y = y + h / 2
                horizontal_angle = ((box_center_x / width) - 0.5) * camera_fov_horizontal
                vertical_angle = ((box_center_y / height) - 0.5) * camera_fov_vertical
                distance = 100  # Example value
                explosion_lat, explosion_lng = calculate_target_coordinates(drone_coords, distance, horizontal_angle)

                # Display GPS coordinates on the detection box
                gps_text = f"Lat: {explosion_lat:.6f}, Lng: {explosion_lng:.6f}"
                cv2.putText(frame, gps_text, (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
                current_time = time.time()
                
        if current_time - last_alert_time > cooldown_period:
            if drone_coords:
                box_center_x = boxes[indexes[0]][0] + boxes[indexes[0]][2] / 2
                box_center_y = boxes[indexes[0]][1] + boxes[indexes[0]][3] / 2
                horizontal_angle = ((box_center_x / width) - 0.5) * camera_fov_horizontal
                vertical_angle = ((box_center_y / height) - 0.5) * camera_fov_vertical
                distance = 100  # Example value
                target_lat, target_lng = calculate_target_coordinates(drone_coords, distance, horizontal_angle)
                target_coords = {
                    "latitude": target_lat,
                    "longitude": target_lng,
                    "address": get_location_details(target_lat, target_lng)
                }
                send_email(drone_coords, target_coords)
            else:
                print("Unable to retrieve GPS coordinates.")
            last_alert_time = current_time

    # Display real-time GPS coordinates on the video feed
    if drone_coords:
        gps_text = f"GPS: Lat {drone_coords[0]:.6f}, Lng {drone_coords[1]:.6f}"
    else:
        gps_text = "GPS: Unable to retrieve coordinates"
    cv2.putText(frame, gps_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)

    cv2.imshow("Real-Time Detection", frame)
    
    # Check for termination key
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:  # 'q' or 'ESC' key
        print("Termination key pressed. Exiting...")
        break
    
# Function to map cursor position to GPS coordinates
from geopy.distance import geodesic
from geopy.point import Point
import math

def map_cursor_to_gps(cursor_x, cursor_y, drone_coords, frame_width, frame_height, image_width, image_height, 
                      camera_fov_horizontal, camera_fov_vertical, camera_altitude, pitch_angle, roll_angle, yaw_angle, 
                      prev_cursor=None):
    """
    Map the cursor position to GPS coordinates considering camera orientation, altitude, and image dimensions.
    Args:
        cursor_x, cursor_y (float): Cursor's x and y position on the display.
        drone_coords (tuple): GPS coordinates (latitude, longitude) of the drone.
        frame_width, frame_height (int): Display dimensions of the camera feed.
        image_width, image_height (int): Actual dimensions of the captured image (used for scaling).
        camera_fov_horizontal, camera_fov_vertical (float): Camera field of view angles in degrees.
        camera_altitude (float): Camera's altitude above ground in meters.
        pitch_angle, roll_angle, yaw_angle (float): Camera's orientation angles in degrees.
        prev_cursor (tuple, optional): Previous cursor coordinates to avoid redundant processing.

    Returns:
        tuple: GPS coordinates (latitude, longitude) of the mapped cursor position.
    """
    try:
        # Skip processing if the cursor hasn't moved significantly
        if prev_cursor:
            prev_x, prev_y = prev_cursor
            if abs(cursor_x - prev_x) < 2 and abs(cursor_y - prev_y) < 2:  # Threshold for movement
                return None

        # Precompute frequently used constants
        camera_fov_horizontal = math.radians(camera_fov_horizontal)
        camera_fov_vertical = math.radians(camera_fov_vertical)
        pitch_angle = math.radians(pitch_angle)
        roll_angle = math.radians(roll_angle)
        yaw_angle = math.radians(yaw_angle)

        # Adjust cursor position based on actual image resolution
        adjusted_cursor_x = cursor_x * (image_width / frame_width)
        adjusted_cursor_y = cursor_y * (image_height / frame_height)

        # Normalize adjusted cursor position relative to the frame
        normalized_x = (adjusted_cursor_x / image_width) - 0.5  # Range: [-0.5, 0.5]
        normalized_y = (adjusted_cursor_y / image_height) - 0.5  # Range: [-0.5, 0.5]

        # Calculate angles based on the cursor's position
        horizontal_angle = normalized_x * camera_fov_horizontal + yaw_angle
        vertical_angle = normalized_y * camera_fov_vertical + pitch_angle

        # Avoid invalid tan() values
        if abs(vertical_angle) < 1e-5:  # Avoid division by zero
            vertical_angle = 1e-5

        # Calculate the projected distance on the ground
        ground_distance = camera_altitude / math.tan(vertical_angle)

        # Convert distance and angle to GPS coordinates
        origin = Point(latitude=drone_coords[0], longitude=drone_coords[1])
        destination = geodesic(kilometers=ground_distance / 1000.0).destination(origin, math.degrees(horizontal_angle))

        return destination.latitude, destination.longitude

    except Exception as e:
        print(f"Error calculating cursor GPS coordinates: {e}")
        return drone_coords  # Return original coordinates on error


# Mouse callback function
def on_mouse_event(event, x, y, flags, param):
    global cursor_coords
    if event == cv2.EVENT_MOUSEMOVE:
        cursor_coords = (x, y)


# Initialize mouse event handling
cursor_coords = None
cv2.namedWindow("Real-Time Detection")
cv2.setMouseCallback("Real-Time Detection", on_mouse_event)

# Example camera orientation and altitude values
camera_altitude = 7.4676  # in meters
pitch_angle = 60  # in degrees
roll_angle = 0  # assuming no roll
yaw_angle = 90  # assuming the camera faces north
image_width = 1920  # in pixels
image_height = 1080  # in pixels

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame. Exiting...")
        break

    # Get the GPS coordinates in real-time
    drone_coords = get_gps_coordinates()

    height, width, _ = frame.shape

    # Display cursor GPS coordinates if available
    if cursor_coords and drone_coords:
        cursor_x, cursor_y = cursor_coords
        cursor_lat, cursor_lng = map_cursor_to_gps(
            cursor_x, cursor_y, drone_coords, width, height,
            image_width, image_height,
            camera_fov_horizontal, camera_fov_vertical,
            camera_altitude, pitch_angle, roll_angle, yaw_angle
        )
        cursor_text = f"Cursor: Lat {cursor_lat:.6f}, Lng {cursor_lng:.6f}"
        cv2.putText(frame, cursor_text, (cursor_x + 10, cursor_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.circle(frame, (cursor_x, cursor_y), 5, (0, 255, 0), -1)

    # Display the frame
    cv2.imshow("Real-Time Detection", frame)

    # Check for termination key
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:  # 'q' or 'ESC' key
        print("Termination key pressed. Exiting...")
        break

cap.release()
cv2.destroyAllWindows()
