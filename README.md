# Python Scripts and Tools

This is a collection of scripts and various useful function/class libraries written by me or adapted from the web over time.
Most of them are indipendent from each other so you can simply copy-paste the one you need into your code. Sometimes functions may be redefined inside other functions and that's a deliberate choice to avoid dependencies so you only need to copy the single function you need instead of many functions or import the entire file.

NOTE: sometimes when a single function depends on a Python module, its import statement may be written inside the function itself so that its dependencies are included in the function and you don't have to worry about finding out what to import. If you prefer, that import can be extracted out of the function as a global import in you code, which may be be also beneficial for performance.

## Scripts

- `extract_subimage` script that lets you extract an image from inside another image, compensating the perspective distortion
- `generate_random_noise` (work in progres) script that generates an image of given size and format filled with a configurable noise pattern

## Libraries

- `easy_opencv_trackbars` provides the class `EZTrackbars` that lets you quickly configure OpenCV trackbars even with embedded value mappings, creates a windows that includes live visualization of real and mapped values of each trackbar (even with units of measure if needed). After initialization, the `EZTrackbars` class provides a dataclass-like interface to retrieve the values of each trackbar.
- `image_utilities` contains many functions to be used with NumPy and OpenCV to manipulate and do various stuff with images.
- `useful_functions` a collection of many useful functions that I have stumbled upon and have rewrittern from scratch many times in many projects.