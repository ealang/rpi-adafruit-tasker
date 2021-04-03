import asyncio

import digitalio
import board

from ..messages import ButtonPressed


async def button_poll_task(queue: asyncio.Queue) -> None:
    button_a = digitalio.DigitalInOut(board.D23)
    button_b = digitalio.DigitalInOut(board.D24)
    button_a.switch_to_input()
    button_b.switch_to_input()

    last_a = False
    last_b = False
    while True:
        a = not button_a.value
        b = not button_b.value

        if a and not last_a:
            await queue.put(ButtonPressed(0))
        if b and not last_b:
            await queue.put(ButtonPressed(1))

        last_a = a
        last_b = b

        await asyncio.sleep(0.05)
