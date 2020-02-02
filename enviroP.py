from bme280 import BME280
from Adafruit_IO import Client, Feed, RequestError

import time

try:
	from smbus2 import SMBus
except ImportError:
	from smbus import SMBus

def output():

	bus = SMBus(1)
	bme280 = BME280(i2c_dev=bus)

	temp = bme280.get_temperature()
	pressure = bme280.get_pressure()
	humidity = bme280.get_humidity()
	return temp, humidity

def post():
	ADAFRUIT_IO_KEY = 'aio_nzSL66GSZR7evJ9SdhvaLRUZ5i63'
	ADAFRUIT_IO_USERNAME = 'The_Bravest_Toaster'
	
	aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
	try:
		digital = aio.feeds('photocell')
	except RequestError:
		feed = Feed(name="photocell")
		digital = aio.create_feed(feed)
	
	try:
		humidityThread = aio.feeds('humidity')
	except RequestError:
		humidFeed = Feed(name="humidity")
		humidityThread = aio.create_feed(humidFeed)
	
	while(True):
		temp, hum = output()
		aio.send(digital.key, temp)
		aio.send(humidityThread.key, hum)
		time.sleep(10)

if __name__ == "__main__":
	post()
