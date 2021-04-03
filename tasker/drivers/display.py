from PIL import Image


class Display:
    def image(self, img: Image) -> None:
        raise NotImplementedError()

    def __enter__(self):
        raise NotImplementedError()

    def __exit__(self, *exc):
        raise NotImplementedError()
