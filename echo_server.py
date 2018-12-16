#!/usr/bin/python3
# Copyright (c) 2017,2018 roseengineering

# 12/16/2018:
# remember to
# 1) add --experimental to ExecStart in /lib/systemd/system/bluetooth.service 
# 2) copy the following xml file into /etc/dbus-1/system.d/
# 3) apt-get install libdbus-1-dev libdbus-glib-1-dev python3-gi
# 4) pip3 install dbus-python bluezero

"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE busconfig PUBLIC 
 "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <policy context="default">
    <allow own="ukBaz.bluezero"/>
    <allow send_destination="ukBaz.bluezero"
           send_interface="org.freedesktop.DBus.Introspectable"/>
    <allow send_type="method_call" log="true"/>
  </policy>
</busconfig>
"""

import os
import dbus

# bluezero

from bluezero import constants
from bluezero import adapter
from bluezero import advertisement
from bluezero import localGATT
from bluezero import GATT

# constants

UART_SRVC =    '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
UART_TX_CHRC = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'  # write
UART_RX_CHRC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'  # read, notify


def encode(value):
    return dbus.Array([ dbus.Byte(n) for n in value.encode() ])

class UartRxChrc(localGATT.Characteristic):
    def __init__(self, service):
        self.value = ''
        localGATT.Characteristic.__init__(
            self,
            1,
            UART_RX_CHRC,
            service,
            '',
            False,
            ['read', 'notify'])

    def update(self, value):
        if self.props[constants.GATT_CHRC_IFACE]['Notifying']:
            print('notifying [%s]' % value)
            self.PropertiesChanged(constants.GATT_CHRC_IFACE, 
                { 'Value': encode(value) }, [])
            self.value = ''
        else:
            self.value = value

    def ReadValue(self, options):
        print('read [%s]' % self.value)
        value = self.value
        self.value = ''
        return encode(value)

    def StartNotify(self):
        self.props[constants.GATT_CHRC_IFACE]['Notifying'] = True

    def StopNotify(self):
        self.props[constants.GATT_CHRC_IFACE]['Notifying'] = False


class UartTxChrc(localGATT.Characteristic):
    def __init__(self, service, chrc):
        self.chrc = chrc
        localGATT.Characteristic.__init__(
            self,
            2,
            UART_TX_CHRC,
            service,
            '',
            False,
            ['write'])


    def WriteValue(self, value, options):
        value = ''.join([ str(n) for n in value ])
        print('writevalue [%s]' % value)
        self.chrc.update(value)



class ble:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.app = localGATT.Application()
        self.srv = localGATT.Service(1, UART_SRVC, True)

        self.receive = UartRxChrc(self.srv)
        self.transmit = UartTxChrc(self.srv, self.receive)

        self.app.add_managed_object(self.srv)
        self.app.add_managed_object(self.receive)
        self.app.add_managed_object(self.transmit)

        self.srv_mng = GATT.GattManager(adapter.list_adapters()[0])
        self.srv_mng.register_application(self.app, {})

        self.dongle = adapter.Adapter(adapter.list_adapters()[0])
        advert = advertisement.Advertisement(1, 'peripheral')

        advert.service_UUIDs = [UART_SRVC]
        if not self.dongle.powered:
            self.dongle.powered = True
        ad_manager = advertisement.AdvertisingManager(self.dongle.address)
        ad_manager.register_advertisement(advert, {})


if __name__ == '__main__':
    echo_server = ble()
    echo_server.app.start()


