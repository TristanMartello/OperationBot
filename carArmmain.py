import mqtt
import network, ubinascii
from machine import Pin
from StepperClass import Stepper
from ServoLib import Servo
from arcServo import ArcServo
import wifiLib
import secrets
import time

locationKey = "tufts"
armDirection = "halt"
driveDirection = "halt"

bigAngleInc = 0.25

dropCountdown = 0
dropDir = True

# When motor message received, update global direction variable
def whenCalled(topic, msg):
    global armDirection, driveDirection, dropCountdown, dropDir
    top = topic.decode()
    ms = msg.decode()
    if top == "arm":
        armDirection = ms
    elif top == "drive":
        driveDirection = ms
    elif top == "drop":
        dropDir = not dropDir
        dropCountdown = 50

# Interpret instructions for car driving movement
def driveLoop(lmotor, rmotor):
    if driveDirection == "halt":
        lmotor.stop()
        rmotor.stop()
    elif driveDirection == "forward":
        lmotor.reverse()
        rmotor.forward()
    elif driveDirection == "right":
        lmotor.reverse()
        rmotor.reverse()
    elif driveDirection == "left":
        lmotor.forward()
        rmotor.forward()
    elif driveDirection == "reverse":
        lmotor.forward()
        rmotor.reverse()

# Activate bucket when triggered
def handleBucket(bucket):
    global dropCountdown
    if dropCountdown > 0:
        if dropCountdown % 5 == 0:
            if dropDir:
                bucket.forward()
            else:
                bucket.reverse()
        dropCountdown -= 1
    else:
        bucket.stop()

# Overall motor control loop 
def motorLoop(broker, stepper, lmotor, rmotor, bigBoy, bucket):
    try:
        bigAngle = 0
        listen = True
        while listen:  # Loop for steering instructions
            broker.check_msg()
            if armDirection == "halt":
                print("halt")
                stepper.stop()
                
            # Stepper instructions
            elif armDirection == "left":
                print("left")
                stepper.counterClockwise()
            elif armDirection == "right":
                print("right")
                stepper.clockwise()
            
            # Big Servo instructions
            elif armDirection == "up":
                print("up")
                bigAngle = min(bigAngle + bigAngleInc, 110)
                print("   ", bigAngle)
                bigBoy.move(bigAngle)
            elif armDirection == "down":
                print("down")
                bigAngle = max(bigAngle - bigAngleInc, -110)
                print("   ", bigAngle)
                bigBoy.move(bigAngle)
            
            # Handle bucket and car instructions
            handleBucket(bucket)
            driveLoop(lmotor, rmotor)
            time.sleep(0.002)
    except Exception as e:
        print(repr(e))
        print("drive fail")

def controlLoop(broker):
    # Initialize motors
    stepper = Stepper(21, 20, 19, 18)
    lmotor = Servo(12)
    rmotor = Servo(13)
    bucket = Servo(15)
    bigBoy = ArcServo(14)
    
    # Start big control loop
    timeLimit = 60000
    motorLoop(broker, stepper, lmotor, rmotor, bigBoy, bucket)
    
    # Deinitialize motors
    lmotor.destroy()
    rmotor.destroy()
    bucket.destroy()
    broker.disconnect()
    print('done')

def main():
    # Set up wifi and mqtt
    wifiLib.connect_wifi(locationKey)
    try:
        broker = mqtt.MQTTClient('CarPico', secrets.returnIp(locationKey), keepalive=6000)
        print('Connected')
        broker.connect()
        broker.set_callback(whenCalled)
    except OSError as e:
        print('Failed')
        return
    
    # Subscribe to mqtt channels
    broker.subscribe('arm')
    broker.subscribe('drive')
    broker.subscribe('drop')
    
    # Begin control loop
    controlLoop(broker)
    print("done")

main()

