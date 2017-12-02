# Copyright (c) 2017 roseengineering

import os
import dbus
from gi.repository import GObject

# bluezero

from bluezero import dbus_tools
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
    pi_cpu_monitor = ble()
    dbus_tools.start_mainloop()


