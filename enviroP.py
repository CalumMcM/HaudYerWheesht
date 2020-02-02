from bme280 import BME280
from Adafruit_IO import Client, Feed, RequestError
from enviroplus import gas

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

	gases = gas.read_all()
	nh3 = gases.nh3
	no2 = gases.oxidising

	return temp, humidity, nh3, no2

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
	
	try:
		no2Thread = aio.feeds('no2')
	except RequestError:
		no2Feed = Feed(name="no2")
		no2Thread = aio.create_feed(no2Feed)

	while(True):
		temp, hum, nh3, no2 = output()
		aio.send(digital.key, temp)
		aio.send(humidityThread.key, hum)
		aio.send(no2Thread.key, no2)
		time.sleep(10)

if __name__ == "__main__":
	post()
