from abc import ABC, abstractmethod
from src.utils.gpio_manager import GPIOManager

class BaseController(ABC):
    def __init__(self, gpio_manager: GPIOManager):
        self.gpio_manager = gpio_manager

    @abstractmethod
    def check_status(self) -> bool:
        pass