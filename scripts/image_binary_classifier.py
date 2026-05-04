try:
    import cv2
except ImportError:
    print("Error: OpenCV is not installed. Please install it using 'pip install opencv-python'.")
    sys.exit(1)

import sys
import os
import argparse

KEY_LEFT = 2424832
KEY_RIGHT = 2555904

def close_and_exit():
    cv2.destroyAllWindows()
    sys.exit()

def make_path(*args):
    return os.path.normpath(os.path.join(*args))

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Classify images into left and right categories, using arrow keys.")
    parser.add_argument("source", "s", help="Path to the directory containing images to classify")
    parser.add_argument("destination", "d", help="Path to the directory for classified images")
    parser.add_argument("left_name", default="LEFT", help="Name for the left category")
    parser.add_argument("right_name", default="RIGHT", help="Name for the right category")
    args = parser.parse_args()
    
    left_path = make_path(args.destination, args.left_name)
    right_path = make_path(args.destination, args.right_name)
    
    if not os.path.exists(left_path):
        os.makedirs(left_path)
    
    if not os.path.exists(right_path):
        os.makedirs(right_path)

    input_images = os.listdir(args.source)
    for i, image_name in enumerate(input_images):
        
        if (image_name.split('.')[-1] in ['png', 'jpg', 'jpeg', 'bmp']):
            image = cv2.imread(make_path(args.source, image_name))
            
            if len(image.shape) < 3 or image.shape[2] == 1:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

            while image.shape[0] > 1000 or image.shape[1] > 1000:
                image = cv2.resize(image, (None, None), fx=0.75, fy=0.75)

            cv2.putText(image, f"< {args.left_name}", (20, image.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255),  3)
            cv2.putText(image, f"{args.right_name} >", (image.shape[1] - 310, image.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0),  3)
            
            image = cv2.resize(image, (400, 400))
            cv2.imshow(f"INPUT: {image_name}", image)
            
            k = 0
            while True:
                k = cv2.waitKeyEx(0)

                if k == KEY_LEFT:
                    os.replace(make_path(args.source, image_name), make_path(left_path, image_name))
                    print(f"Moved {image_name} into {args.left_name} category")
                    break
                elif k == KEY_RIGHT:
                    os.replace(make_path(args.source, image_name), make_path(right_path, image_name))
                    print(f"Moved {image_name} into {args.right_name} category")
                    break

                elif k == 27:
                    close_and_exit()

            cv2.destroyWindow(f"INPUT: {image_name}")

    close_and_exit()
