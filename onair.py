# -*- coding: utf-8 -*-
#----< Table 1 >---------------------------------------------------------------
#
#	[ SSL1 ]	[ SSL0 ]	[	Search Stop Level	]
#		0			0		not allowed in search mode
#		0			1		low;  level ADC output =  5
#		1			0		mid;  level ADC output =  7
#		1			1		high; level ADC output = 10
#
#----< Table 2 >---------------------------------------------------------------
#
#	[ PLL/REF ]	[ XTAL ]	[	Clock Frequency 	]
#		0			0			13.000	MHz
#		0			1			32.768	kHz
#		1			0			 6.500	MHz
#		1			1			not allowed
#
#------------------------------------------------------------------------------

import sys
if sys.version < '3':
    def byteindex(data, index):
        return ord(data[index])

    def iterbytes(data):
        return (ord (char) for char in data)

else:
    byteindex = lambda x, i: x[i]
    iterbytes = lambda x: iter(x)


import RPi.GPIO as GPIO
import time

# push btn setting
GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

# import the sleep library so we don't have to eat cpu cycles on this device
from time import sleep

# import the quick2wire library to access the i2c bus
import quick2wire.i2c as i2c
from quick2wire.i2c import I2CMaster, writing_bytes, reading

class tea5767:
    """Class to control the operation of a TEA5767 FM radio module over I2C using the quick2wire python3 library"""

    def __init__(self):
        """class constructor"""

        # devices i2c address
        self.address = 0x60

        self.crystalOscillatorFrequency = 32768

        self.FMstation = 98.0

        # number of bytes that can be read and written
        self.numReadBytes = 5
        self.numWriteBytes = 5

        # data that is to be written to the device
        #first byte data
        self.mute = 1
        self.searchMode = 0
        # upper frequency byte defined below

        #second byte data
        # lower frequency byte defined below

        #third byte data
        self.SUD = 1                # 1 = search up					0 = search down
        self.searchStopLevel = 1    # 2 bits; see table 1 above		range ( 1 - 3 )
        self.HLSI = 1                # 1 = high side LO injection	0 = low side LO injection
        self.mono = 0                # 1 = forced mono				0 = stereo mode allowed
        self.muteRight = 0            # 1 = right channel muted		0 = right channel not muted
        self.muteLeft = 0            # 1 = left channel muted		0 = left channel not muted
        self.SWP1 = 0                # 1 = port 1 HIGH				0 = port 1 LOW

        # fourth byte data
        self.SWP2 = 0                # 1 = port 2 HIGH				0 = port 2 LOW
        self.standby = 0            # 1 = standby mode				0 = not in standby mode
        self.bandLimits = 0            # 1 = Japanese FM Band			0 = US/European FM Band
        self.XTAL = 1 if self.crystalOscillatorFrequency == 32768 else 0    # see table 2 above
        self.softMute = 0            # 1 = soft mute on				0 = soft mute off
        self.HCC = 0                # 1 = high cut control is ON	0 = high cut control is OFF
        self.SNC = 0                # 1 = stereo noise canceling	0 = no stereo noise canceling
        self.SI = 0                    # 1 = SWPORT1 is ready output	0 = SWPORT1 is software programmable

        # fifth byte data
        self.PLL = 1 if self.crystalOscillatorFrequency == 6500000 else 0    # see table 2 above
        self.DTC = 0                # 1 = de-emphasis time constant = 75us
        # 0 = de-emphasis time constant = 50us

        # status read from device
        #first byte data
        self.readyFlag = 0
        self.bandLimitFlag = 0
        self.upperFrequencyByte = 0x00

        #second byte data
        self.lowerFrequencyByte = 0x00

        #third byte data
        self.stereoFlag = 0
        self.IFcounter = 0x00

        #fourth byte data
        self.levelADCoutput = 0x00
        self.chipID = 0x00
        # chip ID is set to 0
        # bit 0 is unused

        #fifth byte data
        # these are unused on the 5767

        self.readBytes()
        self.calculateByteFrequency()

    def readBytes(self):
        """read the devices current state"""
        with i2c.I2CMaster() as bus:
            results = bus.transaction(
                reading(self.address, self.numReadBytes)
            )
            # bc = 'on' if c.page=='blog' else 'off'

            # first byte data
            self.readyFlag = 1 if results[0][0] & 0x80 else 0
            self.bandLimitFlag = 1 if results[0][0] & 0x40 else 0
            self.upperFrequencyByte = results[0][0] & 0x3F

            # second byte data
            self.lowerFrequencyByte = results[0][1]

            # third byte data
            self.stereoFlag = 1 if results[0][2] & 0x80 else 0
            self.IFcounter = results[0][2] & 0x7F

            # fourth byte data
            self.levelADCoutput = results[0][3] >> 4
            self.chipID = results[0][3] & 0x0E

            self.calculateFrequency()

    def writeBytes(self):
        """write the data to the device"""

        self.calculateByteFrequency()

        # make sure we initialize everything to avoid possible issues
        byteOne = 0x00
        byteTwo = 0x00
        byteThree = 0x00
        byteFour = 0x00
        byteFive = 0x00

        # first byte
        byteOne = byteOne + 0x80 if self.mute == 1 else byteOne
        byteOne = byteOne + 0x40 if self.searchMode == 1 else byteOne
        byteOne = byteOne + self.upperFrequencyByte

        # second byte
        byteTwo = self.lowerFrequencyByte

        # third byte
        byteThree = byteThree + 0x80 if self.SUD == 1 else byteThree
        byteThree = byteThree + (self.searchStopLevel << 5)
        byteThree = byteThree + 0x10 if self.HLSI == 1 else byteThree
        byteThree = byteThree + 0x08 if self.mono == 1 else byteThree
        byteThree = byteThree + 0x04 if self.muteRight == 1 else byteThree
        byteThree = byteThree + 0x02 if self.muteLeft == 1 else byteThree
        byteThree = byteThree + 0x01 if self.SWP1 == 1 else byteThree

        byteFour = byteFour + 0x80 if self.SWP2 == 1 else byteFour
        byteFour = byteFour + 0x40 if self.standby == 1 else byteFour
        byteFour = byteFour + 0x20 if self.bandLimits == 1 else byteFour
        byteFour = byteFour + 0x10 if self.XTAL == 1 else byteFour
        byteFour = byteFour + 0x08 if self.softMute == 1 else byteFour
        byteFour = byteFour + 0x04 if self.HCC == 1 else byteFour
        byteFour = byteFour + 0x02 if self.SNC == 1 else byteFour
        byteFour = byteFour + 0x01 if self.SI == 1 else byteFour

        # fifth byte data
        byteFive = byteFive + 0x80 if self.PLL == 1 else byteFive
        byteFive = byteFive + 0x40 if self.DTC == 1 else byteFive

        with i2c.I2CMaster() as bus:
            bus.transaction(
                writing_bytes(self.address, byteOne, byteTwo, byteThree, byteFour, byteFive)
            )

    def calculateByteFrequency(self):
        """calculate the upper and lower bytes needed to set the frequency of the FM radio module"""

        frequency = int(4 * (self.FMstation * 1000000 + 225000) / self.crystalOscillatorFrequency)

        self.upperFrequencyByte = int(frequency >> 8)
        self.lowerFrequencyByte = int(frequency & 0xFF)

    def calculateFrequency(self):
        """calculate the station frequency based upon the upper and lower bits read from the device"""

        # this is probably not the best way of doing this but I was having issues with the
        #	frequency being off by as much as 1.5 MHz
        self.FMstation = round((float(round(int(((int(self.upperFrequencyByte) << 8) + int(
            self.lowerFrequencyByte)) * self.crystalOscillatorFrequency / 4 - 22500) / 100000) / 10) - .2) * 10) / 10

    def display(self):
        """print(out all of the information that we are able to collect from the device for debugging"""
        print("")
        print("            Ready Flag = " + str(self.readyFlag))
        print("       Band Limit Flag = " + str(self.bandLimitFlag))
        print("  Upper Frequency Byte = " + hex(self.upperFrequencyByte))
        print("  Lower Frequency Byte = " + hex(self.lowerFrequencyByte))
        print("           Stereo Flag = " + str(self.stereoFlag))
        print("     IF Counter Result = " + str(self.IFcounter))
        print("      Level ADC Output = " + str(self.levelADCoutput))
        print("               Chip ID = " + str(self.chipID))
        print("            FM Station = " + str(self.FMstation) + " MHz")

    def info(self):
        # will return map
        data = {}
        data['freq'] = str(self.FMstation)
        data['stereo'] = str(self.stereoFlag)
        data['level'] = str(self.levelADCoutput)
        return data


    def test(self, b):

        self.mute = 0
        self.standby = 0
        self.bandLimits = 0
        self.FMstation = b
        self.calculateByteFrequency()
        self.writeBytes()

        # allow us to wait until the device is ready to get the correct information
        self.readyFlag = 0
        while (self.readyFlag == 0 and self.standby == 0):
            self.readBytes()
            sleep(0.5)

        print(self.readyFlag)
        print(self.standby)
        # display the updated device information
        self.display()
        return ""

    def search(self):
        self.calculateByteFrequency()
        self.searchMode = 1
        self.bandLimits = 0
        self.mute = 0
        self.standby = 0
        self.readyFlag = 0
        print('Searching: ' + str(self.FMstation))
        self.FMstation = self.FMstation + 0.1
        if self.FMstation > 108:
            self.FMstation = 80
        self.writeBytes()
        while (self.readyFlag == 0 and self.standby == 0):
            self.readBytes()
            sleep(0.5)
            #self.display()
            print('...')

        self.mute = 0
        self.searchMode = 0
        self.bandLimits = 0
        self.writeBytes()
        print('New station: ' + str(self.FMstation))
        #print('Standby: ' + str(self.standby))
        #print('Ready: ' + str(self.readyFlag))
        self.standby = 0

        # allow us to wait until the device is ready to get the correct information
        self.readyFlag = 0
        while (self.readyFlag == 0 and self.standby == 0):
            self.readBytes()
            sleep(0.5)

        self.display()


ch = {825: (97.3, "KBS1 라디오"), 824: ( 93.1, "KBS FM1")
    , 827: (106.1, "KBS2 라디오"), 826: ( 89.1, "KBS FM2")
    , 828: (111, "KBS 사랑의소리")
    , 832: (95.9, "MBC FM"), 831: (  91.9, "MBC FM4U")
    , 834: (103.5, "SBS 러브 FM"), 835: ( 107.7, "SBS 파워 FM")
    , 822 :( 98.1 ,"CBS 표준 FM"), 821: ( 93.9, "CBS 음악 FM")
    , 823: ( 104.5, "EBS 라디오")
    , 820: ( 101.9, "BBS 불교방송"), 837: ( 95.1, "TBS 교통방송")
      # , 'MILITARY': 101.1
      # , 'EASTPOLE': 106.9, 'AFN': 102.7, 'KYUNGKI': 99.9
      # , 'YTNRADIO': 94.5, 'PYNGHWA': 104.5
}

import json, requests
import sys , time
from PIL import Image,ImageDraw,ImageFont
import pcd8544.lcd as lcd

lcd.init()
lcd.cls()

# load an available True Type font
font = ImageFont.truetype("/usr/share/fonts/truetype/unfonts-core/UnBatang.ttf", 14)

# New b-w image

#im = Image.new('1', (84,48))
# New drawable on image
#draw = ImageDraw.Draw(im)

tea = tea5767()
global isHolding
isHolding = False
global old_val
old_val = 0
t = time.time() - 10

url = 'http://music.daum.net/onair/songlist.json?type=top&searchDate='
resp = requests.post(url=url)
data = json.loads(resp.text)

while True:
#    if isHolding :
#lcd.cls()
#lcd.text("Hold")
#time.sleep(1)
    if GPIO.input(14) == 1 and old_val == 0:
        print("Button 1 pressed")
        isHolding = not isHolding
        old_val = 1
        time.sleep(1)
    else :
        old_val = 0

    playList = []
    if time.time() - t > 10 :
        t = time.time()
        print("refresh")
        try:
            resp = requests.post(url=url)
        except:
            print("fail call")
        data = json.loads(resp.text)

        for song in reversed(data['songList']):
            #if song['channel']['channelType'] != "4" or  song['channel']['channelName'] in  ["KBS 사랑의소리","MBC FM4U" ,"CBS 표준 FM"]:
            if song['channel']['channelType'] != "4" or  song['channel']['channelName'] in  ["KBS 사랑의소리", "MBC FM4U"]:
                continue
            print("#######################################")
            print(song['lastUpdate'])
            #print(song['channel']['channelId'] +" :(  ,\" " +song['channel']['channelName'] + "\")")

            print(ch[int(song['channel']['channelId'])][0])
            #print(ch[int(song['channel']['channelId'])][1])

            # print song['channel']['channelType']
            #print(song['title'])
            #print(song['artistName'])
            playList.append(song)

        if len(sys.argv) >1  and sys.argv[1] :
            print(sys.argv[1])
            tea.test(ch[int(playList[int(sys.argv[1])]['channel']['channelId'])][0])
            break
        else:
            recent = playList[-1]

            #lcd.init()
            # New b-w image
            im = Image.new('1', (84,48))
            # New drawable on image
            draw = ImageDraw.Draw(im)

            lcd.cls()
            lcd.backlight(0)
            rTitle = str(ch[int(recent['channel']['channelId'])][1])
            rAddress = str(ch[int(recent['channel']['channelId'])][0])
            song = recent['title']
            title = recent['artistName']

            draw.text((0,-2), rTitle, fill=1, font=font)
            draw.text((0,10), rAddress, fill=1, font=font)
            draw.text((0,20), song, fill=1, font=font)
            draw.text((0,30), title, fill=1, font=font)

            # Copy it to the display
            lcd.show_image(im)
            # clean up
            del draw
            del im

            if isHolding :
                lcd.text("   Hold  ")
            else:
                tea.test(ch[int(recent['channel']['channelId'])][0])

GPIO.cleanup()