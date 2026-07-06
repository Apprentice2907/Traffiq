import cv2
import argparse
import sys

# Global variables to store points
points = []
slots = []
image = None
clone = None

def click_and_crop(event, x, y, flags, param):
    global points, slots, image, clone

    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))

        # If we have two points, draw a rectangle and save the coordinates
        if len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]
            
            # Ensure proper ordering
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)
            
            slots.append([x_min, y_min, x_max, y_max])
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.imshow("Image", image)
            
            print(f"Slot {len(slots)}: ({x_min}, {y_min}, {x_max}, {y_max})")
            points = []

def main():
    global image, clone
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to the image")
    args = parser.parse_args()

    image = cv2.imread(args.image)
    if image is None:
        print(f"Error: Could not load image at {args.image}")
        sys.exit(1)

    clone = image.copy()
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", click_and_crop)

    print(f"Loaded {args.image}")
    print("Click two points (top-left, bottom-right) to define a slot.")
    print("Press 'q' when done.")

    while True:
        cv2.imshow("Image", image)
        key = cv2.waitKey(1) & 0xFF

        # if the 'r' key is pressed, reset the cropping region
        if key == ord("r"):
            image = clone.copy()
            slots.clear()
            points = []
            print("Resetting all slots.")
            
        # if the 'q' key is pressed, break from the loop
        elif key == ord("q"):
            break

    cv2.destroyAllWindows()
    
    print("\n--- Final Python List of Slots ---")
    
    formatted_slots = []
    for i, s in enumerate(slots, 1):
        formatted_slots.append(f'        {{"slot_id": {i}, "coords": {s}}}')
    
    final_output = "[\n" + ",\n".join(formatted_slots) + "\n    ]"
    print(final_output)

if __name__ == "__main__":
    main()
