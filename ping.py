# Copyright (c) 2017 roseengineering

import sys
from bluepy import btle

# mqtt proxy characteristic

srvc_uuid = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
read_uuid = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'  # read, notify
send_uuid = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'  # write

class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        print('data [%s]' % data)

address = sys.argv[1]
p = btle.Peripheral()
p.connect(address)
p.setMTU(512)

svc = p.getServiceByUUID(srvc_uuid)   # 2800
ch = svc.getCharacteristics(read_uuid)[0]  # 2803
cout = svc.getCharacteristics(send_uuid)[0]  # 2803
p.setDelegate(MyDelegate())

setup_data = b"\x01\x00"
handle = ch.getHandle() + 1
p.writeCharacteristic(handle, setup_data, withResponse=True)

while True:
    if p.waitForNotifications(1):
        continue
    cout.write('/topic mqtt message'.encode())

