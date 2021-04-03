import asyncio
import functools
import matplotlib.pyplot as pplot
import numpy as np
from PIL import Image

from .display import Display
from ..messages import ButtonPressed

pplot.ion()


async def _periodic_flush(canvas):
    while True:
        canvas.flush_events()
        await asyncio.sleep(.1)


def _on_keypress(queue, event):
    if event.key == "up":
        button = 0
    elif event.key == "down":
        button = 1
    else:
        return

    asyncio.get_running_loop().create_task(
        queue.put(ButtonPressed(button))
    )


class MatplotlibDisplay(Display):
    def __init__(self, width: int, height: int, queue: asyncio.Queue):
        self.fig, self.ax = pplot.subplots()
        self.plot = self.ax.imshow(np.zeros((height, width)))
        self.fig.show()

        self.fig.canvas.mpl_connect('key_press_event', functools.partial(_on_keypress, queue))
        self.flush_task = asyncio.get_running_loop().create_task(
            _periodic_flush(self.plot.figure.canvas)
        )

    def image(self, img: Image) -> None:
        self.plot.set_data(np.array(img))
        self.plot.figure.canvas.flush_events()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.flush_task.cancel()
        return False
