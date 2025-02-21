import pytest
from src.utils.serial_manager import SerialManager

# Classe factice pour simuler serial.Serial
class DummySerial:
    def __init__(self, port, baudrate, timeout):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_open = True

def dummy_serial_success(*args, **kwargs):
    return DummySerial(kwargs.get("port"), kwargs.get("baudrate"), kwargs.get("timeout"))

def dummy_serial_fail(*args, **kwargs):
    raise Exception("Échec de connexion")

def test_initialize_connection_success(monkeypatch):
    monkeypatch.setattr("mantcare.utils.serial_manager.serial.Serial", dummy_serial_success)
    manager = SerialManager("COM3", 9600, retry_attempts=1)
    assert manager.is_connected()

def test_initialize_connection_fail(monkeypatch):
    monkeypatch.setattr("mantcare.utils.serial_manager.serial.Serial", dummy_serial_fail)
    manager = SerialManager("COM3", 9600, retry_attempts=2)
    assert not manager.is_connected()