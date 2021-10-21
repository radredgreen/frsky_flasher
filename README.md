

# Introduction

frsky_flasher.py is a flash firmware programmer for programming firmware updates to frsky products through the s.port interface.  It is useful for: 
* Updating frsky product firmware from Linux
* If you don't have access to a windows computer for running the frsky stk tool 
* If you don't have access to an opentx transmitter (you're using an older PPM transmitter)
* If you prefer an opensource implementation of the firmware flasher

For now, this tool only works with python2, not python3.

This tool was created, from scratch in python, by reviewing the opentx software, specifically frsky_firmware_update.cpp

# Alternatives
* OpenTX (https://www.open-tx.org/) allows you to flash s.port products directly from the transmitter
* frsky stk (s.port tool kit) allows you to flash s.port products from windows

# Cable
To use this, you'll need to build or buy a cable
* Frsky sells a stk cable which I believe presents itself to linux as a serial port which can be used with this software
* You can build a converter as described here: https://hackaday.io/project/27894-frsky-smartport-inverter.  This was the path I choose since the R9MM has an inverted s.port the selection resistors and supply voltages seemed finicky.  I ended with a 22k pull up resistor to 5 volts.
* You can build a converter as described here: https://www.rcgroups.com/forums/showthread.php?2204986-Update-FrSky-XJT-module-with-FTDI-cable-and-diode.  I would recommend this method if you have a device that uses a non-inverted sport.

# Usage
Install PyCRC: pip install pythoncrc

Install PySerial: pip install PySerial

Download frsky firmware (.frk file) for your device

Connect programming cable

Execute: ./frsky_flasher.py firmware.frk /dev/ttyUSB0

# Testing
frsky_flasher has been tested with the R9M transmit module (front and back s.port) and the R9MM receiver.
If you have success or failures with other devices, open an issue to track compatibility with other s.port devices.

# Tips
* The programmer needs to send a command to the bootloader at device power up to enter programming mode.  Follow the instructions in the program for (re)connecting the device to trigger the bootloader at power up. Watch the official youtube videos for a demonstration of the power up procedure
* With the R9M, connecting power to the module can cause the usb to serial adaptor (ch341) to reboot.  Powering the module from a battery resolved this, but power to the battery had to be disconnected and reconnected at the beginning of the programming sequence to catch the bootloader.



