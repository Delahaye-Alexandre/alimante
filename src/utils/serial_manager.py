import serial
import logging
import time
from typing import Optional

class SerialManager:
    def __init__(self, port: str, baud_rate: int, retry_attempts: int = 3):
        self.port = port
        self.baud_rate = baud_rate
        self.retry_attempts = retry_attempts
        self.connection: Optional[serial.Serial] = None
        self.initialize_connection()

    def initialize_connection(self) -> bool:
        for attempt in range(self.retry_attempts):
            try:
                self.connection = serial.Serial(port=self.port, baudrate=self.baud_rate, timeout=1)
                logging.info(f"Connexion série établie sur {self.port}")
                return True
            except serial.SerialException as e:
                logging.warning(f"Tentative {attempt+1} échouée : {e}")
                time.sleep(2)
        return False

    def is_connected(self) -> bool:
        return self.connection is not None and self.connection.is_open