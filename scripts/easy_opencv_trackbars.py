import cv2
import numpy as np
from dataclasses import dataclass

class EZTrackbars:

    @dataclass
    class Trackbar:
        name: str
        variable: str
        unit: str


    def __init__(self, name:str, width:int=500, font_size:int=12, padding:int=6):
        self.winname: str = name
        self.width: int = width
        self.font_size: int = font_size
        self.padding: int = padding
        self.trackbars: list[EZTrackbars.Trackbar] = []
        cv2.namedWindow(self.winname, cv2.WINDOW_AUTOSIZE)
        cv2.resizeWindow(self.winname, self.width, 100)

    def is_active(self) -> bool:
        return cv2.getWindowProperty(self.winname, cv2.WND_PROP_VISIBLE) == True


    def close(self):
        if self.is_active():
            cv2.destroyWindow(self.winname)


    def redraw_on_window(self):
        if not self.is_active():
            return

        canvas_height: int = (self.font_size + self.padding) * len(self.trackbars) + self.padding

        if cv2.getWindowImageRect(self.winname)[2:] != (self.width, canvas_height):
            cv2.resizeWindow(self.winname, self.width, canvas_height)
    
        # don't know why but max(100, canvas_height) is required
        size: tuple = (max(100, canvas_height), self.width, 3)
        canvas: np.ndarray = np.zeros(size, dtype=np.uint8)
        
        for i, trackbar in enumerate(self.trackbars):
            vpos: int = (i + 1) * (self.font_size + self.padding)
            text: str = f"{trackbar.name} = {self.__dict__[trackbar.variable]} {'' if trackbar.unit is None else trackbar.unit}"
            cv2.putText(canvas, text, (self.padding, vpos), cv2.FONT_HERSHEY_SIMPLEX, self.font_size / 22, (255, 255, 255), 1)

        cv2.imshow(self.winname, canvas)
        

    def make_trackbar(self, trackbar_name:str, variable:str, min_val:int, max_val:int, init_val:int=None, unit:str=None):
        """
        Makes a trackbar ranging from `min_val` to `max_val` included, initialized at `init_val`        
        """
        init_val = init_val if init_val is not None else min_val
        if not (min_val <= init_val <= max_val):
            raise ValueError("Initial value out of range")
        
        self.trackbars.append(EZTrackbars.Trackbar(trackbar_name, variable, unit))
        self.__dict__[variable] = init_val

        def callback(value):
            self.__dict__[variable] = value
            self.redraw_on_window()

        cv2.createTrackbar(trackbar_name, self.winname, init_val, max_val-min_val, callback)
        if min_val != 0:
            cv2.setTrackbarMin(trackbar_name, self.winname, min_val)


    def make_mapped_trackbar(self, trackbar_name:str, variable:str, min_val:float, max_val:float, init_val:float=None, unit:str=None, resolution:int=20, precision:int=0):
        """
        Makes a trackbar ranging from 0 to `resolution` (default 20) whose values map to a range from `min_val` to `max_val`
        and initialized at `init_val` (mapped value)
        """
        init_val = init_val if init_val is not None else min_val
        init_val = round(self.rangemap(init_val, min_val, max_val, 0, resolution))

        if not (0 <= init_val <= resolution):
            raise ValueError("Initial value out of range")
        
        self.trackbars.append(EZTrackbars.Trackbar(trackbar_name, variable, unit))
        self.__dict__[variable] = init_val

        def callback(value):
            mapped_value = self.rangemap(value, 0, resolution, min_val, max_val)
            self.__dict__[variable] = round(mapped_value) if precision == 0 else round(mapped_value, precision) 
            self.redraw_on_window()

        cv2.createTrackbar(trackbar_name, self.winname, init_val, resolution, callback)


    @staticmethod
    def rangemap(value, source_min:float, source_max:float, target_min:float, target_max:float) -> float:
        return target_min + ((target_max - target_min) * (value - source_min) / (source_max - source_min))


if __name__ == '__main__':
    """
    DEMO APPLICATION
    """
    ctrl = EZTrackbars("EZTrackbars", width=600, font_size=20, padding=10)

    ctrl.make_trackbar("Test trackbar 1", "foo", 5, 25, 9, unit="units")
    ctrl.make_mapped_trackbar("Test trackbar 2", "bar", 7, 13, 8, unit="km", resolution=100, precision=3)

    foo_bk = None
    bar_bk = None

    while ctrl.is_active():
        if foo_bk != ctrl.foo:
            print("Foo", ctrl.foo)
            foo_bk = ctrl.foo

        if bar_bk != ctrl.bar:
            print("Bar", ctrl.bar)
            bar_bk = ctrl.bar    
        
        if cv2.waitKey(1) & 0xFF == 27:
            break

    ctrl.close()
