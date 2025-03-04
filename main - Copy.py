# UARTFish (PICO2)
from machine import UART, ADC, Pin, I2C
import time
from math import sqrt, atan2, pi, copysign, sin, cos, log
from os import urandom, statvfs, listdir, remove, ilistdir
import re
import onewire, ds18x20
# led Blink off
blinkonoff="dot"
iStopData=0

myUsart0 = UART(0, baudrate=1200, bits=8, tx=Pin(0), rx=Pin(1), timeout=15)
myUsart1 = UART(1, baudrate=1200, bits=8, tx=Pin(4), rx=Pin(5), timeout=15)
# set real time clock
rtc=machine.RTC()
# internal temperatute
sensor_temp = ADC(4)
conversion_factor = 3.3/(65535)
press=ADC(26)    # pressure guage cell
photo=ADC(27) # photorestive sensdot chl
adc=ADC(28)   # salt or themistor chl
led = Pin(25, Pin.OUT)   # create LED object from Pin 25, Set Pin 15 to output
USBpower = Pin(24, Pin.IN)  # USB Power connect object
battLevel = ADC(3) # Really? https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf section 4.4 Powerchain
SensorPin = Pin(20, Pin.IN)
sensor = ds18x20.DS18X20(onewire.OneWire(SensorPin))
roms = sensor.scan()
print(roms)
# t0 = time.ticks_us()
a0IT = 824.6732767
a1IT = -0.05276744553
        
timestamp=rtc.datetime()
if timestamp[0] == 2021:
    foh = urandom(8)
    fohlist=list(bytes(foh, 'ascii'))
    fohstrlist=[str(ii) for ii in fohlist]
    fohstr=''.join(fohstrlist)
    timestringfilename = "Fish" + fohstr + ".csv"
else:
    timestringfilename="Fish%04d%02d%02d%02d%02d%02d.csv"%(timestamp[0:3] + timestamp[4:7])

#Create file
files_items= statvfs("/")
file = open(timestringfilename, "w")
file.write("Time,Thermister,Voltage,ThrCnt,Internal Temp degF,,IT_Cnt,Tmp IC degF,PhotoR,PhtCnt,Press,PRcnt,Battery,BtCNt,MemAvailable\n")
file.close()
# led Blink flashes
blinkonoff="dot"
debug="off"

if USBpower() == 1:
    print("files_items",files_items)
    print("Time,Thermister,Voltage,ThrCnt,Internal Temp degF,IT_Cnt,Tmp IC degF,PhotoR,PhtCnt,Press,PRcnt,Battery,BtCNt,MemAvailable") 

def convert2blinks(tmp):
    sTmp =str(tmp)
    i = 0
    while sTmp[i] != ".":   # extract number until '.'
        blinkNumber(sTmp[i])
        i = i + 1
    
    blinkDot() # Sleep 0.5s
    blinkNumber(sTmp[i + 1]) # number after dot

def blinkNumber(sTmp):
    tmp = int(sTmp)
    # morse code numbers: https://morsedecoder.com/
    # Numbers
    # 0	-----	1	.----	2	..---	3	...--	4	....-
    # 5	.....   6	-....	7	--...	8	---..	9	----.
    if tmp <5:
        morse = 0.01  # dot
        imorse = 0.3 # dash
    else:
        morse = 0.3  # dash
        imorse = 0.01 # dot
        
    for x in range(5):
        if x == tmp % 5:
            morse = imorse
        led.value(1)    # Set led turn on
        time.sleep(morse) # Sleep morse s
        led.value(0)    # Set led turn off
        spause = 0.5-morse
        time.sleep(spause) # Sleep 0.4s
        
    time.sleep(0.4) # Sleep 0.6s + 0.4 s    
    
def blinkDot():
    led.value(1) 
    time.sleep(0.4) # Sleep 0.4 s with led on    
    led.value(0)
    time.sleep(0.4) # Sleep 0.4 s with led off    

def LowBattBlink():
    for i in range(5):
        led.value(1) 
        time.sleep(0.2) # Sleep 0.2 s with led on    
        led.value(0)
        time.sleep(0.2) # Sleep 0.2 s with led off
    time.sleep(0.5)

try:
    while True:
        # have this pico receive commands
        # CMDS: time, header,blink, listfiles, printfile, allfileinfo
            
        if myUsart1.any() > 1:  # oringally 0 , but restart makes this 1?
            rxData = bytes()
            rxData = myUsart1.read()
            print(rxData)
            time.sleep(0.05)
            cmdstring = "{}".format(rxData.decode('utf-8'))
            myUsart0.write("CMD:" + cmdstring +"\n") # "{}".format(rxData.decode('utf-8')))
            regex = re.compile(",")
            cmd = regex.split(cmdstring)
            if str.lower(cmd[0]) == 'time' or str.lower(cmd[0]) == '00time':
# set time command:
#     "time,YYYY-mm-dd dow HH:MM:SS"
# spaces are important, dow is a number for the day of the week (where Monday is 1 and Sunday is 7)
# datetime.timetuple() - https://docs.python.org/3/library/datetime.html?highlight=weekday#module-datetime
                print ("cmd:", cmd)
                regex = re.compile(" ")
                mytime0 = regex.split(cmd[1])
                print("time to be set", mytime0)
                regex = re.compile("-")
                mytime1 = regex.split(mytime0[0])
                print("Date Tuple:", mytime1)
                regex = re.compile(":")
                mytime2 = regex.split(mytime0[2])
                print("Time Tuple:", mytime2)
                finaltimestr = mytime1 + [mytime0[1]] + mytime2 + [0]
                # print(finaltimestr)
                finaltime=[int(ii) for ii in finaltimestr]
                timestamp=rtc.datetime()
                print("My tuple:", finaltime, "PICO Now tuple:", timestamp)
                rtc.datetime(finaltime)
                timestamp=rtc.datetime()
                
# Create new file with now time
                timestringfilename="Fish%04d%02d%02d%02d%02d%02d.csv"%(timestamp[0:3] + timestamp[4:7])
                file = open(timestringfilename, "w")
                file.write("Time,Thermister,Voltage,ThrCnt,Internal Temp degF,,IT_Cnt,Tmp IC degF,PhotoR,PhtCnt,Press,PRcnt,Battery,BtCNt,MemAvailable\n")
                file.close()

            elif str.lower(cmd[0]) == 'header':
                myUsart0.write("Header in 10 seconds\n")
                time.sleep(10)
                myUsart0.write("Time,Thermister,Voltage,ThrCnt,Internal Temp degF,IT_Cnt,Tmp IC degF,PhotoR,PhtCnt,Press,PRcnt,Battery,BtCNt,MemAvailable")
                time.sleep(2)
            elif str.lower(cmd[0]) == 'blink':
# Turn blink function on or off
#      "blink,on"
#            to turn the LED blink function on
# or
#      "blink, off"
#            to turn the LED blink function off
                blinkonoff = cmd[1]
            elif str.lower(cmd[0]) == 'debug':
# Send debug messages to myUsat0: on or off
#      "debug,on"
#            to send myUsart0 messages
# or
#      "debug,off"
#            to stop messages
# or
#      "debug,dot"
#            for just dots
                debug = cmd[1]
            elif str.lower(cmd[0]) == 'listfiles':
# listfiles command will simply send a list the files on the RP to the remote system
                myUsart0.write("listfiles")
                time.sleep(5)
                listfiles=listdir()
                print("listfiles",listfiles)
                for filename in listfiles:
                    myUsart0.write(filename+"\n")
                myUsart0.write("\n")
                time.sleep(2)
                iStopData=3  # if iStopData = 1 then don't send new data to the  remote computer.  iStopData=3 will delay the data stop a couple cycles 
            elif str.lower(cmd[0]) == 'allfileinfo':
# allfileinfo command will send a list the files and file size on the RP to the remote system
                myUsart0.write("all file info")
                time.sleep(5)
                ilistfiles=ilistdir()
                for ilist in ilistfiles:
                    print(ilist,end="\n")
                    # print("\n")
                ilistfiles=ilistdir()
                i=0
                for ilist in ilistfiles:
                    i=i+1
                    # print("write Files:",i)
                    il=ilist[0]+" "+str(ilist[3])+"\n"
                    myUsart0.write(il) #,end=" ")
                    myUsart0.write("\n")
                myUsart0.write("\n")
                time.sleep(2)
                iStopData=3  # if iStopData = 1 then don't send new data to the  remote computer.  iStopData=3 will delay the data stop a couple cycles 
            elif str.lower(cmd[0]) == 'printfile':
# printfile command will print a file to the remote system.  Does not work well, yet.  The "printed" file is imcomplete. A later downlod is better. 
                time.sleep(2)
                downloadfile=cmd[1]
                iLine=0
                with open(downloadfile,'r') as input:
                    for line1 in input:
                        myUsart0.write(line1)
                        iLine=iLine+1
                        if iLine<3:
                            print("FileDump:",line1) # Only print to the screen the first line as a check.  Make is faster, less dropouts? 
                time.sleep(2)
                myUsart0.write("EOF")
                print("Filedump Complete")
                iStopData=1  # if iStopData = 1 then don't send new data to the  remote computer. 
            elif str.lower(cmd[0]) == 'remove':
# remove a seleted file from the this RP. 
                print("remove:", cmd[1])
                remove(cmd[1])
                iStopData=1    # if iStopData = 1 then don't send new data to the remote computer. 
            elif str.lower(cmd[0]) == 'restart':
                iStopData=0    # if iStopData = 0 then send new data to the remote computer. 
            else:
                print("Not known command")
            # myUsart0.write(cmdstring) # "{}".format(rxData.decode('utf-8')))

        if debug =='on':
            myUsart0.write("Start loop-> ")
        timestamp=rtc.datetime()
        timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
        reading = sensor_temp.read_u16() 
        tmpC=-0.02851521656*reading+434.371975 # 3/9/23 - From "Pico2 Calibration" google sheet  https://docs.google.com/spreadsheets/d/1RGrltegvYBxDpVtWtxXBlZisxOnsMp_n2vlwaf9G-EU/edit#gid=1589681626
        # Orignal conversion: 27 - (reading * conversion_factor - 0.706)/0.001721 # from: https://electrocredible.com/raspberry-pi-pico-temperature-sensor-tutorial/
        tmpF = (tmpC * 9 / 5) + 32
                
        adcValue = adc.read_u16() # Thermister
        if adcValue == 65535:
            voltage = 65534 * conversion_factor # / 65535.0 * 3.3
        elif adcValue == 0:
            voltage = conversion_factor # 1 / 65535.0 * 3.3
        else:
            voltage = adcValue * conversion_factor# / 65535.0 * 3.3
        Rt = 10.0 * voltage / (3.3-voltage)
        
        # DS18X20 https://cdn.sparkfun.com/datasheets/Sensors/Temp/DS18B20.pdf
        sensor.convert_temp() #  conversion routine: https://www.tomshardware.com/how-to/monitor-temperature-raspberry-pi-pico also see my TmpIC.py
        for rom in roms:
            temperatureC = sensor.read_temp(rom)
        temperatureF=(temperatureC)*9/5 + 32

        pressValue = press.read_u16()
        Pressure = pressValue*conversion_factor #/ 65535.0 * 3.3
        
        photoValue = photo.read_u16()
        photoVolt = photoValue * conversion_factor #/ 65535.0 * 3.3
        
        battL = battLevel.read_u16()
        batt = battL / 65535.0 * 29 #  * 0.0003879864694 + 1.028239557  
        if batt<3.3:
            LowBattBlink()
        
        tempK = (1 / (1 / (273.15+25) + (log(Rt/10)) / 3950))
        tempF = (tempK - 273.15)*9/5 + 32
        tempFCorr= tempF*1.220873666-17.52571118  # 3/9/23 - From "Pico2 Calibration" google sheet  https://docs.google.com/spreadsheets/d/1RGrltegvYBxDpVtWtxXBlZisxOnsMp_n2vlwaf9G-EU/edit#gid=1589681626
        files_item = statvfs("/")
        # filesize=mem_free()
        filesize=files_item[3]

        tempRpt = str(tempF)+","+str(voltage)+","+str(adcValue)+","+str(tmpF)+","+str(reading)+","+str(temperatureF)+","+str(photoVolt)+","+str(photoValue)+","+str(Pressure)+","+str(pressValue)+","+str(batt)+","+str(battL)+","+str(filesize)
        # tempRpt = str(tempF) + ", " + str(adcValue) + ", " + str(tmpF)  + ", " + str(reading)  + ", " + str(batt) + ", " + str(battL) 
        # print(tempRpt)
        if iStopData==0:
            myUsart0.write(timestring + "," + tempRpt) # + "\n")
        elif iStopData>1:
            myUsart0.write(timestring + "," + tempRpt) # + "\n")
            iStopData=iStopData-1
            
        file = open(timestringfilename, "a")
        # file.write(timestring + "," + tempRpt + "\n")
        file.write(timestring + "," + tempRpt + "\n")
        file.close()
        
        if USBpower() == 1:
             print("iStop:",iStopData, timestring, ",", tempRpt)
        #t0 = time.ticks_us()
        if blinkonoff == 'ON' or blinkonoff == 'on':
            convert2blinks(tempF)
        elif blinkonoff == 'DOT' or blinkonoff == 'dot':
            blinkDot()
        time.sleep(1)
        
except KeyboardInterrupt:
    print("Keyboard")
    pass # machine.soft_reset() 