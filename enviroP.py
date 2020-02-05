from bme280 import BME280
from enviroplus import gas
from PIL import Image, ImageDraw, ImageFont

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

	# Get Temperature, pressure and humidity
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

	# Get gases
	gases = gas.read_all()
	nh3 = gases.nh3
	no2 = gases.oxidising

	# Get light and proximity
	light = ltr559.get_lux()
	proxim = ltr559.get_proximity()

	# Calculate current time as string
	curTime = time.strftime("%d/%m/%y,%H:%M", time.localtime())	
	
	return compTemp, humidity, nh3, no2, light, proxim, pressure, curTime

# Writes all values returned by output() to "data.txt"
def save():
	file = open("data.txt", "a")
	
	temp, humidity, nh3, no2, light, proxim, pressure, curTime = output()

	line = curTime + "," + str(temp) + "," + str(humidity) + "," + str(nh3) + "," + str(no2)	
	line += "," + str(light) + "," + str(proxim) + "," + str(pressure) + "\n"

	file.write(line)

	file.close()
# Outputs current runtime to the Enviro+ display as well as 
# having the screen change between traffic colours depending
# on a given variable (var)
def display(var, time, runtime):
	# Opens the display for writing to
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
	
	# Construct font types
	fontSizeHeader = 24
	fontSizePara = 20
	fontHeader = ImageFont.truetype("Asap-Bold.ttf", fontSizeHeader)
	fontPara = ImageFont.truetype("Asap-Bold.ttf", fontSizePara)

	# Depending on var apply traffic light colours
	# Currently configured for light
	if (var < 5):
		rect_colour = (0,250,200)
		text_colour = (250, 0, 200)
		
	elif (var < 9):
		rect_colour = (250,190,0)
		text_colour = (0, 190, 250)
		
	else:
		rect_colour = (250,0,0)
		text_colour = (0, 250, 250)

	# Output all values to the display
	draw.rectangle((0,0,160,80), rect_colour)
	draw.text((0, 0), time, font=fontHeader, fill=text_colour)
	draw.text((disp.width/2-75, disp.height/2-5), "Current run time:", font=fontPara, fill=text_colour)
	draw.text((disp.height/2 - 30, disp.width/2 - 30), runtime, font=fontHeader, fill=text_colour)

	disp.display(img)

def main():

	# Cayenne authentication info
	MQTT_USERNAME  = "ced46c60-47fc-11ea-ba7c-716e7f5ba423"
	MQTT_PASSWORD  = "5e41e78b454da9993ca069405291cfa4bf103293"
	MQTT_CLIENT_ID = "cd803190-47fd-11ea-84bb-8f71124cfdfb"
	
	client = cayenne.client.CayenneMQTTClient()

	client.begin(MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID)

	# Initialise all variables
	starttime = time.time()
	temp, hum, nh3, no2, light, proxim, pressure, curTime = output()
	oldTemp, oldHum, oldNh3, oldNo2, oldLight, oldProxim, oldPressure = temp, hum, nh3, no2, light, proxim, pressure
	
	while True:
		# Send values to Cayenne
		client.loop()

		client.celsiusWrite(1, temp)
		client.virtualWrite(2, hum)
		client.virtualWrite(3, no2)	
		client.virtualWrite(4, nh3)
		client.luxWrite(5, light)
		# client.virtualWrite(6, proxim)

		# Filter inaccurate pressure readings
		if (pressure < 700):
			client.virtualWrite(7, oldPressure)
		else:
			client.virtualWrite(7, pressure)
			oldPressure = pressure

		save()

		# Calculate how long the program has been running for
		timeDiff = time.localtime(time.time() - starttime - 3600)
		runTime = time.strftime("%H:%M", timeDiff)	
		
		display(light, curTime, runTime)

		# Have the program send values once every minute
		time.sleep(60.0 - ((time.time() - starttime) % 60.0))

		# Update values
		oldTemp, oldHum, oldNh3, oldNo2, oldLight, oldProxim = temp, hum, nh3, no2, light, proxim
		temp, hum, nh3, no2, light, proxim, pressure, curTime = output()

if __name__ == "__main__":
	main()
