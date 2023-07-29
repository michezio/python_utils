import numpy as np
import cv2


def heatmap(img:np.ndarray, cmap:int=None, min_value:float=None, max_value:float=None) -> np.ndarray:
    if len(img.shape) > 2 or img.shape[3] != 1:
        raise ValueError("only 2 dimensional arrays are supported as input")

    min_val = np.min(img) if min_value is None else min_value
    max_val = np.max(img) if max_value is None else max_value

    if min_value is not None or max_value is not None:
        img = np.clip(img, min_val, max_val)

    img = (255 * (img - min_val) / (max_val - min_val)).astype(np.uint8)
    
    if cmap is None:
        return img
    return cv2.applyColorMap(img, cmap)


def put_wrapped_text(img:np.ndarray, text:str, width:int, gap:int, org:tuple, 
                     font:int, scale:float, color:tuple, thickness:int=1, **kwargs) -> None:
    # IMPORTS ########
    import textwrap
    ##################
    textsize = cv2.getTextSize(text, font, scale, thickness)[0]
    gap = textsize[1] + gap
    char_size = textsize[0]/len(text)
    wrap_size = int(width / char_size)
    if wrap_size == 0:
        return
    wrapped_text = textwrap.wrap(text, width=wrap_size)
    for i, line in enumerate(wrapped_text):
        x = org[0]
        y = int(org[1] + i * gap)
        cv2.putText(img, line, (x, y), font, scale, color, thickness, **kwargs)


def overlay_image_alpha(img, img_overlay, x, y, alpha_mask=None):
    """Overlay `img_overlay` onto `img` at (x, y) and blend using optional `alpha_mask`.

    `alpha_mask` must have same HxW as `img_overlay` and values in range [0, 1].
    """

    if y < 0 or y + img_overlay.shape[0] > img.shape[0] or x < 0 or x + img_overlay.shape[1] > img.shape[1]:
        y_origin = 0 if y > 0 else -y
        y_end = img_overlay.shape[0] if y < 0 else min(img.shape[0] - y, img_overlay.shape[0])

        x_origin = 0 if x > 0 else -x
        x_end = img_overlay.shape[1] if x < 0 else min(img.shape[1] - x, img_overlay.shape[1])

        img_overlay_crop = img_overlay[y_origin:y_end, x_origin:x_end]
        alpha = alpha_mask[y_origin:y_end, x_origin:x_end] if alpha_mask is not None else None
    else:
        img_overlay_crop = img_overlay
        alpha = alpha_mask

    y1 = max(y, 0)
    y2 = min(img.shape[0], y1 + img_overlay_crop.shape[0])

    x1 = max(x, 0)
    x2 = min(img.shape[1], x1 + img_overlay_crop.shape[1])

    img_crop = img[y1:y2, x1:x2]
    img_crop[:] = alpha * img_overlay_crop + (1.0 - alpha) * img_crop if alpha is not None else img_overlay_crop
    

def image_resize(image, size, letterbox=True, out=None):
    """
    Letter box (black bars) a color image (think pan & scan movie shown 
    on widescreen) if not same aspect ratio as specified size. 
    """
    cols, rows = size
    image_rows, image_cols = image.shape[:2]
    row_ratio = rows / float(image_rows)
    col_ratio = cols / float(image_cols)
    ratio = min(row_ratio, col_ratio)
    
    image_resized = cv2.resize(image, dsize=(None, None), fx=ratio, fy=ratio)

    if letterbox:
        shape = (int(rows), int(cols), 3)
        if out is None:
            out = np.zeros(shape, dtype=np.uint8)
        row_start = int((out.shape[0] - image_resized.shape[0]) / 2)
        col_start = int((out.shape[1] - image_resized.shape[1]) / 2)
        out[row_start:row_start + image_resized.shape[0], col_start:col_start + image_resized.shape[1]] = image_resized
        return out

    return image_resized


def stack_images(stack:list, shape:tuple=None, background:tuple=(0,0,0)) -> np.ndarray:
    """
    Stacks multiple images in a single image resizing them to fit in in the grid (keeps aspect ratio)

    usage:
    @stack place the images in a list of lists with each list representing a row of the grid (see example)
    @shape the size of the whole image, if None the size will be the one of the top-left image multiplied by rows and columns
    @background color of the background of the whole image (shown in empty spots or in margins)

    example:
    grid = stack_images([[img0_r0, img1_r0, img2_r0], [img0_r1, img1_r1, img2_r1], ...], shape=(600, 800), background=(255, 0, 255))
    """
    if stack[0][0] is None:
        raise ValueError("First element of the grid cannot be None")

    if shape[0] <= 0 or shape[1] <= 0:
        raise ValueError("Shape cannot have a 0 or negative element")
    
    rows = len(stack)
    columns = len(stack[0])

    height, width = stack[0][0].shape[:2] if shape is None else (shape[0] // rows, shape[1] // columns)

    canvas = np.full((height * rows, width * columns, 3), background, dtype=np.uint8)

    for i, row in enumerate(stack):
        start_y = i * height
        stop_y = (i+1) * height
        for j, img in enumerate(row):
            if img is None:
                continue
            start_x = j * width
            stop_x = (j+1) * width
            if len(img.shape) < 3 or img.shape[2] == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            image_resize(img, (width, height), letterbox=True, out=canvas[start_y:stop_y, start_x:stop_x])

    return canvas


def extract_and_straighten_image(source_image:np.ndarray, corners:list, width:int, height:int) -> tuple[np.ndarray, np.ndarray]:
    if len(corners) != 4 or any(len(pt) != 2 for pt in corners):
        raise ValueError("Corners must be a list of size = 4 and each element must be of size = 2")
    dest_corners = np.float32([[0,0], [width, 0], [width, height], [0, height]])
    transformation_matrix = cv2.getPerspectiveTransform(np.float32(corners), dest_corners)
    extracted_image = cv2.warpPerspective(source_image, transformation_matrix, (width, height))
    return extracted_image, transformation_matrix