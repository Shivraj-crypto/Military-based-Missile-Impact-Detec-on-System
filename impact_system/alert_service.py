import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailAlertService:
    def __init__(self, smtp_server, smtp_port, sender, password, recipient):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender = sender
        self.password = password
        self.recipient = recipient

    def send_explosion_alert(self, maps_link_fn, drone_coords, target_coords=None):
        subject = "Explosion Detected!"
        if target_coords:
            body = (
                f"An explosion has been detected at:\n"
                f"Latitude: {target_coords['latitude']}\n"
                f"Longitude: {target_coords['longitude']}\n"
                f"Address: {target_coords['address']}\n"
                f"Google Maps: {maps_link_fn(target_coords['latitude'], target_coords['longitude'])}"
            )
        else:
            body = f"An explosion has been detected at the following GPS coordinates: {drone_coords}"

        msg = MIMEMultipart()
        msg["From"] = self.sender
        msg["To"] = self.recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.recipient, msg.as_string())
            print("Email sent successfully.")
        except Exception as exc:
            print(f"Failed to send email: {exc}")
