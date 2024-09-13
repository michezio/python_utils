# Python Scripts and Tools

This is a collection of scripts and various useful function/class libraries written by me or adapted from the web over time.
Most of them are indipendent from each other so you can simply copy-paste the one you need into your code. Sometimes functions may be redefined inside other functions and that's a deliberate choice to avoid dependencies so you only need to copy the single function you need instead of many functions or import the entire file.

NOTE: sometimes when a single function depends on a Python module, its import statement may be written inside the function itself so that its dependencies are included in the function and you don't have to worry about finding out what to import. If you prefer, that import can be extracted out of the function as a global import in you code, which may be be also beneficial for performance.

## Scripts

- `extract_subimage` script that lets you extract an image from inside another image, compensating the perspective distortion
- `generate_random_noise` (work in progres) script that generates an image of given size and format filled with a configurable noise pattern
- `dir_tree_cloner` (working but missing some features, not currently developed) this script can clone a complete tree structure from a root folder into another one, replacing files with placeholders or a file list txt (with file properties). Useful to clone a folder structure without its content, i've used it to send the file system structure of a recovered partition to a client so that it could tell me what file they really needed to recover (instead of the whole partition). Works best on Linux, in Windows it works but is much slower.

## Libraries

- `easy_opencv_trackbars` provides the class `EZTrackbars` that lets you quickly configure OpenCV trackbars even with embedded value mappings, creates a windows that includes live visualization of real and mapped values of each trackbar (even with units of measure if needed). After initialization, the `EZTrackbars` class provides a dataclass-like interface to retrieve the values of each trackbar.
- `image_utilities` contains many functions to be used with NumPy and OpenCV to manipulate and do various stuff with images.
- `useful_functions` a collection of many useful functions that I have stumbled upon and have rewrittern from scratch many times in many projects.
- `bit_stream` old project, class `BitStream` provides a way to create a sequence of pure boolean digits to be exported in files without being limited at 8-bit chunks. Not optimized for performace but pretty easy to use. This was more of a toy project from when I was studying compression algorithms and is not inteded to be used in production, surely exist something thousand times better :).
- `serial_relay_controller` classes to manage a relay board (using a line driver like the SP232EEN or similar) over an RS-232 serial connection.
