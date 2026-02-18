import matplotlib.pyplot as plt
import numpy as np
import cv2
import json
import time

def CaptureImg(save_path="output/captured_img.png", camera_index=1):
    # Open camera
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None

    # Give camera a short time to adjust/expose
    time.sleep(0.5)

    # Capture one frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        cap.release()
        return None

    # Show the captured frame (optional)
    cv2.imshow("Captured Image", frame)
    cv2.waitKey(500)  # display for 0.5 second

    # Save the image automatically
    cv2.imwrite(save_path, frame)
    print(f"Image saved as {save_path}")

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    return frame
    
def load_H_Matrix():
    with open("output/H_matrix.json", "r") as f:
        H = np.array(json.load(f))
    return H   

def save_image(image):
   cv2.imshow("Image", image)
   cv2.imwrite("output/Markdown_Image.png", image)
   cv2.waitKey(1500)
   cv2.destroyAllWindows()

def pixel_to_robot(u, v, H):

    p = np.array([u, v, 1.0], dtype=np.float32).reshape(3, 1)
    pr = H @ p
    pr = pr / pr[2, 0] 
    X = pr[0, 0]
    Y = pr[1, 0]
    return X, Y

def filter_image(img): 
   T = 120
   _, bin_img = cv2.threshold(img, T, 255, cv2.THRESH_BINARY_INV)

   kernel = np.ones((10, 10), np.uint8)
   closing = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, kernel)
   kernel = np.ones((3, 3), np.uint8)
   return cv2.erode(closing, kernel, iterations=6)

def object_detection(img,H,img_clr):
   eroded = filter_image(img)
   data = {}  # Dictionary to store JSON data 
   num_labels, labeled_img, stats, centroids = cv2.connectedComponentsWithStats(eroded, connectivity=4, ltype=cv2.CV_32S)

   # Draw Centroids
   for i, (cx, cy) in enumerate(centroids[1:], start=1):
      cx, cy = int(cx), int(cy)
      X, Y = pixel_to_robot(cx, cy, H)
      # print(f'Centroid: ({cx},{cy})')

      cv2.circle(img_clr, (cx,cy), 2, (191,40,0), 2)
      cv2.putText(img_clr, f"({cx},{cy}) => ({X:.2f}, {Y:.2f})" , (cx-40, cy-15),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 125), 1, cv2.LINE_AA)

      # Store in dictionary
      point_name = f"P{i}"
      data[point_name] = {
            "X": float(X),
            "Y": float(Y),
            "cx": cx,
            "cy": cy
        }
   # Save to JSON file
   with open("output/centroids_data.json", "w") as f:
      json.dump(data, f, indent=4)
      
   return img_clr


def main():
    print("Running Object detection module...")
    #CaptureImg('output/captured_img.png',1)

    # img = cv2.imread("./output/captured_img.png")
    img_clr = cv2.imread('./output/captured_img.png')
    img = cv2.cvtColor(img_clr, cv2.COLOR_BGR2GRAY)

    H = load_H_Matrix()

    img_clr = object_detection(img,H,img_clr)

    save_image(img_clr)

if __name__ == "__main__":
    main()