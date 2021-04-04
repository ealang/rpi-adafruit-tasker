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
    TaskFinished,
)
from .ui_state import UIState


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


async def task_supervisor(app_config: AppConfig, queue: asyncio.Queue) -> None:
    logger.info(f"Starting {app_config.display_name}")
    app = await asyncio.create_subprocess_exec(
        app_config.binary,
        *app_config.args,
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, _ = await app.communicate()

    logger.info(f"{app_config.display_name} exited with exit code: {app.returncode}")
    await queue.put(TaskFinished(app.returncode, stdout))


async def app(app_configs: List[AppConfig], virtual_driver: bool) -> None:

    def start_app(selection_index: int) -> asyncio.Task:
        return asyncio.create_task(
            app_supervisor(
                app_configs[selection_index],
                queue,
            ),
        )

    width = 240
    height = 240
    fontsize = 24

    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    ui_state = UIState.construct(app_configs, width, height, fontsize)

    queue = asyncio.Queue()

    if virtual_driver:
        display = _construct_matplotlib_driver(width, height, queue)
    else:
        display = _construct_rpi_driver(width, height, queue)

    # Start first app
    app_task = start_app(ui_state.cursor_index)
    ui_state = ui_state.on_press_select()

    with display:
        while True:
            ui_state.draw(draw)
            display.image(image)

            msg = await queue.get()

            if isinstance(msg, ButtonPressed):
                if msg.button == 0:
                    ui_state = ui_state.on_press_select()

                    # app_task.cancel()
                    # await app_task
                    # app_task = start_app(ui_state.cursor_index)
                    asyncio.create_task(
                        task_supervisor(
                            app_configs[ui_state.cursor_index],
                            queue,
                        ),
                    )


                elif msg.button == 1:
                    ui_state = ui_state.on_press_next()

            elif isinstance(msg, AppFailed):
                ui_state = ui_state.on_app_failed()
            elif isinstance(msg, AppExited):
                ui_state = ui_state.on_app_exited()
            elif isinstance(msg, AppStarted):
                ui_state = ui_state.on_app_started()
            elif isinstance(msg, TaskFinished):
                print("got", msg.returncode, msg.stdout)
                ui_state = ui_state.on_display_task(msg.returncode, msg.stdout)


def main():
    logging.basicConfig(level="INFO")

    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", type=str, help="Path to json config file")
    parser.add_argument("--virtual", action="store_true", help="Use matplotlib driver for display/input")
    args = parser.parse_args()

    with open(args.config_path) as fp:
        config = [
            AppConfig(**args)
            for args in json.load(fp)["mutex_daemons"]
        ]

    asyncio.run(app(config, args.virtual))


if __name__ == "__main__":
    main()
