import math
from geopy.distance import geodesic
from geopy.point import Point


def map_cursor_to_gps(
    cursor_x,
    cursor_y,
    drone_coords,
    frame_width,
    frame_height,
    image_width,
    image_height,
    camera_fov_horizontal,
    camera_fov_vertical,
    camera_altitude,
    pitch_angle,
    roll_angle,
    yaw_angle,
):
    try:
        camera_fov_horizontal = math.radians(camera_fov_horizontal)
        camera_fov_vertical = math.radians(camera_fov_vertical)
        pitch_angle = math.radians(pitch_angle)
        roll_angle = math.radians(roll_angle)
        yaw_angle = math.radians(yaw_angle)

        adjusted_cursor_x = cursor_x * (image_width / frame_width)
        adjusted_cursor_y = cursor_y * (image_height / frame_height)

        normalized_x = (adjusted_cursor_x / image_width) - 0.5
        normalized_y = (adjusted_cursor_y / image_height) - 0.5

        horizontal_angle = normalized_x * camera_fov_horizontal + yaw_angle
        vertical_angle = normalized_y * camera_fov_vertical + pitch_angle

        if abs(vertical_angle) < 1e-5:
            vertical_angle = 1e-5

        ground_distance = camera_altitude / math.tan(vertical_angle)
        origin = Point(latitude=drone_coords[0], longitude=drone_coords[1])
        destination = geodesic(kilometers=ground_distance / 1000.0).destination(
            origin,
            math.degrees(horizontal_angle),
        )

        return destination.latitude, destination.longitude
    except Exception:
        return drone_coords
