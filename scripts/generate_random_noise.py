import numpy as np
import cv2
import argparse
import sys
import os

# perlin noise implementation adapted from https://stackoverflow.com/a/42154921

def lerp(a, b, x):
    return a + x * (b - a)

def fade(t):
    # return (3 - 2 * t) * t**2 # Smoothstep: -2t^3 + 3t^2
    return ((6 * t - 15) * t + 10) * t**3 # Smootherstep: 6t^5 + 16t^4 + 10t^3

def gradient(h, x, y):
    # converts h to the right gradient vector and return the dot product between x and y
    vectors = np.array([[0, 1], [0, -1], [1, 0], [-1, 0]])
    g = vectors[h % 4]
    return g[:, :, 0] * x + g[:, :, 1] * y

def perlin_single_pass(x, y):
    # permutation table
    p = np.arange(256, dtype=int)
    np.random.shuffle(p)
    p = np.stack([p, p]).flatten()

    # top left coords
    xi, yi = x.astype(int), y.astype(int)
    # internal coords
    xf, yf = x - xi, y - yi

    # fade factors
    u, v = fade(xf), fade(yf)

    # noise components
    n00 = gradient(p[(p[xi % 512] + yi) % 512], xf, yf)
    n01 = gradient(p[(p[xi % 512] + yi + 1) % 512], xf, yf - 1)
    n11 = gradient(p[(p[(xi + 1) % 512] + yi + 1) % 512], xf - 1, yf - 1)
    n10 = gradient(p[(p[(xi + 1) % 512] + yi) % 512], xf - 1, yf)

    # combine noises
    x1 = lerp(n00, n10, u)
    x2 = lerp(n01, n11, u)

    return lerp(x1, x2, v)

def perlin(width, height, num_steps:int, attenuation:float=1) -> np.ndarray:
    image = np.zeros((height, width), dtype=float)
    for i in range(num_steps):
        freq = 2**i
        lin = np.linspace(0, freq, max(width, height), endpoint=False)
        x, y = np.meshgrid(lin[:width], lin[:height])
        perl = perlin_single_pass(x, y) / (freq ** attenuation)
        image = perl + image
    return (image - np.min(image)) / np.ptp(image)


def generate_random(out_file_name:str, width:int, height:int, channels:int, depth:int, seed:int=None):

    bit_depths = { 1: bool, 8: np.uint8, 16: np.uint16, 32: np.uint32, 64: np.uint64 }

    if seed is None:
        seed = np.random.randint(1 << 32 - 1)
    
    np.random.seed(seed)

    full_image = np.ndarray((height, width, channels), dtype=bit_depths[depth])

    for c in range(channels):
        perl = perlin(width, height, 8, 1.5)
        full_image[:, :, c] = (255 * perl).astype(bit_depths[depth])   

    cv2.imwrite(out_file_name, full_image)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="generate_random_noise.py", usage="use '%(prog)s --help' with a Python3 interpreter for more informations",
        description="Script to quickly generate a random noise image given resolution and format.\n\n"\
            "Author: Michele Abruzzese (michezio) <oniricha04@gmail.com>   Date: 2023/07/21\n\n",
        formatter_class=argparse.RawDescriptionHelpFormatter)  

    parser.add_argument("--out", "-o", type=str, help="File path of the output generated image")
    parser.add_argument("--resolution", "-r", type=str, default="256x256", help="Size of the generated image (default = 256x256)")
    parser.add_argument("--format", "-f", type=str, default=None, help="Output format of the generated image (default = None, based on filename extension)")
    parser.add_argument("--channels", type=int, choices=[1, 3, 4], default=3, help="Number of channels to be used (default = 3, like RGB channels)")
    parser.add_argument("--depth", type=int, choices=[1, 8, 16, 32, 64], default=8, help="Bit depth of each channel (default = 8, 8-bit)")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for the RNG")

    if len(sys.argv) < 2:
        parser.print_help()
        exit(1)

    args = parser.parse_args(sys.argv[1:])

    supported_image_formats = ["png", "jpg", "jpeg", "bmp", "gif", "tiff", "tif"]

    args.out = os.path.normpath(args.out)
    if os.path.exists(args.out):
        print(f"File '{args.out}' already exists.")
        exit(1)

    file_name = os.path.basename(args.out)
    file_extension = file_name.split('.')[-1]

    if file_name == file_extension and args.format is None:
        print("Format cannot be decided based on filename exension. Please provide an explicit one using --format/-f argument")
        exit(1)

    format = file_extension.lower() if args.format is None else args.format.lower()

    if format not in supported_image_formats:
        print(f"Format '{format}' not supported")
        exit(1)

    out_file_name = args.out

    if format != file_extension.lower():       
        print("Explicit file format differs from the one in the file name. Using the explicit one.")
        out_file_name = '.'.join((out_file_name, format))
        print(f"New file name: '{out_file_name}'")

    width, height = map(int, args.resolution.split("x"))
    
    generate_random(out_file_name, width, height, args.channels, args.depth, args.seed)
