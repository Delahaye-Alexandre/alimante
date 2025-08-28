import Adafruit_DHT

# Type de capteur : DHT22
sensor = Adafruit_DHT.DHT22

# GPIO utilisé (le pin Data)
pin = 4

humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

if humidity is not None and temperature is not None:
    print(f"Temp: {temperature:.1f}°C  Humidity: {humidity:.1f}%")
else:
    print("Échec de lecture du capteur")
