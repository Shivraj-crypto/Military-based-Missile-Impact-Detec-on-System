from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class AppConfig:
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    email_sender: str = os.getenv("EMAIL_ADDRESS", "aairconfisys@gmail.com")
    email_password: str = os.getenv("EMAIL_PASSWORD", "nsya zbgo cyqx bxjj")
    email_recipient: str = os.getenv("EMAIL_RECIPIENT", "uploadanythingua2@gmail.com")

    camera_fov_horizontal: float = 96.0
    camera_fov_vertical: float = 73.0
    camera_altitude_m: float = 7.4676
    pitch_angle_deg: float = 60.0
    roll_angle_deg: float = 0.0
    yaw_angle_deg: float = 90.0

    image_width: int = 1920
    image_height: int = 1080

    detection_conf_threshold: float = 0.5
    detection_nms_threshold: float = 0.3
    alert_cooldown_seconds: int = 60
    gps_cache_seconds: int = 2
    assumed_target_distance_m: float = 100.0

    static_drone_lat: float = 19.230154
    static_drone_lng: float = 72.839063


PROJECT_ROOT = Path(__file__).resolve().parent.parent
YOLO_CFG_PATH = Path(os.getenv("YOLO_CFG_PATH", str(PROJECT_ROOT / "yolov3_testing.cfg")))
YOLO_WEIGHTS_PATH = Path(
    os.getenv("YOLO_WEIGHTS_PATH", str(PROJECT_ROOT / "yolov3_training_last.weights"))
)
CLASS_NAMES = ["Explosion"]
WINDOW_NAME = "Real-Time Detection"
