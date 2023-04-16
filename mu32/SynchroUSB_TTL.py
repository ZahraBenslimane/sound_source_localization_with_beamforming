#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 14:20:01 2020

@author: francois

"""
"""
sudo su
//type your password
cd /
cd dev
chown username ttyUSB0 ou 1
"""
import serial

ser = serial.Serial('/dev/ttyUSB0')  # open serial port
print(ser.name)         # check which port was really used
ser.write(b'0')     # write a string
ser.close()             # close port
