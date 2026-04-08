import time

import cv2

from impact_system.alert_service import EmailAlertService
from impact_system.config import (
    AppConfig,
    CLASS_NAMES,
    WINDOW_NAME,
    YOLO_CFG_PATH,
    YOLO_WEIGHTS_PATH,
)
from impact_system.cursor_mapper import map_cursor_to_gps
from impact_system.detector import YoloExplosionDetector
from impact_system.gps_service import GPSService


def select_location_source():
    print("Select location source:")
    print("1. PC's Location (IP-based)")
    print("2. Drone's GPS Coordinates")
    return input("Enter your choice (1/2): ").strip()


def select_camera():
    print("Select input source:")
    print("1. Physical Camera (Default webcam)")
    print("2. OBS Virtual Camera")
    choice = input("Enter your choice (1/2): ").strip()

    if choice == "1":
        cap = cv2.VideoCapture(0)
    elif choice == "2":
        virtual_cam_index = input(
            "Enter the camera index for OBS Virtual Camera (usually 1 or higher): "
        ).strip()
        cap = cv2.VideoCapture(int(virtual_cam_index))
    else:
        raise ValueError("Invalid camera selection")

    if not cap.isOpened():
        raise RuntimeError("Could not open selected camera")
    return cap


def run_detection_system():
    config = AppConfig()
    location_choice = select_location_source()

    detector = YoloExplosionDetector(
        cfg_path=YOLO_CFG_PATH,
        weights_path=YOLO_WEIGHTS_PATH,
        class_names=CLASS_NAMES,
        conf_threshold=config.detection_conf_threshold,
        nms_threshold=config.detection_nms_threshold,
    )
    gps_service = GPSService(
        location_choice=location_choice,
        google_maps_api_key=config.google_maps_api_key,
        cache_seconds=config.gps_cache_seconds,
        static_coords=(config.static_drone_lat, config.static_drone_lng),
    )
    alert_service = EmailAlertService(
        smtp_server=config.smtp_server,
        smtp_port=config.smtp_port,
        sender=config.email_sender,
        password=config.email_password,
        recipient=config.email_recipient,
    )

    cap = select_camera()
    cursor_position = {"xy": None}
    last_alert_time = 0.0

    def on_mouse_event(event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            cursor_position["xy"] = (x, y)

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse_event)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame. Exiting...")
                break

            frame_height, frame_width, _ = frame.shape
            drone_coords = gps_service.get_coordinates()
            detections = detector.detect(frame)
            now = time.time()

            for detection in detections:
                x, y, w, h = (
                    detection.x,
                    detection.y,
                    detection.width,
                    detection.height,
                )
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 3)
                cv2.putText(
                    frame,
                    CLASS_NAMES[detection.class_id],
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                )

                if drone_coords:
                    center_x = x + w / 2
                    horizontal_angle = ((center_x / frame_width) - 0.5) * config.camera_fov_horizontal
                    target_lat, target_lng = gps_service.calculate_target_coordinates(
                        drone_coords,
                        config.assumed_target_distance_m,
                        horizontal_angle,
                    )
                    cv2.putText(
                        frame,
                        f"Lat: {target_lat:.6f}, Lng: {target_lng:.6f}",
                        (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 255, 255),
                        2,
                    )

            if detections and drone_coords and (now - last_alert_time > config.alert_cooldown_seconds):
                first = detections[0]
                center_x = first.x + first.width / 2
                horizontal_angle = ((center_x / frame_width) - 0.5) * config.camera_fov_horizontal
                target_lat, target_lng = gps_service.calculate_target_coordinates(
                    drone_coords,
                    config.assumed_target_distance_m,
                    horizontal_angle,
                )
                target_coords = {
                    "latitude": target_lat,
                    "longitude": target_lng,
                    "address": gps_service.get_location_details(target_lat, target_lng),
                }
                alert_service.send_explosion_alert(
                    gps_service.generate_google_maps_link,
                    drone_coords,
                    target_coords,
                )
                last_alert_time = now

            gps_text = (
                f"GPS: Lat {drone_coords[0]:.6f}, Lng {drone_coords[1]:.6f}"
                if drone_coords
                else "GPS: Unable to retrieve coordinates"
            )
            cv2.putText(
                frame,
                gps_text,
                (10, frame_height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            if cursor_position["xy"] and drone_coords:
                cursor_x, cursor_y = cursor_position["xy"]
                cursor_lat, cursor_lng = map_cursor_to_gps(
                    cursor_x,
                    cursor_y,
                    drone_coords,
                    frame_width,
                    frame_height,
                    config.image_width,
                    config.image_height,
                    config.camera_fov_horizontal,
                    config.camera_fov_vertical,
                    config.camera_altitude_m,
                    config.pitch_angle_deg,
                    config.roll_angle_deg,
                    config.yaw_angle_deg,
                )
                cv2.putText(
                    frame,
                    f"Cursor: Lat {cursor_lat:.6f}, Lng {cursor_lng:.6f}",
                    (cursor_x + 10, cursor_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                )
                cv2.circle(frame, (cursor_x, cursor_y), 4, (0, 255, 0), -1)

            cv2.imshow(WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                print("Termination key pressed. Exiting...")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
