class Message: pass
class AppStarted(Message): pass
class AppExited(Message): pass
class AppFailed(Message): pass
class ButtonPressed(Message):
    def __init__(self, button: int):
        super().__init__()
        self.button = button
