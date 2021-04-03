import digitalio
import board
import adafruit_rgb_display.st7789 as st7789
from adafruit_rgb_display.rgb import color565
from PIL import Image

from .display import Display


class ST7789Display(Display):
    def __init__(self, width: int, height: int):
        super().__init__()
        cs_pin = digitalio.DigitalInOut(board.CE0)
        dc_pin = digitalio.DigitalInOut(board.D25)
        self.backlight_pin = digitalio.DigitalInOut(board.D22)
        self.backlight_pin.switch_to_output()

        BAUDRATE = 64000000
        self.display = st7789.ST7789(
            board.SPI(),
            cs=cs_pin,
            dc=dc_pin,
            baudrate=BAUDRATE,
            width=width,
            height=height,
            x_offset=0,
            y_offset=80,  # needed for 240x240 display
        )

    def image(self, img: Image) -> None:
        return self.display.image(img)

    def __enter__(self):
        self.display.fill(color565(0, 0, 0))
        self.display.init()
        self.display.rotation = 180
        self.backlight_pin.value = True
        return self

    def __exit__(self, *exc):
        self.backlight_pin.value = False
        return False
