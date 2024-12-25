import cv2
import socket
import ipaddress
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Configuration
IP_RANGE = "192.168.1.0/24"
RTSP_PORT = 8554
USERNAME = "admin"
PASSWORD = "admin"
RTSP_PATH = "/Streaming/Channels/101"


def scan_ip(ip):
    """Scan the network to find cameras with open RTSP ports."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex((str(ip), RTSP_PORT))
    sock.close()
    return str(ip) if result == 0 else None


def find_cameras():
    """Find cameras on the network."""
    print("Scanning network for cameras...")
    network = ipaddress.ip_network(IP_RANGE)
    with ThreadPoolExecutor(max_workers=100) as executor:
        cameras = list(filter(None, executor.map(scan_ip, network.hosts())))
    print(f"Found {len(cameras)} cameras.")
    return cameras


def display_and_save_stream(ip, output_dir, duration_minutes):
    """Display the CCTV stream and save using FFmpeg."""
    rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@{ip}:{RTSP_PORT}{RTSP_PATH}"
    output_file = os.path.join(output_dir, f"{ip.replace('.', '_')}.mp4")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Convert duration to seconds
    duration_seconds = duration_minutes * 60

    # FFmpeg command to display and save the stream
    ffmpeg_command = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-map", "0:v:0",  # Map only the first video stream for display
        "-f", "sdl", "RTSP Stream",  # Display the stream
        "-t", str(duration_seconds),  # Recording duration
        "-c:v", "libx265",  # Save with H.265 encoding
        "-preset", "faster",  # Faster preset
        "-crf", "23",  # Quality factor
        "-an",  # Disable audio
        "-movflags", "+faststart",
        output_file
    ]

    print(f"Saving stream to {output_file} and displaying...")
    subprocess.run(ffmpeg_command)
    print(f"Stream saved to {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CCTV Network Scanner and Stream Viewer using FFmpeg")
    parser.add_argument(
        "--ip", type=str, default="all", help="IP address to view or 'all' to list available cameras"
    )
    parser.add_argument(
        "--output_dir", type=str, default="output", help="Directory to save output videos"
    )
    parser.add_argument(
        "--duration", type=int, default=5, help="Duration to save the stream (in minutes)"
    )
    args = parser.parse_args()

    if args.ip == "all":
        cameras = find_cameras()
        print("Available Cameras:")
        for idx, camera_ip in enumerate(cameras, 1):
            print(f"{idx}. {camera_ip}")
        selected = int(input("Select a camera to display (enter the number): "))
        selected_ip = cameras[selected - 1]
        display_and_save_stream(selected_ip, args.output_dir, args.duration)
    else:
        display_and_save_stream(args.ip, args.output_dir, args.duration)
