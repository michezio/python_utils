import numpy as np
import cv2
import argparse
import sys
import os

from dataclasses import dataclass, field

show_grid = False

@dataclass
class Point:
    x: int = field(default=0)
    y: int = field(default=0)

    def __repr__(self):
        return f"Point({self.x}, {self.y})"
    
    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y
    
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, other:float):
        return Point(self.x * other, self.y * other)
    
    def sqdist(self, other):
        return (self.x - other.x)**2 + (self.y - other.y)**2
    
    def dist(self, other):
        return self.sqdist(other) ** 0.5
    



def warpImage(frame:np.ndarray, points:list[Point], width:int, height:int) -> tuple[np.ndarray, np.ndarray]:
    dest_points = np.float32([[0,0], [width, 0], [width, height], [0, height]])
    matrix = cv2.getPerspectiveTransform(np.float32([[pt.x, pt.y] for pt in points]), dest_points)
    img = cv2.warpPerspective(frame, matrix, (width, height))
    return img, matrix

def drawGrid(frame:np.ndarray, size:tuple[int, int], grid:tuple[int, int], color:tuple[int], alpha:float, matrix:np.ndarray) -> None:
    
    def lerp(x1:float, y1:float, x2:float, y2:float, t:float) -> list[float, float]:
        return [x1 + t * (x2 - x1), y1+ t * (y2 - y1)] # faster but may be inaccurate at t = 1 due to float numbers
        #return [x1 * (1 - t) + x2 * t, y1 * (1 - t) + y2 * t]

    w, h = size
    x_div, y_div = grid

    x_step = 1 / x_div
    y_step = 1 / y_div

    line_top = [lerp(0, 0, w, 0, x_step * i) for i in range(1, x_div)]
    line_right = [lerp(w, 0, w, h, x_step * i) for i in range(1, x_div)]
    line_bottom = [lerp(0, h, w, h, y_step * i) for i in range(1, y_div)]
    line_left = [lerp(0, 0, 0, h, y_step * i) for i in range(1, y_div)]

    if matrix is not None:
        matrix_inverse = np.linalg.inv(matrix)

        line_top = np.round(cv2.perspectiveTransform(np.float32([[line_top]]).reshape(-1, 1, 2), matrix_inverse).reshape(-1, x_div-1, 2)[0]).astype(np.int32).tolist()
        line_right = np.round(cv2.perspectiveTransform(np.float32([[line_right]]).reshape(-1, 1, 2), matrix_inverse).reshape(-1, y_div-1, 2)[0]).astype(np.int32).tolist()
        line_bottom = np.round(cv2.perspectiveTransform(np.float32([[line_bottom]]).reshape(-1, 1, 2), matrix_inverse).reshape(-1, x_div-1, 2)[0]).astype(np.int32).tolist()
        line_left = np.round(cv2.perspectiveTransform(np.float32([[line_left]]).reshape(-1, 1, 2), matrix_inverse).reshape(-1, y_div-1, 2)[0]).astype(np.int32).tolist()

        # some_negative = lambda lst: any(x < 0 or y < 0 for x, y in lst)
        # if some_negative(line_top) or some_negative(line_right) or some_negative(line_bottom) or some_negative(line_left):
        #     return
    
    else:
        line_top = [[round(x), round(y)] for x, y in line_top]
        line_right = [[round(x), round(y)] for x, y in line_right]
        line_bottom = [[round(x), round(y)] for x, y in line_bottom]
        line_left = [[round(x), round(y)] for x, y in line_left]
    
    if alpha < 1:
        overlay = frame.copy()
        overlay_centrals = frame.copy()
    else:
        overlay = frame

    for x, (pt1, pt2) in enumerate(zip(line_top, line_bottom)):
        cv2.line(overlay, pt1, pt2, color, 1, lineType=cv2.LINE_AA)
        if x + 1 == x_div // 2:
            cv2.line(overlay_centrals, pt1, pt2, color, 1, lineType=cv2.LINE_AA)

    for y, (pt1, pt2) in enumerate(zip(line_left, line_right)):
        cv2.line(overlay, pt1, pt2, color, 1, lineType=cv2.LINE_AA)
        if y + 1 == y_div // 2:
            cv2.line(overlay_centrals, pt1, pt2, color, 1, lineType=cv2.LINE_AA)

    if alpha < 1:
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, dst=frame)
        cv2.addWeighted(overlay_centrals, min(1, alpha * 1.5), frame, max(0, 1 - alpha * 1.5), 0, dst=frame)

def getResizeParamsKeepRatio(w:int, h:int, max_size:int=1000) -> tuple[tuple[int, int], float]:
    if w <= max_size and h <= max_size:
        scale = 1.0
    elif h >= w and h > max_size:
        scale = max_size / float(h)
        w = int(w * scale)
        h = max_size
    elif w > h and w > max_size:
        scale = max_size / float(w)
        w = max_size
        h = int(h * scale)
    return (w, h), scale

def resizeImageIfBiggerKeepRatio(image:cv2.Mat, max_size:int=1000, inter:int=cv2.INTER_AREA) -> tuple[cv2.Mat, tuple[int, int], float]:
    h, w = image.shape[:2]

    dim, scale = getResizeParamsKeepRatio(w, h, max_size)

    if scale == 1.0:
        return image.copy(), dim, 1.0
    else:
        return cv2.resize(image, dim, interpolation=inter), dim, scale

def extractImage(file_path:str, out_path:str, postfix:str, out_size:tuple[int, int], grid:tuple[int, int], max_win_size:int, autoclose:bool, process:bool):
    global show_grid

    pointsList:list[Point] = []

    image_name = os.path.basename(file_path)
    image_extensions = image_name.split('.')[-1]
    image_name = '.'.join(image_name.split('.')[:-1])
    image_original = cv2.imread(file_path)
    image_reduced, window_size, scale = resizeImageIfBiggerKeepRatio(image_original, max_win_size)

    if out_size is None:
        out_size = image_original.shape[:2][::-1]
    out_size_reduced, _ = getResizeParamsKeepRatio(out_size[0], out_size[1], max_win_size)

    mouse_down = False

    def onMouseClick(event, x, y, flags, param):
        nonlocal mouse_down, pointsList, window_size

        if not 0 <= x < window_size[0] or not 0 <= y < window_size[1]:
            mouse_down = False
            return

        def movePt(x, y):
            closest = 0
            min_dist = float('inf')
            for i, pt in enumerate(pointsList):
                dist = pt.sqdist(Point(x, y))
                if dist < min_dist:
                    min_dist = dist
                    closest = i
            pointsList[closest] = Point(x, y)

        if event == cv2.EVENT_LBUTTONDOWN and not mouse_down:
            mouse_down = True
            if len(pointsList) < 4:
                pointsList.append(Point(x, y))
            else:
                movePt(x, y)
        elif event == cv2.EVENT_MOUSEMOVE and mouse_down:
            movePt(x, y)
        elif event == cv2.EVENT_LBUTTONUP and mouse_down:
            mouse_down = False
    
    main_window_name = f"ExtractImage ({file_path})"
    extr_window_name = "ExtractImage - Extracted"

    cv2.namedWindow(main_window_name, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(main_window_name, onMouseClick)

    warped = None
    matrix = None

    while True:
        
        if cv2.getWindowProperty(main_window_name, cv2.WND_PROP_VISIBLE) == False:
            # quit program
            cv2.destroyAllWindows()
            print("Exiting")
            exit()

        image = image_reduced.copy()

        for i in range(len(pointsList)):
            if i == len(pointsList) - 1 and i != 3:
                break
            p1 = pointsList[i]
            p2 = pointsList[(i+1)%4]
            cv2.line(image, (p1.x, p1.y), (p2.x, p2.y), (255, 255, 255), 1, lineType=cv2.LINE_AA)

        for i, pt in enumerate(pointsList):
            color = np.uint8([[[i * (180 / 4), 255, 255]]])
            color = cv2.cvtColor(color, cv2.COLOR_HSV2BGR)[0, 0].tolist()
            cv2.circle(image, (pt.x, pt.y), 3, color, -1, lineType=cv2.LINE_AA)
        
        if len(pointsList) == 4:
            warped, matrix = warpImage(image_reduced, pointsList, out_size_reduced[0], out_size_reduced[1])
            if show_grid:
                drawGrid(image, out_size_reduced, grid, (255, 255, 255), 0.2, matrix)
                
        cv2.imshow(main_window_name, image)

        if warped is not None:
            if show_grid:
                warped_show = warped.copy()
                drawGrid(warped_show, out_size_reduced, grid, (255, 255, 255), 0.2, None)
            else:
                warped_show = warped
            cv2.imshow(extr_window_name, warped_show)

        k = cv2.waitKey(30)
        if k == 27: # interrupt processing of current image
            cv2.destroyAllWindows()
            break
        if k == ord('q'): # quit program
            print("Exiting")
            cv2.destroyAllWindows()
            exit()
        elif k == ord('c'): # clear point list
            pointsList = []
            warped = None
            cv2.destroyWindow(extr_window_name)
        elif k == ord('g'): # toggle grid
            show_grid = not show_grid
        elif k == ord(' ') or k == ord('s'): # save extracted image
            if warped is not None:
                scaled_pointList = [ x * (1 / scale) for x in pointsList ]
                warped_original, _ = warpImage(image_original, scaled_pointList, out_size[0], out_size[1])
                out_file_name = os.path.join(out_path, f"{image_name}{postfix}.{image_extensions}")
                ok = cv2.imwrite(out_file_name, warped_original)
                if ok:
                    print(f"Extracted image exported to: '{out_file_name}'")
                else:
                    print(f"Could not exported to: '{out_file_name}'")
                if autoclose:
                    cv2.destroyAllWindows()
                    break

    cv2.destroyAllWindows()
    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="extract_subimage.py", usage="use '%(prog)s --help' with a Python3 interpreter for more informations",
        description="Script to extract an image from inside another image even with perspective distortion.\n\n"\
            "Author: Michele Abruzzese (michezio) <oniricha04@gmail.com>   Date: 2023/07/19\n\n"\
            "Select 4 points on the corner of the image you want to extract (starting from top left and going in clockwise direction).\n"\
            "When all 4 points have been selected, the extracted image will appear and you can finely adjust the corners.\n"\
            "- Press 'c' to reset the points.\n"\
            "- Press 'g' to toggle the alignment grid.\n"\
            "- Press 's' or SPACE to save the extracted image.\n"\
            "- Press ESC to stop the current processing (go to the next image if using --folder/-f option).\n"\
            "- Press 'q' or click on X to quit the application (stop all processings if using --folder/-f option).",
        formatter_class=argparse.RawDescriptionHelpFormatter)  

    parser.add_argument("--input", "-i", type=str, help="Path of the image/folder to use as source")
    parser.add_argument("--select", type=str, default=None, help="Select only files containing the provided string (if --input is a folder)")
    parser.add_argument("--ignore", type=str, default=None, help="Ignore all files containing the provided string (if --input is a folder)")
    parser.add_argument("--outsize", "-s", type=str, default=None, help="Output size of the extracted image (default = 800x600)")
    parser.add_argument("--winsize", type=int, default=720, help="Max size of the windows. If width or height of the image to process exceeds this value it is automatically scaled down (default = 720)")
    parser.add_argument("--out", "-o", type=str, default=None, help="Path where to save the extracted images (default = same folder of the --input)")
    parser.add_argument("--postfix", type=str, default="_extr", help="String to append to the file name of each extracted image (default = '_extr')")
    parser.add_argument("--autoclose", action="store_true", help="If present, closes the application after completing the export.")
    parser.add_argument("--grid", type=str, default="20x20", help="Grid divisions for the perspective preview (default = 20x20)")
    parser.add_argument("--process", action="store_true", help="If present, enable processing on the extracted image.") # TODO: implement image processing with controls
    

    if len(sys.argv) < 2:
        parser.print_help()
        exit(1)

    args = parser.parse_args(sys.argv[1:])

    supported_image_formats = ["png", "jpg", "jpeg", "bmp"]

    if args.outsize is not None:
        args.outsize = tuple(map(int, args.outsize.split("x")))

    args.grid = tuple(map(int, args.grid.split("x")))

    is_folder = os.path.isdir(args.input)

    if not is_folder:
        # SINGLE FILE INPUT
        args.input = os.path.normpath(args.input)
        if not args.input.split('.')[-1] in supported_image_formats:
            print("ERROR: The path does not locate a supported file type")
            exit(1)

        if args.out is None:
            root_folder = os.path.join(*args.input.split(os.path.sep)[:-1])
            args.out = root_folder.replace(":", f":{os.path.sep}")

        extractImage(args.input, args.out, args.postfix, args.outsize, args.grid, args.winsize, args.autoclose, args.process)

    else:
        # FOLDER INPUT (+ select and ignore filtering)
        args.input = os.path.normpath(args.input)
        file_list_gen = filter(lambda x: x.split('.')[-1] in supported_image_formats, os.listdir(args.input))
        if args.select is not None:
            file_list_gen = filter(lambda x: args.select in x, file_list_gen)
        if args.ignore is not None:
            file_list_gen = filter(lambda x: args.ignore not in x, file_list_gen)
        origins = [os.path.join(args.input, file) for file in file_list_gen]
        if args.out is None:
            args.out = args.input
        for i, filepath in enumerate(origins):
            print(f"Processing {i+1}/{len(origins)}: {filepath}")
            extractImage(filepath, args.out, args.postfix, args.outsize, args.grid, args.winsize, args.autoclose, args.process)