import sys, os

"""
Bulk convert all supported images in the current folder to PNG

Usage: place it in the folder you'd like to process and run `python all2png.py [y]`
       use option `y` to automatically overwrite existing PNG files with same name
"""

supported_file_format = ["tif", "tiff", "jpg", "jpeg", "bmp", "tga"]

auto_overwrite = True if len(sys.argv) > 1 and sys.argv[1].lower() == "y" else False
ffmpeg_command = "ffmpeg -hide_banner -loglevel error"
if auto_overwrite:
    ffmpeg_command += " -y"

file_list = list(filter(lambda x: x.split('.')[-1].lower() in supported_file_format, os.listdir(".")))
file_list_len = len(file_list)

error_list = list()

for i, file in enumerate(file_list):
    new_name = ".".join(file.split(".")[:-1]) + ".png"
    print(f"Processing {i + 1}/{file_list_len}: {file} -> {new_name}")
    error = os.system(f"{ffmpeg_command} -i {file} {new_name}")
    if (error):
        error_list.append(file)
        if os.path.exists(new_name): 
            os.remove(new_name)

if len(error_list) > 0:
    print("\nThe following files where not processed correctly:")
    for file in error_list:
        print(file)

print("\nDone")