import cv2
import json
import os
import argparse
from ultralytics import YOLO

# COCO classes: 2: car, 5: bus, 7: truck
VEHICLE_CLASSES = [2, 5, 7]

def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0
    
    boxAArea = max(0, boxA[2] - boxA[0]) * max(0, boxA[3] - boxA[1])
    boxBArea = max(0, boxB[2] - boxB[0]) * max(0, boxB[3] - boxB[1])

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def main(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} not found.")
        return

    # Load YOLOv8n model
    model = YOLO('yolov8n.pt')
    
    # Run inference
    results = model(image_path)
    
    # Get detected vehicle boxes
    vehicle_boxes = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            if cls in VEHICLE_CLASSES:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                vehicle_boxes.append([x1, y1, x2, y2])
                
    # Define placeholder parking slots (x1, y1, x2, y2)
    # These will be updated by the user later
    slots = [
        {"slot_id": 1, "coords": [9, 312, 327, 552]},
        {"slot_id": 2, "coords": [465, 274, 523, 322]},
        {"slot_id": 3, "coords": [676, 286, 787, 454]},
        {"slot_id": 4, "coords": [547, 269, 653, 365]},
        {"slot_id": 5, "coords": [400, 450, 600, 550]},
        {"slot_id": 6, "coords": [350, 380, 500, 430]}
    ]
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}")
        return
        
    output_data = []
    
    for slot in slots:
        slot_coords = slot["coords"]
        is_occupied = False
        
        for v_box in vehicle_boxes:
            iou = calculate_iou(slot_coords, v_box)
            if iou > 0.3:
                is_occupied = True
                break
                
        status = "occupied" if is_occupied else "empty"
        output_data.append({"slot_id": slot["slot_id"], "status": status})
        
        # Draw slot box
        color = (0, 0, 255) if is_occupied else (0, 255, 0) # BGR: Red if occupied, Green if empty
        cv2.rectangle(image, (slot_coords[0], slot_coords[1]), (slot_coords[2], slot_coords[3]), color, 2)
        cv2.putText(image, f'Slot {slot["slot_id"]}', (slot_coords[0] + 5, slot_coords[1] + 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Draw vehicle boxes
    for v_box in vehicle_boxes:
        cv2.rectangle(image, (v_box[0], v_box[1]), (v_box[2], v_box[3]), (255, 0, 0), 1)
        cv2.putText(image, 'Vehicle', (v_box[0], v_box[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    # Ensure output directory exists
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, f"annotated_{base_name}")
    cv2.imwrite(output_path, image)
    
    print(json.dumps(output_data, indent=2))
    print(f"Annotated image saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Default to the path specified by the user
    default_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_street.jpg"))
    parser.add_argument("--image", type=str, default=default_img, help="Path to input image")
    args = parser.parse_args()
    
    main(args.image)
