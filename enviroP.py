from bme280 import BME280
from Adafruit_IO import Client, Feed, RequestError
from enviroplus import gas


import ltr559
import time

try:
	from smbus2 import SMBus
except ImportError:
	from smbus import SMBus
try:
	from ltr559 import LTR559
	ltr559 = LTR559()
except ImportError:
	import ltr559

def get_cpu_temperature():
	with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
		temp = f.read()
		temp = int(temp) / 1000.0
	return temp

def output():

	bus = SMBus(1)
	bme280 = BME280(i2c_dev=bus)

	cpu_temps = [get_cpu_temperature()] * 5
	factor = 0.8

	raw_temp = bme280.get_temperature()
	cpu_temp = get_cpu_temperature()
	cpu_temps = cpu_temps[1:] + [cpu_temp]
	avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
	compTemp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)

	pressure = bme280.get_pressure()
	humidity = bme280.get_humidity()

	gases = gas.read_all()
	nh3 = gases.nh3
	no2 = gases.oxidising

	light = ltr559.get_lux()
	proxim = ltr559.get_proximity()

	return compTemp, humidity, nh3, no2, light, proxim, pressure

def save():
	file = open("data.txt", "a")
	
	temp, humidity, nh3, no2, light, proxim, pressure = output()

	curTime = time.strftime("%d/%m/%y,%H:%M", time.localtime())
	
	line = curTime + "," + str(temp) + "," + str(humidity) + "," + str(nh3) + "," + str(no2)	
	line += "," + str(light) + "," + str(proxim) + "," + str(pressure) + "\n"

	file.write(line)

	file.close()

	print (line)

def main():
	ADAFRUIT_IO_KEY = 'aio_nzSL66GSZR7evJ9SdhvaLRUZ5i63'
	ADAFRUIT_IO_USERNAME = 'The_Bravest_Toaster'
	
	aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
	try:
		tempThread = aio.feeds('temp')
	except RequestError:
		tempFeed = Feed(name="temp")
		tempThread = aio.create_feed(tempFeed)
	
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

	try:
		nh3Thread = aio.feeds('no3')
	except RequestError:
		nh3Feed = Feed(name="no3")
		nh3Thread = aio.create_feed(nh3Feed)

	try:
		lightThread = aio.feeds('photocell')
	except RequestError:
		lightFeed = aio.Feed(name="photocell")
		lightThread = aio.create_feed(lightFeed)

	try:
		proximThread = aio.feeds('proxim')
	except RequestError:
		proximFeed = aio.Feed(name="proxim")
		proximThread = aio.create_feed(proximFeed)
	try:
		pressureThread = aio.feeds('pressure')
	except RequestError:
		pressureFeed = aio.Feed(name="pressure")
		pressureThread = aio.create_feed(pressureThread)

	starttime = time.time()
	while(True):
		temp, hum, nh3, no2, light, proxim, pressure = output()
		aio.send(tempThread.key, temp)
		aio.send(humidityThread.key, hum)
		aio.send(no2Thread.key, no2)
		aio.send(nh3Thread.key, nh3)
		aio.send(lightThread.key, light)
		aio.send(proximThread.key, proxim)
		aio.send(pressureThread.key, pressure)
		save()
		time.sleep(60.0 - ((time.time() - starttime) %60.0))

if __name__ == "__main__":
	main()
