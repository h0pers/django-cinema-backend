from abc import ABC, abstractmethod


class BaseHandler(ABC):
    def __init__(self, event, *args, **kwargs):
        self.event = event
        super().__init__()

    @abstractmethod
    def handle(self, *args, **kwargs):
        pass

