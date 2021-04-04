from dataclasses import dataclass, replace, field
from enum import Enum
from typing import List, Tuple, Tuple, Optional

from PIL import ImageDraw, ImageFont

from .app_config import AppConfig


Color = Tuple[int, int, int]


class ProcessState(Enum):
    OK = 1
    EXITED = 2
    FAILED = 3


@dataclass
class Styles:
    screen_width: int
    screen_height: int
    font_size: int

    line_padding: int = 3
    screen_padding: int = 15
    screen_left_padding: int = 22
    icon_size: int = 8

    background_color: Color = (0, 0, 0)
    cursor_bg_color: Color = (255, 255, 255)

    text_default_color: Color = (255, 255, 255)
    text_default_highlighted: Color = (0, 0, 0)
    text_exited_color: Color = (128, 128, 128)
    text_failed_color: Color = (255, 0, 0)

    font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    line_height: int = field(init=False)
    num_lines: int = field(init=False)

    def __post_init__(self):
        self.line_height = self.font_size + self.line_padding * 2
        self.num_lines = max((self.screen_height - self.screen_padding * 2) // self.line_height, 1)


@dataclass
class State:
    font: ImageFont
    cursor_index: int = 0
    scroll_index: int = 0
    selected_index: Optional[int] = None
    process_state: ProcessState = ProcessState.OK


@dataclass
class UIState:

    @classmethod
    def construct(cls, config: List[AppConfig], screen_width: int, screen_height: int, font_size: int) -> "UIState":
        styles = Styles(
            screen_width=screen_width,
            screen_height=screen_height,
            font_size=font_size,
        )
        return UIState(
            state=State(
                font=ImageFont.truetype(styles.font_path, font_size),
            ),
            styles=styles,
            config=config,
        )

    def __init__(self, state: State, styles: Styles, config: List[AppConfig]) -> None:
        self._styles = styles
        self._config = config
        self._state = state

    def on_press_select(self) -> "UIState":
        return self._replace_state(
            process_state=ProcessState.OK,
            selected_index=self._state.cursor_index,
        )

    def on_press_next(self) -> "UIState":
        cursor_index = self._state.cursor_index
        scroll_index = self._state.scroll_index
        num_lines = self._styles.num_lines

        cursor_index = (cursor_index + 1) % len(self._config)

        if cursor_index >= scroll_index + num_lines:
            scroll_index = cursor_index - num_lines + 1
        elif cursor_index < scroll_index:
            scroll_index = cursor_index

        return self._replace_state(
            cursor_index=cursor_index,
            scroll_index=scroll_index,
        )

    def on_app_failed(self) -> "UIState":
        return self._replace_state(
            process_state=ProcessState.FAILED,
        )

    def on_app_exited(self) -> "UIState":
        return self._replace_state(
            process_state=ProcessState.EXITED,
        )

    def on_app_started(self) -> "UIState":
        return self._replace_state(
            process_state=ProcessState.OK,
        )

    def on_display_task(self, returncode: int, stdout: str) -> "UIState":
        return self

    def draw(self, draw: ImageDraw.Draw) -> None:
        cursor_index = self._state.cursor_index
        scroll_index = self._state.scroll_index
        selected_index = self._state.selected_index

        num_lines = self._styles.num_lines
        screen_width = self._styles.screen_width
        screen_height = self._styles.screen_height
        line_height = self._styles.line_height
        icon_size = self._styles.icon_size

        draw.rectangle(
            (0, 0, screen_width, screen_height),
            outline=None,
            fill=self._styles.background_color,
        )

        y = self._styles.screen_padding
        i = self._state.scroll_index
        for app_config in self._config[scroll_index:scroll_index + num_lines]:
            fill = self._pick_fill(i)
            if i == cursor_index:
                draw.rectangle(
                    (0, y, screen_width, y + line_height),
                    outline=None,
                    fill=self._styles.cursor_bg_color,
                )
                cx = (self._styles.screen_left_padding - icon_size) // 2
                cy = y + (line_height - icon_size) // 2
                draw.ellipse(
                    [(cx, cy), (cx + icon_size, cy + icon_size)],
                    outline=fill,
                    fill=None,
                    width=1,
                )
            if i == selected_index:
                cx = (self._styles.screen_left_padding - icon_size) // 2
                cy = y + (line_height - icon_size) // 2
                draw.ellipse(
                    [(cx, cy), (cx + icon_size, cy + icon_size)],
                    fill=fill,
                )
            draw.text(
                (self._styles.screen_left_padding, y),
                app_config.display_name,
                font=self._state.font,
                fill=fill
            )

            y += line_height
            i += 1

    @property
    def cursor_index(self) -> int:
        return self._state.cursor_index

    def _replace_state(self, **args) -> "UIState":
        return UIState(
            state=replace(self._state, **args),
            styles=self._styles,
            config=self._config
        )

    def _pick_fill(self, index):
        selected_index = self._state.selected_index

        if index == selected_index:
            process_state = self._state.process_state
            if process_state == ProcessState.EXITED:
                return self._styles.text_exited_color
            if process_state == ProcessState.FAILED:
                return self._styles.text_failed_color

        cursor_index = self._state.cursor_index

        if index == cursor_index:
            return self._styles.text_default_highlighted
        return self._styles.text_default_color
