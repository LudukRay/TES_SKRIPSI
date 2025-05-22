import socket
import time

# Definisi IP dan port untuk koneksi ke server lengan robot
PI_IP        = "192.168.63.108"
PUBLISH_PORT = 9001
OUTPUT_FILE  = "robot_coordinates_z.txt"

# Fungsi untuk koneksi secara terus - menerus ke server lengan robot setiap dua detik 
def connect_and_log():
    sock = None
    while sock is None:
        try:
            sock = socket.create_connection((PI_IP, PUBLISH_PORT), timeout=2)
            print("Connected to telemetry server!")
        except (ConnectionRefusedError, socket.timeout):
            print("No server yet… retrying in 2 s")
            time.sleep(2)

    sock.settimeout(None)

    # Proses perekaman data koordinat dari lengan robot berjalan 
    with sock.makefile('r') as stream, open(OUTPUT_FILE, "a") as f:
        for line in stream:  
            if not line:
                print("Server closed the connection")
                break
            f.write(line)
            print("COORDINATE RECEIVED")

if __name__ == "__main__":  
    connect_and_log()