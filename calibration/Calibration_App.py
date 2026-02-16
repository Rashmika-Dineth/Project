import json
import cv2
import numpy as np


# Store H Matrix
hmatrix = []

def CaptureImg():
    # Open default camera (0 = built-in webcam)
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()

    print("Press SPACE to capture image")
    print("Press ESC to exit")

    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1)

        # Press SPACE to capture
        if key % 256 == 32:
            cv2.imwrite("output/captured_img.png", frame)
            print("Image saved as captured_img.png")

        # Press ESC to exit
        elif key % 256 == 27:
            print("Closing camera")
            break

    cap.release()
    cv2.destroyAllWindows()

def Save_H_Matrix(H):
    with open("output/H_matrix.json", "w") as f:
        json.dump(H.tolist(), f, indent=4)
    print("Homography matrix saved to H_matrix.json")

def click_event(event, x, y, flags, param):
    global hmatrix
    
    if event == cv2.EVENT_LBUTTONDOWN and len(hmatrix) < 4:
        hmatrix.append([x, y])
        print(f"Image Point {len(hmatrix)}: ({x}, {y})")
        
        cv2.circle(img, (x, y), 5, (0, 0, 255), -1)
        cv2.imshow("Image", img)

        if len(hmatrix) == 4:
            cv2.destroyAllWindows()

def Generate_H_Matrix(img_pts):
    robot_pts = []

    print("\nEnter 4 Robot Points (X Y):")
    for i in range(4):
        x = float(input(f"Robot Point {i+1} - X: "))
        y = float(input(f"Robot Point {i+1} - Y: "))
        robot_pts.append([x, y])

    robot_pts = np.array(robot_pts, dtype=np.float32)
    img_pts = np.array(img_pts, dtype=np.float32)

    # Compute homography
    H, mask = cv2.findHomography(img_pts, robot_pts)

    print("\nHomography Matrix H:")
    print(H)

    Save_H_Matrix(H)

# -----------------------------
# Main Program
# -----------------------------

CaptureImg()
img = cv2.imread("./output/captured_img.png")
cv2.imshow("Image", img)
cv2.setMouseCallback("Image", click_event)

cv2.waitKey(0)
cv2.destroyAllWindows()

print("\nCollected Image Points:")
print(hmatrix)

if len(hmatrix) == 4:
    Generate_H_Matrix(hmatrix)
else:
    print("Error: You must select exactly 4 points.")
