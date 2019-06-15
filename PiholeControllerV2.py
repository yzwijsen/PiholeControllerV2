#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import subprocess
import select
import os
import signal
import atexit

# Settings
alertPin = 25
statusPin = 24
buttonPin = 23
disableDuration = "30m"
logFile = "/var/log/pihole.log"
matchString = "/etc/pihole/gravity.list"
falsePos = "read /etc/pihole/gravity.list"
disableFile = "/etc/pihole/gravity.list.bck"

# Functions
def button_callback(channel):
    print("Button was pressed!")

    if piholeIsEnabled():
        subprocess.call('/usr/local/bin/pihole disable ' + str(disableDuration), shell=True)
    else:
        subprocess.call('/usr/local/bin/pihole enable', shell=True)

def checkLogTailResult():
    if p.poll(1):
        line = f.stdout.readline()
        if matchString in line:
            if falsePos not in line:
                alert(line)

def checkPiholeStatus():
    if piholeIsEnabled():
        GPIO.output(statusPin, GPIO.HIGH)
    else:
        GPIO.output(statusPin, GPIO.LOW)

def piholeIsEnabled():
    return not os.path.isfile(disableFile)

def alert(logLine, blinkTime = .2):
    print("Ad Blocked!  ==>  " + logLine)
    GPIO.output(alertPin, GPIO.HIGH)
    time.sleep(blinkTime)
    GPIO.output(alertPin, GPIO.LOW)
    #make sure led blinks instead of staying on continuously when multiple ads are blocked in short succession
    time.sleep(.1)

def handleExit():
    print("Cleaning up GPIO...")
    GPIO.output(alertPin, GPIO.LOW)
    GPIO.output(statusPin, GPIO.LOW)
    GPIO.cleanup()

# Bind exit function
atexit.register(handleExit)
signal.signal(signal.SIGTERM, handleExit)
signal.signal(signal.SIGINT, handleExit)

# Setup GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(alertPin, GPIO.OUT)
GPIO.setup(statusPin, GPIO.OUT)
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(buttonPin, GPIO.RISING, callback=button_callback, bouncetime=1000)

# Tail Pihole logfile
f = subprocess.Popen(['tail','-F',logFile],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
p = select.poll()
p.register(f.stdout)

# Main loop
while True:
    checkPiholeStatus()
    checkLogTailResult()    
    #reduces load on rpi
    time.sleep(.1)
    