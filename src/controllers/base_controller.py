from abc import ABC, abstractmethod
from src.utils.serial_manager import SerialManager

class BaseController(ABC):
    def __init__(self, serial_manager: SerialManager):
        self.serial_manager = serial_manager

    @abstractmethod
    def check_status(self) -> bool:
        pass