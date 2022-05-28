# Moxy Sensor Python script to read from device

This guide has been prepared to enable the Python developers to connect to the device then, pull the data and decode the it.
There is an article published on mdpi with the title : Muscle Oxygen Desaturation and Re-Saturation Capacity Limits in Repeated Sprint Ability Performance in Women Soccer Players: A New Physiological Interpretation. (https://www.mdpi.com/1660-4601/18/7/3484)

# Connection and wiring
I have created this tutorial to help the developers use Python to decode Hear Rate and Muscle Oxygentation (SmO2) factors. First, To be able to get connected to the device, you need a ANT Serial/Analog Converter (https://www.moxymonitor.com/product/ant-to-serial-converter/). The sensor will be connected to the converter by ANT+ wireless protocol automatically when it turns on. Second, the converter needs to be connected to the PC by a USB-Micro cable. 

# Code
Moxy company (https://www.moxymonitor.com/) has provided the Matlab code (https://my.moxymonitor.com/hubfs/documents/ANT%20Analog%20Manual.pdf) but there was a gap for Python developers to be able to use the device. So, this tutorial is for them.

| ANT+ Profile | Abbreviation | Profile Number | 
| :---: | :---: | :---: | 
| NONE | NONE | 0 |
| Muscle Oxygen | MO2 | 1 |
| Heart Rate | HR | 2 |
| :---: | :---: | :---: | 


