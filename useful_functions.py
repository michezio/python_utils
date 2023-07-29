import datetime
import time
import colorsys
import random

def makeChunks(lst:list, n:int, padding:bool=True) -> list:
    '''
    Yield successive n-sized chunks from lst.
    If padding is true, the last chunks will contain
    None elements to make up for a n-size chunk
    '''
    if padding and (rem := len(lst) % n):
        lst.extend([None] * (n-rem))
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_timestamp(format="%Y%m%d_%H%M%S"):
    return datetime.datetime.now().strftime(format)


def precise_sleep(duration, get_now=time.perf_counter):
    now = get_now()
    end = now + duration
    while now < end:
        now = get_now()


def color_generator(initial:int) -> tuple:
    hue = initial
    while True:
        yield tuple(map(lambda x: int(x*255), colorsys.hsv_to_rgb(hue/255, 1, 1)))
        hue += 206
        hue %= 256   


def random_color(hashable=None):
    """
    Generate a random 3-channel color.
    If hashable is present, the random color will be deterministic and 
    will be always the same for that object
    """
    if hashable is None:
        seed = random.randint(0, 1e9-1)
    else:
        seed = abs(hash(hashable))

    r = 256 * (seed % 1000) // 1000
    g = 256 * ((seed // 1000) % 1000) // 1000
    b = 256 * ((seed // 1000000) % 1000) // 1000
    return (b, g, r)


def validate_color(color) -> tuple:
    if isinstance(color, int) or isinstance(color, float):
        color = (color,) * 3

    if len(color) != 3:
        raise ValueError("Color should be a single value or a tuple/list of 3 values")

    if any(isinstance(x, float) for x in color):
        if not all(0 <= x <= 1 for x in color):
            raise ValueError("Color values (float) must be in range 0-1'")
        return tuple(map(lambda x: round(x) * 255), color)
    else:
        if not all(0 <= x <= 255 for x in color):
            raise ValueError("Color values (int) must be in range 0-255")
        return color
    

def lerp(a, b, x):
    return a + x * (b - a)
    # return a * (1 - x) + b * x  # little slower but less susceptible to float errors when x = 1


def smooth_step(x, smoother=False):
    x = max(0, min(1, x))
    if smoother:
        return ((6 * x - 15) * x + 10) * x**3 # Smootherstep: 6x^5 + 16x^4 + 10x^3
    return (3 - 2 * x) * x**2 # Smoothstep: -2x^3 + 3x^2
    

def map_range(value, source_min:float, source_max:float, target_min:float, target_max:float) -> float:
    return target_min + ((target_max - target_min) * (value - source_min) / (source_max - source_min))


def generalized_smooth_step(x, N):
    """
    Taken from Wikipedia implementation at https://en.wikipedia.org/wiki/Smoothstep
    N -> polynomial degree = 2N+1
    """
    def pascal(a, b):
        result = 1
        for i in range(b):
            result *= (a - i) / (i + 1)
        return result
    
    x = max(0, min(1, x))

    result = 0
    for n in range(N+1):
        result += pascal(-N - 1, n) * pascal(2 * N + 1, N - n) * x**(N + n + 1)
    
    return result


def extract_info_from_file_path(path:str):
    import os
    parent = os.path.dirname(path)
    file_name = os.path.basename(path)
    *name, extension = file_name.split('.')
    name = '.'.join(name)
    return parent, file_name, name, extension