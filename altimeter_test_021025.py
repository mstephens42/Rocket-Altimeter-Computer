from machine import Pin, I2C, Timer
from bmp280 import *
import time
import math

class RocketAltimeter:
    def __init__(self):
        self.heights = []
        self.times = []
        self.max_height = 0
        self.speed = 0
        self.max_speed = 0
        self.acceleration = 0
        self.max_acceleration = 0
        self.max_data_points = 100  # Limit the number of data points stored

    def convert_pressure_to_height(self, p_bar):
        return (1 - (p_bar * 750.062 / 760) ** (1/5.25588)) * 145366.45

    def record_height_from_pressure(self, p_bar):
        try:
            height_ft = self.convert_pressure_to_height(p_bar)
            current_time = time.time()
            
            # Update heights and times
            self.heights.append(height_ft)
            self.times.append(current_time)

            # Limit the number of data points stored
            if len(self.heights) > self.max_data_points:
                self.heights.pop(0)
                self.times.pop(0)

            # Calculate maximum height
            if height_ft > self.max_height:
                self.max_height = height_ft
            
            # Calculate speed and acceleration
            if len(self.heights) > 1:
                delta_height = self.heights[-1] - self.heights[-2]
                delta_time = self.times[-1] - self.times[-2]
                
                if delta_time > 0:
                    # Speed in feet per second
                    self.speed = delta_height / delta_time
                    
                    # Update maximum speed
                    if self.speed > self.max_speed:
                        self.max_speed = self.speed
                    
                    if len(self.heights) > 2:
                        previous_delta_height = self.heights[-2] - self.heights[-3]
                        previous_delta_time = self.times[-2] - self.times[-3]

                        if previous_delta_time > 0:
                            delta_speed = self.speed - (previous_delta_height / previous_delta_time)
                            self.acceleration = delta_speed / delta_time
                            
                            # Update maximum acceleration
                            if self.acceleration > self.max_acceleration:
                                self.max_acceleration = self.acceleration
                        else:
                            self.acceleration = 0
                else:
                    self.speed = 0
                    self.acceleration = 0
        except Exception as e:
            print(f"An error occurred: {e}")
            self.speed = 0
            self.acceleration = 0

    def reset_data(self):
        self.heights = []
        self.times = []
        self.max_height = 0
        self.speed = 0
        self.max_speed = 0
        self.acceleration = 0
        self.max_acceleration = 0
        print("Altimeter data reset")

    def get_max_height(self):
        return self.max_height

    def get_speed(self):
        return self.speed

    def get_speed_mph(self):
        return self.speed * 0.681818  # Convert ft/s to MPH

    def get_max_speed(self):
        return self.max_speed

    def get_acceleration(self):
        return self.acceleration

    def get_max_acceleration(self):
        return self.max_acceleration

    def get_current_height(self):
        return self.heights[-1] if self.heights else 0

# MicroPython sensor setup
sdaPIN = machine.Pin(0)
sclPIN = machine.Pin(1)
bus = I2C(0, sda=sdaPIN, scl=sclPIN, freq=400000)
time.sleep(0.1)
bmp = BMP280(bus)

bmp.use_case(BMP280_CASE_INDOOR)

# Create an instance of the RocketAltimeter
altimeter = RocketAltimeter()

# Setup reset button (assume connected to GPIO pin 2)
reset_button = Pin(2, Pin.IN, Pin.PULL_UP)

# Timer to print values every second
def print_metrics(timer):
    current_height = altimeter.get_current_height()
    print(f"Current Height: {current_height:.2f} feet")
    print(f"Maximum Height: {altimeter.get_max_height():.2f} feet")
    print(f"Speed: {altimeter.get_speed():.2f} feet/second ({altimeter.get_speed_mph():.2f} MPH)")
    print(f"Maximum Speed: {altimeter.get_max_speed():.2f} feet/second")
    print(f"Acceleration: {altimeter.get_acceleration():.2f} feet/second²")
    print(f"Maximum Acceleration: {altimeter.get_max_acceleration():.2f} feet/second²")

# Initialize timer
timer = Timer(-1)
timer.init(period=1000, mode=Timer.PERIODIC, callback=print_metrics)

while True:
    try:
        # Check if reset button is pressed
        if reset_button.value() == 0:
            altimeter.reset_data()

        pressure = bmp.pressure
        p_bar = pressure / 100000
        temperature = bmp.temperature
        # print("Temperature: {} C".format(temperature))
        # print("Pressure: {} Pa, {} bar, {} mmHg".format(pressure, p_bar, p_mmHg))

        # Record height and update metrics
        altimeter.record_height_from_pressure(p_bar)

        # Run the algorithm faster in the background
        time.sleep(0.1)  # Adjust the sleep interval as needed

    except Exception as e:
        print(f"An error occurred in the main loop: {e}")
        time.sleep(1)  # Pause for a moment before retrying
