#Imports
import spidev
import time
from time import sleep
import numpy as np
import statistics as stat
import RPi.GPIO as GPIO

#Define LDR variables
global count
global averageList
delay = 1
count = 0
listSize = 5
ldr_N = 0
ldr_W = 1
ldr_M = 2
ldr_E = 3
ldr_S = 4
ldr_N_List = []
ldr_W_List = []
ldr_M_List = []
ldr_E_List = []
ldr_S_List = []
averageList = []

#Define Servo variables
global servoLastPos_1
global servoLastPos_2
rotationSize = 0.5
servoPin_1 = 10
servoPin_2 = 12
servoLastPos_1 = 8
servoLastPos_2 = 8

#Create SPI
spi = spidev.SpiDev()
spi.open(0, 0)

#Set up Servos
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(servoPin_1, GPIO.OUT)
GPIO.setup(servoPin_2, GPIO.OUT)

#Read LDR data, ADC only has 8 channels
def readData(chanum):
    assert 0 <= chanum <= 7, "Channel number outside of acceptable range"
    read = spi.xfer2([1, 8 + chanum << 4, 0])
    data = ((read[1] & 3) << 8) + read[2]
    assert data > 100, "LDR returned very low value, please check LDR wiring"
    return data

#Remove outliers then calculate average LDR data value
def calculateAverage(dataList):
    newList = []
    dataList.sort()
    q1, q3 = np.percentile(dataList, [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        iqr = 1
    lb = q1 - (1.5 * iqr)
    ub = q3 + (1.5 * iqr)
    for i in range(len(dataList)):
        if dataList[i] in range(int(lb), int(ub)):
            newList.append(dataList[i])
    average = stat.mean(newList)
    dataList.clear()
    return average

#Collect LDR data
def collectData():
    print("Collecting Data...")
    global count
    global averageList
    if count < listSize:
        count += 1
        ldr_N_List.append(readData(ldr_N))
        ldr_W_List.append(readData(ldr_W))
        ldr_M_List.append(readData(ldr_M))
        ldr_E_List.append(readData(ldr_E))
        ldr_S_List.append(readData(ldr_S))
        time.sleep(delay)
    else:
        count = 0
        aveNor = calculateAverage(ldr_N_List)
        aveWest = calculateAverage(ldr_W_List)
        aveMid = calculateAverage(ldr_M_List)
        aveEast = calculateAverage(ldr_E_List)
        aveSou = calculateAverage(ldr_S_List)
        print("------")
        print("North = %d" % aveNor)
        print("West = %d" % aveWest)
        print("Middle = %d" % aveMid)
        print("East = %d" % aveEast)
        print("South = %d" % aveSou)
        print("------")
        averageList.append(aveNor)
        averageList.append(aveWest)
        averageList.append(aveMid)
        averageList.append(aveEast)
        averageList.append(aveSou)

#Set both servos to 90 degree positions
def servoToNeutralPos():
    pwm_1 = GPIO.PWM(servoPin_1, 50)
    pwm_1.start(8)
    sleep(0.5)
    pwm_1.stop()
    pwm_2 = GPIO.PWM(servoPin_2, 50)
    pwm_2.start(8)
    sleep(0.5)
    pwm_2.stop()

#Rotate servo 1 to make sensor rotate north
def rotateNorth():
    global servoLastPos_1
    if (servoLastPos_1 > 3.5):
        pwm_1 = GPIO.PWM(servoPin_1, 50)
        pwm_1.start(servoLastPos_1)
        sleep(0.5)
        newPos_1 = servoLastPos_1 - rotationSize
        pwm_1.ChangeDutyCycle(newPos_1)
        sleep(0.5)
        pwm_1.stop()
        servoLastPos_1 = newPos_1
        print("Moving North")

#Rotate servo 1 to make sensor rotate south
def rotateSouth():
    global servoLastPos_1
    if (servoLastPos_1 < 11.5):
        pwm_1 = GPIO.PWM(servoPin_1, 50)
        pwm_1.start(servoLastPos_1)
        sleep(0.5)
        newPos_1 = servoLastPos_1 + rotationSize
        pwm_1.ChangeDutyCycle(newPos_1)
        sleep(0.5)
        pwm_1.stop()
        servoLastPos_1 = newPos_1
        print("Moving South")

#Rotate servo 2 to make sensor rotate east
def rotateEast():
    global servoLastPos_2
    if (servoLastPos_2 > 3.5):
        pwm_2 = GPIO.PWM(servoPin_2, 50)
        pwm_2.start(servoLastPos_2)
        sleep(0.5)
        newPos_2 = servoLastPos_2 - rotationSize
        pwm_2.ChangeDutyCycle(newPos_2)
        sleep(0.5)
        pwm_2.stop()
        servoLastPos_2 = newPos_2
        print("Moving East")

#Rotate servo 2 to make sensor rotate west
def rotateWest():
    global servoLastPos_2
    if (servoLastPos_1 < 11.5):
        pwm_2 = GPIO.PWM(servoPin_2, 50)
        pwm_2.start(servoLastPos_2)
        sleep(0.5)
        newPos_2 = servoLastPos_2 + rotationSize
        pwm_2.ChangeDutyCycle(newPos_2)
        sleep(0.5)
        pwm_2.stop()
        servoLastPos_2 = newPos_2
        print("Moving West")

#Decides which direction the sensor should rotate
def moveSensor(List):
    for i in List:
        if i == 0:
            rotateNorth()
        if i == 1:
            rotateWest()
        if i == 3:
            rotateEast()
        if i == 4:
            rotateSouth()

#Main
servoToNeutralPos()
try:
    while True:
        collectData()
        if len(averageList) > 0:
            indexes = [i for i, x in enumerate(averageList) if x < (min(averageList) + 25)]
            moveSensor(indexes)
            averageList = []
except KeyboardInterrupt:
    print("Process Stopped")
