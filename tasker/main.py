import argparse
import asyncio
import dataclasses
import json
import logging
from enum import Enum
from typing import List

from PIL import Image, ImageDraw, ImageFont
from .app_config import AppConfig
from .drivers.display import Display
from .messages import (
    AppExited,
    AppFailed,
    AppStarted,
    ButtonPressed,
)


logger = logging.getLogger(__name__)


def _construct_matplotlib_driver(width: int, height: int, queue: asyncio.Queue) -> Display:
    from .drivers.matplotlib_display import MatplotlibDisplay
    return MatplotlibDisplay(width, height, queue)


def _construct_rpi_driver(width, height, queue: asyncio.Queue) -> Display:
    from .drivers.st7789_display import ST7789Display
    from .drivers.st7789_input import button_poll_task
    asyncio.create_task(button_poll_task(queue))
    return ST7789Display(width, height)


async def app_supervisor(app_config: AppConfig, queue: asyncio.Queue) -> None:
    app = None
    try:
        for _ in range(app_config.retry_count):
            logger.info(f"Starting {app_config.display_name}")
            app = await asyncio.create_subprocess_exec(
                app_config.binary,
                *app_config.args,
            )
            await queue.put(AppStarted())
            await app.wait()

            await queue.put(AppExited() if app.returncode == 0 else AppFailed())

            logger.info(f"{app_config.display_name} exited with exit code: {app.returncode}")
            if app.returncode == 0:
                return 0

            await asyncio.sleep(app_config.retry_delay)

        logger.info(f"Gave up trying to start {app_config.display_name}")
        await queue.put(AppFailed())

    except asyncio.CancelledError:
        if app and app.returncode is None:
            logger.error(f"Terminating {app_config.display_name}")
            app.terminate()
            await app.wait()
            logger.error(f"Terminated {app_config.display_name}")

    except Exception as e:
        logger.exception("Unexpected failure")
        await queue.put(AppFailed())


async def app(app_configs: List[AppConfig], virtual_driver: bool) -> None:
    width = 240
    height = 240
    fontsize = 24
    line_padding = 3
    screen_padding = 15
    line_height = fontsize + line_padding * 2
    num_lines = max((height - screen_padding * 2) // line_height, 1)

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fontsize)
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    background_color = (0, 0, 0)
    deselected_text_color = (255, 255, 255)
    selected_text_color = (0, 0, 0)
    selected_text_exited_color = (200, 200, 200)
    selected_text_failed_color = (255, 0, 0)
    selected_background_color = (255, 255, 255)

    scroll_index = 0
    selection_index = 0

    class AppState(Enum):
        OK = 1
        EXITED = 2
        FAILED = 3

    app_state = AppState.OK

    def pick_text_color(i):
        if i != selection_index:
            return deselected_text_color
        if app_state == AppState.OK:
            return selected_text_color
        if app_state == AppState.EXITED:
            return selected_text_exited_color
        return selected_text_failed_color

    def refresh_display() -> None:
        draw.rectangle((0, 0, width, height), outline=0, fill=background_color)

        y = screen_padding
        i = scroll_index
        for app_config in app_configs[scroll_index:scroll_index + num_lines]:
            selected = i == selection_index
            if selected:
                draw.rectangle((0, y, width, y + line_height), outline=0, fill=selected_background_color)

            draw.text(
                (screen_padding, y),
                app_config.display_name,
                font=font,
                fill=pick_text_color(i),
            )

            y += line_height
            i += 1

        display.image(image)

    def start_selected_app() -> asyncio.Task:
        return asyncio.create_task(
            app_supervisor(
                app_configs[selection_index],
                queue,
            ),
        )

    queue = asyncio.Queue()
    app_task = start_selected_app()

    if virtual_driver:
        display = _construct_matplotlib_driver(width, height, queue)
    else:
        display = _construct_rpi_driver(width, height, queue)


    with display:
        while True:

            if selection_index >= scroll_index + num_lines:
                scroll_index = selection_index - num_lines + 1
            elif selection_index < scroll_index:
                scroll_index = selection_index

            refresh_display()

            msg = await queue.get()

            if isinstance(msg, ButtonPressed):
                direction = -1 if msg.button == 0 else 1
                selection_index = (selection_index + direction) % len(app_configs)
                app_task.cancel()
                await app_task
                app_task = start_selected_app()
                app_state = AppState.OK
            elif isinstance(msg, AppFailed):
                app_state = AppState.FAILED
            elif isinstance(msg, AppExited):
                app_state = AppState.EXITED
            elif isinstance(msg, AppStarted):
                app_state = AppState.OK


def main():
    logging.basicConfig(level="INFO")

    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", type=str, help="Path to json config file")
    parser.add_argument("--virtual", action="store_true", help="Use matplotlib driver for display/input")
    args = parser.parse_args()

    with open(args.config_path) as fp:
        config = [
            AppConfig(**args)
            for args in json.load(fp)
        ]

    asyncio.run(app(config, args.virtual))


if __name__ == "__main__":
    main()
