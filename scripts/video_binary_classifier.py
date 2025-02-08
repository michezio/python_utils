import cv2
import sys
import os
import psutil
import numpy as np
import argparse

KEY_LEFT = 2424832
KEY_RIGHT = 2555904

def print_replacing(text):
    sys.stdout.write(f"\r{text}")
    sys.stdout.flush()

def make_path(*args):
    return os.path.normpath(os.path.join(*args))

def update_array(array, start, stop,  direction, status):
    for i in range(start, stop, direction):
        if array[i] != status:
            array[i] = status
        else:
            break

def generate_timeline(binary_select, binary_class, index, frame_width):
    timeline = np.zeros((50, len(binary_select) + 20, 3), dtype=np.uint8)
    timeline[10:-10, index+10] = (255,255,255)
    timeline[20, 10:-10] = [(255,255,0) if a else (40,40,40) for a in binary_select]
    timeline[30, 10:-10] = [(0,255,0) if a else (0,0,255) for a in binary_class]
    return cv2.resize(timeline, (frame_width, 50), interpolation=cv2.INTER_NEAREST)

def update_left(array, start, status):
    update_array(array, start, -1, -1, status)

def update_right(array, start, status):
    update_array(array, start, len(array), 1, status)

def export_images(frames, binary_select, binary_class, name, path_false, path_true, opt_png_compression):
    if not os.path.exists(path_false):
        os.makedirs(path_false)
    if not os.path.exists(path_true):
        os.makedirs(path_true)

    true_count = 0
    false_count = 0

    params = [cv2.IMWRITE_PNG_COMPRESSION, opt_png_compression] if opt_png_compression > -1 else [cv2.IMWRITE_JPEG_QUALITY, 100]

    for i in range(len(frames)):
        print_replacing(f"Exporting {'PNG' if opt_png_compression > -1 else 'JPEG'} images: {100*(i+1)/len(frames):.1f}%")

        if not binary_select[i]:
            continue
        file_name = f"{name}_{str(i).zfill(len(str(len(frames))))}.{'png' if opt_png_compression > -1 else 'jpg'}"

        if binary_class[i]:
            true_count += 1
            out_path = path_true
        else:
            false_count += 1
            out_path = path_false

        cv2.imwrite(os.path.join(out_path, file_name), frames[i], params)

    print(f"\nExported {true_count} TRUE and {false_count} FALSE.")




if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="video_binary_classifier.py",
    description="Generate a binary classification dataset with frames from a video source.\n"\
        "Only selected frames will be classified and exported.\n"\
        "All frames start as not selected.\n"\
        "  Use 'A' to start a selection and 'S' to end the selection.\n"\
        "  Use 'D' to toggle selection for single frames.\n"\
        "All frames start as FALSE classified (red).\n"\
        "  Use 'Z' to start a group of TRUE classified (green) frames and 'X' to end that group.\n"\
        "  Use 'C' to toggle classification for single frame.\n"\
        "Frames classified with FALSE (red) are exported to the path specified by --false_out.\n"\
        "Frames classified with TRUE (green) are exported to the path specified by --true_out.\n"\
        "Use 'O' to start exporting selected frames with their classification.")

    parser.add_argument("--input", "-i", type=str, required=True, help="Path to the video file to use as source. If folder is used iterate all video files.")
    parser.add_argument("--false_out", "-f", type=str, default='./false', help="Path to export FALSE classified images")
    parser.add_argument("--true_out", "-t", type=str, default='./true', help="Path to export TRUE classified images")
    parser.add_argument("--png", type=int, default=-1, help="If present save images as PNG with the specified compression, else use JPEG")
    parser.add_argument("--autoclose", action="store_true", help="If present, closes the application after completing the export.")

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args(sys.argv[1:])

    input_path = args.input
    path_true = args.true_out
    path_false = args.false_out
    use_png = args.png
    autoclose = args.autoclose

    origins = []

    if os.path.isdir(input_path):
        origins = [os.path.normpath(os.path.join(input_path, file)) for file in os.listdir(input_path) if file.split('.')[-1] in ['mp4', 'avi', 'm4v']]
    elif os.path.exists(input_path):
        origins = [input_path]
    else:
        print(f"ERROR: file/folder '{input_path}' does not exist.")
        exit()

    for op_num, origin in enumerate(origins):

        print(f"\nRunning on file {op_num+1}/{len(origins)}: '{origin}'")

        file_name = ".".join(os.path.basename(origin).split(".")[:-1])

        try:
            capture = cv2.VideoCapture(origin, cv2.CAP_FFMPEG)
        except:
            print(f"ERROR: '{origin}' is not a valid video file.")
            exit()

        frames = []

        total_frames_n = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_available = True
        while frame_available:
            frame_available, frame = capture.read()
            if frame_available:
                #if len(frame.shape) > 2:
                #    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frames.append(frame)
            print_replacing(f"Loading video frames in memory: {100*len(frames)/total_frames_n:.1f}%")
        capture.release()

        print(f"\nProcess is using {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2:.2f} MB of RAM memory.")

        binary_select = [False] * len(frames)
        binary_class = [False] * len(frames)

        cv2.namedWindow(f"{origin}", cv2.WINDOW_AUTOSIZE)


        frame_index = 0

        while True:

            temp_frame = frames[frame_index].copy()

            color = (0,255,0) if binary_class[frame_index] else (0,0,255)
            cv2.rectangle(temp_frame, (0,0), temp_frame.shape[:2][::-1], color, thickness=10)
            
            if not binary_select[frame_index]:
                cv2.line(temp_frame, (0,0), temp_frame.shape[:2][::-1], (0,0,0), 2)
                cv2.line(temp_frame, (0,temp_frame.shape[0]), (temp_frame.shape[1],0), (0,0,0), 2)

            timeline = generate_timeline(binary_select, binary_class, frame_index, temp_frame.shape[1])

            composed = np.vstack((temp_frame, timeline))

            cv2.imshow(f"{origin}", composed)


            k = cv2.waitKeyEx(0)

            if k == KEY_LEFT:
                frame_index = max(0, frame_index-1)
            elif k == KEY_RIGHT:
                frame_index = min(total_frames_n-1, frame_index+1)
            elif k == ord(','):
                frame_index = max(0, frame_index-5)
            elif k == ord('.'):
                frame_index = min(total_frames_n-1, frame_index+5)

            elif k == ord('a'): # start selection
                update_left(binary_select, frame_index-1, False)
                update_right(binary_select, frame_index, True)
            elif k == ord('s'): # end selection
                update_left(binary_select, frame_index-1, True)
                update_right(binary_select, frame_index, False)
            elif k == ord('d'): # toggle selection for single frame
                binary_select[frame_index] = not binary_select[frame_index]

            elif k == ord('z'): # start true classification
                update_left(binary_class, frame_index-1, False)
                update_right(binary_class, frame_index, True)
            elif k == ord('x'): # stop true classification
                update_left(binary_class, frame_index-1, True)
                update_right(binary_class, frame_index, False)
            elif k == ord('c'): # toggle binary classification for single frame
                binary_class[frame_index] = not binary_class[frame_index]
                
            elif k == ord('o'):
                export_images(frames, binary_select, binary_class, file_name, path_false, path_true, use_png)
                if autoclose:
                    break

            elif k == 27:
                break

        del frames
        cv2.destroyAllWindows()