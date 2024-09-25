import cv2
import cv2.aruco as aruco
import numpy as np
import serial
import time

# Load ArUco dictionary
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)

# Open serial port
ser = serial.Serial('/dev/ttyUSB0', 115200)  # Change '/dev/ttyUSB0' to your serial port name

# Create video capture object
cap = cv2.VideoCapture(0)  # Change 0 to the camera index if using multiple cameras

# Initialize variables to keep track of marker ID 4 and 5 presence and toggle
marker_4_present = False
marker_5_present = False
toggle_4 = False
toggle_5 = False

# Load image to display on marker
img_on_marker = cv2.imread('bulub.jpg')  # Replace 'your_image_path.jpg' with the path to your image

# Check if the image is loaded successfully
if img_on_marker is None:
    print("Error: Image not loaded.")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Check if frame is captured successfully
    if not ret:
        print("Error: Frame not captured.")
        continue

    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect markers
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict)

    # Draw detected markers
    if ids is not None:
        aruco.drawDetectedMarkers(frame, corners, ids)
    
    # Check if marker ID 4 is detected
    if ids is not None and 4 in ids:
        if not marker_4_present:
            if toggle_4:
                print("Marker with ID 4 brought back into frame. Sending character 'a' serially.")
                ser.write(b'b')  # Send character 'a' as bytes
                time.sleep(3)

            else:
                print("Marker with ID 4 detected. Sending character '0' serially.")
                ser.write(b'1')  # Send character '0' as bytes
                time.sleep(3)
            toggle_4 = not toggle_4
        marker_4_present = True
        # Overlay image on marker
        for i in range(len(ids)):
            if ids[i] == 4:
                # Assuming a fixed size for the marker
                marker_size = 100
                marker_corners = np.squeeze(corners[i])
                # Calculate the center of the marker
                marker_center = np.mean(marker_corners, axis=0)
                # Calculate the top-left corner of the image to overlay
                img_x = int(marker_center[0] - marker_size / 2)
                img_y = int(marker_center[1] - marker_size / 2)
                # Check if image dimensions are valid before resizing
                if img_on_marker.shape[0] > 0 and img_on_marker.shape[1] > 0:
                    # Overlay the image onto the frame
                    frame[img_y:img_y+marker_size, img_x:img_x+marker_size] = cv2.resize(img_on_marker, (marker_size, marker_size))
                else:
                    print("Error: Image dimensions are invalid.")
        
    else:
        marker_4_present = False
    
    # Check if marker ID 5 is detected
    if ids is not None and 5 in ids:
        if not marker_5_present:
            if toggle_5:
                print("Marker with ID 5 brought back into frame. Sending character 'a' serially.")
                ser.write(b'a')  # Send character 'a' as bytes
            else:
                print("Marker with ID 5 detected. Sending character '0' serially.")
                ser.write(b'0')  # Send character '0' as bytes
            toggle_5 = not toggle_5
        marker_5_present = True
        # Overlay image on marker
        for i in range(len(ids)):
            if ids[i] == 5:
                # Assuming a fixed size for the marker
                marker_size = 100
                marker_corners = np.squeeze(corners[i])
                # Calculate the center of the marker
                marker_center = np.mean(marker_corners, axis=0)
                # Calculate the top-left corner of the image to overlay
                img_x = int(marker_center[0] - marker_size / 2)
                img_y = int(marker_center[1] - marker_size / 2)
                # Check if image dimensions are valid before resizing
                if img_on_marker.shape[0] > 0 and img_on_marker.shape[1] > 0:
                    # Overlay the image onto the frame
                    frame[img_y:img_y+marker_size, img_x:img_x+marker_size] = cv2.resize(img_on_marker, (marker_size, marker_size))
                else:
                    print("Error: Image dimensions are invalid.")
    else:
        marker_5_present = False
    
    # Display the resulting frame
    cv2.imshow('frame', frame)

    # Check for exit key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture object
cap.release()

# Close serial port
ser.close()

# Close all OpenCV windows
cv2.destroyAllWindows()
