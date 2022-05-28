# Moxy Sensor Python script to read from device

This guide has been prepared to enable the Python developers to connect to the device then, pull the data and decode the it.
There is an article published on mdpi with the title : Muscle Oxygen Desaturation and Re-Saturation Capacity Limits in Repeated Sprint Ability Performance in Women Soccer Players: A New Physiological Interpretation. (https://www.mdpi.com/1660-4601/18/7/3484)

# Connection and wiring
I have created this tutorial to help the developers use Python to decode Hear Rate and Muscle Oxygentation (SmO2) factors. First, To be able to get connected to the device, you need a ANT Serial/Analog Converter (https://www.moxymonitor.com/product/ant-to-serial-converter/). The sensor will be connected to the converter by ANT+ wireless protocol automatically when it turns on. Second, the converter needs to be connected to the PC by a USB-Micro cable. ANT Serial/Analog Converter is able to connect to multiple sensors according the Moxy's documentation. 

# Code Explanation
Moxy company (https://www.moxymonitor.com/) has provided the Matlab code (https://my.moxymonitor.com/hubfs/documents/ANT%20Analog%20Manual.pdf) but there was a gap for Python developers to be able to use the device. So, this tutorial is for them. This code written to connect to 2 sensors and read one of the profiles from each sensor. Finally, I have stored the data into the sqlite database for future.

| ANT+ Profile | Abbreviation | Profile Number | Value Range |
| :---: | :---: | :---: | :---: | 
| NONE | NONE | 0 | 0 |
| Muscle Oxygen | MO2 | 1 | 0% to 100% |
| Heart Rate | HR | 2 | 0 to 256 BPM |

