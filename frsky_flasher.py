#!/usr/bin/python

# frsky_flasher.py a flash programmer for frsky s.port products
#
# Copyright (C) RadRedGreen
#
# License GPLv2: http://www.gnu.org/licenses/gpl-2.0.html
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#

import sys
import time
import serial
from PyCRC.CRCCCITT import CRCCCITT
import struct

PRIM_REQ_POWERUP 	= b'\x00'
PRIM_REQ_VERSION 	= b'\x01'
PRIM_CMD_DOWNLOAD 	= b'\x03'
PRIM_DATA_WORD 		= b'\x04'
PRIM_DATA_EOF 		= b'\x05'

PRIM_ACK_POWERUP	= b'\x80'
PRIM_ACK_VERSION	= b'\x81'
PRIM_REQ_DATA_ADDR	= b'\x82'
PRIM_END_DOWNLOAD	= b'\x83'
PRIM_DATA_CRC_ERR	= b'\x84'

Tx_SOF 				= b'\x7E\xFF'
Rx_SOF 				= b'\x7E\x5e'
HEADBYTE			= b'\x50'

FRAME_SIZE			= 8
MAX_FRAME_SIZE		= 19
EMPTY_FRAME			= b'\x00\x00\x00\x00\x00\x00\x00'

debug = False

def formatHex(input):
	return ":".join("{:02x}".format(ord(c)) for c in input )

def sendFrame(frame, ser):
	#print "Frame: " + formatHex(frame)
	assert len(frame) == FRAME_SIZE - 1
	frame_crc = struct.pack(">H",CRCCCITT().calculate(frame))
	frame = frame + frame_crc[1]
	txData = Tx_SOF
	for i in range(FRAME_SIZE):
		if frame[i] == b'\x7e':
				txData = txData + b'\x7d'
				txData = txData + b'\x5e'
		elif frame[i] == b'\x7d':
				txData = txData + b'\x7d'
				txData = txData + b'\x5d'
		else: 
				txData = txData + frame[i]

	if debug:
		print "Sending: " + formatHex(txData)

	ser.write(txData)
	ser.flush()

	for i in range(20):
		rxData = ser.read(2*MAX_FRAME_SIZE)
		if debug:
			print "Received: " + formatHex(rxData)
		#Discard our own sent data if present
		if len(rxData) > 2 and rxData[0:2] == Tx_SOF:
			rxData = rxData[len(txData):]
		if len(rxData)>=FRAME_SIZE:
			break
	if len(rxData) < 2:
		return ''
	if rxData[0:2] != Rx_SOF:
		return ''
	rxData = rxData[2:]
	if rxData[1] == PRIM_DATA_CRC_ERR:
		print "Device reported CRC error"

	i = 0
	rxDataUnstuff = ''	
	while(i<len(rxData)):
		if rxData[i] == b'\x7d':
			if rxData[i+1] == b'\x5e':
				rxDataUnstuff = rxDataUnstuff + b'\x7e'
				i=i+2
			elif rxData[i+1] == b'\x5d':
				rxDataUnstuff = rxDataUnstuff + b'\x7d'
				i=i+2
		else: 
			rxDataUnstuff = rxDataUnstuff + rxData[i]
			i=i+1
	rxCRC = struct.pack(">H",CRCCCITT().calculate(rxDataUnstuff[0:7]))
	#print "RX Data Unstuff: " + formatHex(rxDataUnstuff)
	if rxCRC[0] != rxDataUnstuff[7]:
		print "Received CRC error"
	return rxDataUnstuff


def main(firmwareFile, serialPort):
	with open(firmwareFile, "rb") as file:
		firmware = file.read()

	append = (4-(len(firmware)%4))%4
	if debug:
		print "Appending " + str(append) + " bytes to make the firmware a multiple of 4 bytes long"
	for i in range(append):
		firmware = firmware + b'\x00'

	with serial.Serial(serialPort, 57600, timeout=0.04,parity=serial.PARITY_NONE, rtscts=0) as ser:
	
		print "(Re)connect device to programming cable"
		print "Sending power up REQ..."
		while True:
			frame=list(EMPTY_FRAME)
			frame[0]=HEADBYTE
			frame[1]=PRIM_REQ_POWERUP
			response = sendFrame("".join(frame), ser)
			if len(response) >= 8 and response[0] == HEADBYTE and response[1] == PRIM_ACK_POWERUP:
				break

		time.sleep(1)
		frame=list(EMPTY_FRAME)
		frame[0]=HEADBYTE
		frame[1]=PRIM_REQ_POWERUP
		response = sendFrame("".join(frame), ser)
		if len(response) >= 8 and response[0] == HEADBYTE and response[1] == PRIM_ACK_POWERUP:
			print "Second power up ACK not received"
			return(-1)

		print "Received Powerup ACK"
		time.sleep(1)
		print "Requesting Version"
		frame=list(EMPTY_FRAME)
		frame[0]=HEADBYTE
		frame[1]=PRIM_REQ_VERSION
		response = sendFrame("".join(frame), ser)
		if not(len(response) >= 8 and response[0] == HEADBYTE and response[1] == PRIM_ACK_VERSION):
			print "Version ACK not received"
			return(-1)
		print "Version ACK received, reported version: " + formatHex(response[2:6])
		time.sleep(1)
		print "Sending Download Command"
		frame=list(EMPTY_FRAME)
		frame[0]=HEADBYTE
		frame[1]=PRIM_CMD_DOWNLOAD
		response = sendFrame("".join(frame), ser)
		if not(len(response) >= 8 and response[0] == HEADBYTE and response[1] == PRIM_REQ_DATA_ADDR):
			print "Data refused by device"
			return(-1)

		print "Beginning Download, do not interrupt..."
		address = struct.unpack("<i",response[2:6])
		address = address[0]
		while(address < len(firmware)):
			frame=list(EMPTY_FRAME)
			frame[0]=HEADBYTE
			frame[1]=PRIM_DATA_WORD
			frame[2]=firmware[address]
			frame[3]=firmware[address+1]
			frame[4]=firmware[address+2]
			frame[5]=firmware[address+3]
			frame[6]=struct.pack("B",address % 256)
			response = sendFrame("".join(frame), ser)
			if not(len(response) >= 8 and response[0] == HEADBYTE and response[1] == PRIM_REQ_DATA_ADDR):
				print "Data refused by device"
				return(-1)
			address = struct.unpack("<i",response[2:6])
			address = address[0]
			if debug:
				print "Address: " + str(address)
			else:
				if address % 1024 == 0:
					print str(round(float(address)/float(len(firmware))*100,2)) + "% complete"

		print "Sending End of File"
		frame=list(EMPTY_FRAME)
		frame[0]=HEADBYTE
		frame[1]=PRIM_DATA_EOF
		response = sendFrame("".join(frame), ser)
		if not(len(response) >= 8 and response[0] == HEADBYTE and response[1] == PRIM_END_DOWNLOAD):
			print "Firmware Rejected"
			return(-1)

		print "Firmware flashing complete"
		return(0)

if __name__ == "__main__":
	print sys.argv[1]
	if len(sys.argv) != 3:
		print "Usage: frsky_flasher.py firmwareFile serialPort"
		exit()
	firmwareFile = sys.argv[1]
	serialPort = sys.argv[2]
	sys.exit(main(firmwareFile, serialPort))


