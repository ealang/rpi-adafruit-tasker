class Message: pass

class AppStarted(Message):
    pass

class AppExited(Message):
    pass

class AppFailed(Message):
    pass

class TaskFinished(Message):
    def __init__(self, returncode: int, stdout: str):
        self.returncode = returncode
        self.stdout = stdout

class ButtonPressed(Message):
    def __init__(self, button: int):
        super().__init__()
        self.button = button
