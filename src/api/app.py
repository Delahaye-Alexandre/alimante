from flask import Flask, jsonify, request
from src.utils.config_manager import SystemConfig
from src.utils.serial_manager import SerialManager
from src.controllers.temperature_controller import TemperatureController
from src.controllers.light_controller import LightController
from src.controllers.humidity_controller import HumidityController
from src.controllers.feeding_controller import FeedingController

app = Flask(__name__)

# Initialiser les contrôleurs
config = SystemConfig.from_json('config/config.json', 'config/orthopteres/mantidae/mantis_religiosa.json')
serial_manager = SerialManager(config.serial_port, config.baud_rate)
temperature_controller = TemperatureController(serial_manager, config.temperature)
humidity_controller = HumidityController(serial_manager, config.humidity)
light_controller = LightController(serial_manager, config.location)
feeding_controller = FeedingController(serial_manager, config.feeding)

@app.route('/metrics', methods=['GET'])
def get_metrics():
    # Récupérer les métriques des capteurs
    temperature = temperature_controller.read_temperature()
    humidity = humidity_controller.read_humidity()
    return jsonify({
        'temperature': temperature,
        'humidity': humidity
    })

@app.route('/control', methods=['POST'])
def control():
    # Contrôler les conditions en fonction des paramètres envoyés
    data = request.json
    if 'temperature' in data:
        temperature_controller.control_temperature()
    if 'humidity' in data:
        humidity_controller.control_humidity()
    if 'light' in data:
        light_controller.control_lighting()
    if 'feeding' in data:
        feeding_controller.control_feeding()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)