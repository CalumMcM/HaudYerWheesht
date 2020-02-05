from bme280 import BME280
from Adafruit_IO import Client, Feed, RequestError
from enviroplus import gas
from PIL import Image, ImageDraw, ImageFont
from gpiozero import Button

import cayenne.client
import ST7735
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

	curTime = time.strftime("%d/%m/%y,%H:%M", time.localtime())	
	
	return compTemp, humidity, nh3, no2, light, proxim, pressure, curTime

def save():
	file = open("data.txt", "a")
	
	temp, humidity, nh3, no2, light, proxim, pressure, curTime = output()

	line = curTime + "," + str(temp) + "," + str(humidity) + "," + str(nh3) + "," + str(no2)	
	line += "," + str(light) + "," + str(proxim) + "," + str(pressure) + "\n"

	file.write(line)

	file.close()

	print (line)

def display(var, time, runtime):
	disp = ST7735.ST7735(
		port=0,
		cs=1,
		dc=9,
		backlight=12,
		rotation=270,
		spi_speed_hz=10000000
	)
	disp.begin
	
	img = Image.new('RGB', (disp.width, disp.height), color=(0,0,0))
	draw = ImageDraw.Draw(img)
	
	font_size = 24
	font = ImageFont.truetype("Asap-Bold.ttf", font_size)
	midFont = ImageFont.truetype("Asap-Bold.ttf", 20)

	if (var < 5):
		rect_colour = (0,250,200)
		text_colour = (250, 0, 200)
	elif (var < 9):
		rect_colour = (250,190,0)
		text_colour = (0, 190, 250)
	else:
		rect_colour = (250,0,0)
		text_colour = (0, 250, 250)

	draw.rectangle((0,0,160,80), rect_colour)
	draw.text((0, 0), time, font=font, fill=text_colour)
	draw.text((disp.width/2-75, disp.height/2-5), "Current run time:", font=midFont, fill=text_colour)
	draw.text((disp.height/2 - 30, disp.width/2 - 30), runtime, font=font, fill=text_colour)

	disp.display(img)

def send_on():
  #Publish "1" to Cayenne MQTT Broker Channel 3
  print("Button pressed\n")

def send_off():
  client.virtualWrite(3, 0) #Publish "0" to Cayenne MQTT Broker Channel 3
  print("Button released\n")

def main():

	# Cayenne authentication info. This should be obtained from the Cayenne Dashboard.
	MQTT_USERNAME  = "ced46c60-47fc-11ea-ba7c-716e7f5ba423"
	MQTT_PASSWORD  = "5e41e78b454da9993ca069405291cfa4bf103293"
	MQTT_CLIENT_ID = "cd803190-47fd-11ea-84bb-8f71124cfdfb"
	
	client = cayenne.client.CayenneMQTTClient()

	client.begin(MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID)

	"""
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
	"""

	starttime = time.time()
	temp, hum, nh3, no2, light, proxim, pressure, curTime = output()
	oldTemp, oldHum, oldNh3, oldNo2, oldLight, oldProxim, oldPressure = temp, hum, nh3, no2, light, proxim, pressure
	while True:
		client.loop()

		client.celsiusWrite(1, temp)
		client.virtualWrite(2, hum)
		client.virtualWrite(3, no2)	
		client.virtualWrite(4, nh3)
		client.luxWrite(5, light)
		# client.virtualWrite(6, proxim)

		if (pressure < 700):
			client.virtualWrite(7, oldPressure)
		else:
			client.virtualWrite(7, pressure)
			oldPressure = pressure

		save()

		timeDiff = time.localtime(time.time() - starttime - 3600)
		runTime = time.strftime("%H:%M", timeDiff)	
		
		display(light, curTime, runTime)

		time.sleep(60.0 - ((time.time() - starttime) %60.0))

		oldTemp, oldHum, oldNh3, oldNo2, oldLight, oldProxim = temp, hum, nh3, no2, light, proxim
		temp, hum, nh3, no2, light, proxim, pressure, curTime = output()

	while(True):
		"""
		aio.send(tempThread.key, temp)
		aio.send(humidityThread.key, hum)
		aio.send(no2Thread.key, no2)
		aio.send(nh3Thread.key, nh3)
		aio.send(lightThread.key, light)
		aio.send(proximThread.key, proxim)
		
		if (pressure < 700):
			aio.send(pressureThread.key, oldPressure)
		else:
			aio.send(pressureThread.key, pressure)
			oldPressure = pressure

		print (oldPressure)	
		save()

		timeDiff = time.localtime(time.time() - starttime - 3600)
		runTime = time.strftime("%H:%M", timeDiff)	
		
		"""
		display(light, curTime, runTime)
	
		time.sleep(60.0 - ((time.time() - starttime) %60.0))
		oldTemp, oldHum, oldNh3, oldNo2, oldLight, oldProxim = temp, hum, nh3, no2, light, proxim
		temp, hum, nh3, no2, light, proxim, pressure, curTime = output()

if __name__ == "__main__":
	main()
