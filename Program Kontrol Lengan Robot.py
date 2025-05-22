from pymycobot.mycobot import MyCobot
from pymycobot.genre import Angle
from pymycobot import MyCobot280
import os
from pymycobot import PI_PORT, PI_BAUD      # When using the Raspberry Pi version of mycobot, you can refer to these two variables to initialize MyCobot, if not, you can omit this line of code
import time
from pymycobot.mypalletizer import MyPalletizer
from pymycobot.genre import Coord
from pymycobot import MyCobotSocket
import cv2 as cv
import threading
from datetime import datetime
import queue
import asyncio
import serial_asyncio 
import socket

# COMMAND_IP = "10.16.124.79"
COMMAND_IP = "10.16.126.254"
COMMAND_PORT = 9000
PUBLISH_IP = "0.0.0.0"
PUBLISH_PORT = 9001
POLL_INTERVAL = 0.02

# Use port 9000 by default
# mc = MyCobotSocket("172.16.213.98",9000)
# mc = MyCobotSocket("192.168.63.108",9000)
# mc = MyCobotSocket("10.16.123.159",9000)
# Initiate MyCobot
# mc = MyCobot("/dev/ttyUSB0", 115200)
# mc = MyCobot("/dev/ttyAMA0", 115200) ALTERNATIVE
mc = MyCobotSocket(COMMAND_IP,COMMAND_PORT) 

clients = []
clients_lock = threading.Lock()
running = False
pub_thread = None
list_coordinate = []
list_angles = []
mode = 0
speed = 20

def telemetry_server():
    print("Server started")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((PUBLISH_IP,PUBLISH_PORT))
    srv.listen()
    while True:
        conn, addr = srv.accept()
        # print(f"CLIENT CONNECTED: {addr}")
        with clients_lock:
            clients.append(conn)

def telemetry_publisher():
    global running
    try:
        while running:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            coords = mc.get_coords()
            line = f"{ts} - Current Coordinate: {coords}\n"
            data = line.encode("utf-8")
            with clients_lock:
                # print(f"Publish to {len(clients)} client(s)",flush=True)
                for conn in clients[:]:
                    conn.sendall(data)
            time.sleep(POLL_INTERVAL)

    except Exception:
        import traceback
        traceback.print_exc()
        print("PUBLISH DIED ON EXCEPTION", flush = True)

def capture_coordinates():
    start_time = time.time()
    while time.time() - start_time < 60:
        coord = mc.get_coords()  # Get coordinates from the robot
        # Format the coordinate as desired, e.g. (x, y, z, rx, ry, rz)
        list_coordinate = coord
        print(f"\nCurrent Coordinate (x,y,z,rx,ry,rz) : {list_coordinate}")
        time.sleep(1)  # Wait 1 second

def capture_angles():
    start_time = time.time()
    while time.time() - start_time < 20:
        angles = mc.get_angles()  # Get coordinates from the robot
        # Format the coordinate as desired, e.g. (x, y, z, rx, ry, rz)
        list_angles = angles
        print(f"\nCurrent Angles (j1,j2,j3,j4,j5,j6) : {list_angles}")
        time.sleep(0.1)  # Wait 1 second

def display_menu():
    print(f"\nCurrent Coordinate (x,y,z,rx,ry,rz) : {list_coordinate} ")
    print(f"Current Angles (j1,j2,j3,j4,j5,j6) : {list_angles} ")
    print("===== Main Menu =====")
    print("1. release all servo")
    print("2. pause")
    print("3. resume")
    print("4. stop")
    print("5. set speed")
    print("6. get error")
    print("7. get angles")
    print("8. clear screen")
    print("9. get coords")
    print("10. send coords")
    print("11. get speed")
    print("12. send joint angles (degree)")
    print("13. tracking x,y,z")
    print("14. delete list")
    print("15. Move X axis")
    print("16. Move Y axis")
    print("17. Move Z axis")
    print("18. exit")
    print("=====================")

def get_user_choice():
    while True:
        try:
            choice = int(input("Enter your choice : "))
            if 1 <= choice <= 18:
                return choice
            else:
                print("Invalid choice. Please enter a number between 1 and 18.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

threading.Thread(target=telemetry_server,daemon=True).start()

def main():
    global list_coordinate, list_angles, speed, rx, ry, rz,recording
    try:
        while True:
            display_menu()
            choice = get_user_choice()
            if choice == 1:
                mc.release_all_servos()
            elif choice == 2:
                mc.pause()
            elif choice == 3:
                mc.resume()
            elif choice == 4:
                mc.stop()
            elif choice == 5:
                number = int(input("Enter a number to process 0-100 mm/s: "))
                mc.set_speed(number)
                speed = number
            elif choice == 6:
                print("Error no. = ", mc.get_error_information())
                print("0: no error message. 1 ~ 6: The corresponding joint exceeds the limit. 16 ~ 19: collision protection. 32: Kinematics inverse solution has no solution. 33 ~ 34: Linear motion has no adjacent solution.")
            elif choice == 7:
                # list_angles.append(mc.get_angles())
                capture_angles()
            elif choice == 8:
                os.system('cls' if os.name == 'nt' else 'clear')
            elif choice == 9:
                # list_coordinate.append(mc.get_coords())
                capture_coordinates()
            elif choice == 10:
                x = float(input("  x: "))
                y = float(input("  y: "))
                z = float(input("  z: "))
                rx = float(input("  rx: "))
                ry = float(input("  ry: "))
                rz = float(input("  rz: "))
                mc.send_coords([x,y,z,rx,ry,rz],speed,mode)
            elif choice == 11:  
                print("Speed = ", mc.get_speed())
            elif choice == 12:
                j1 = float(input("  j1: "))
                j2 = float(input("  j2: "))
                j3 = float(input("  j3: "))
                j4 = float(input("  j4: "))
                j5 = float(input("  j5: "))
                j6 = float(input("  j6: "))
                mc.send_angles([j1,j2,j3,j4,j5,j6],speed)
            elif choice == 13:
                break
            elif choice == 14:
                list_coordinate = []
                list_angles = []
            elif choice == 15:
                global running,pub_thread
                mc.send_angles([14.94, -54.14, -41.57, 65.47, -1.49, 35.15], speed)
                time.sleep(7)  
                running = True
                pub_thread = threading.Thread(target=telemetry_publisher, daemon = True)
                pub_thread.start()
                time.sleep(1) #giving time for thread
                mc.send_angles([25.83, 62.66, -133.15,  40.69, 6.06, 45.87], speed)
                time.sleep(5)
                running = False
                pub_thread.join()
            elif choice == 16:
                mc.send_angles([-7.38, 1.66, -119.0, 75.14, -5.36, 53.32], speed)
                time.sleep(7)  
                running = True
                pub_thread = threading.Thread(target=telemetry_publisher, daemon = True)
                pub_thread.start()
                time.sleep(1) #giving time for thread  
                mc.send_angles([40.42, -8.78, -113.81, 87.53, -0.96, 49.74], speed)
                time.sleep(5)
                running = False
                pub_thread.join()
            elif choice == 17:
                mc.send_angles([15.82, -67.07, -71.01, 106.61, 5.36, 64.77], speed)
                time.sleep(7)  
                running = True
                pub_thread = threading.Thread(target=telemetry_publisher, daemon = True)
                pub_thread.start()
                time.sleep(1) #giving time for thread
                mc.send_angles([17.13, -30.14, -28.82, 29.79, -5.62, 65.03], speed)
                time.sleep(5)
                running = False
                pub_thread.join()
            elif choice == 18:
                print("Exiting the program. Goodbye!")
                mc.release_all_servos()
                break
            
    except KeyboardInterrupt:
        mc.release_all_servos()

if _name_ == "_main_":
    main()