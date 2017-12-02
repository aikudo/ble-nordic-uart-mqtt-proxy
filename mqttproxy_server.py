# Copyright (c) 2017 roseengineering

import os, sys

# bluezero

import dbus
from gi.repository import GObject
from bluezero import dbus_tools
from bluezero import constants
from bluezero import adapter
from bluezero import advertisement
from bluezero import localGATT
from bluezero import GATT

# mqtt

import paho.mqtt.client as mqtt

# characteristics

MQTT_SRVC =    '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
MQTT_RX_CHRC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
MQTT_TX_CHRC = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'


class Receive(localGATT.Characteristic):
    def __init__(self, service, chrc_id, client, newline):
        self.newline = newline
        client.on_message = self.on_message
        localGATT.Characteristic.__init__(
            self,
            1,
            chrc_id,
            service,
            '',
            False,
            ['read', 'notify'])

    def on_message(self, client, userdata, msg):
        print('on_message: [%s]: [%s]' % (msg.topic, msg.payload))
        if self.props[constants.GATT_CHRC_IFACE]['Notifying']:
            value = '%s %s' % (msg.topic, msg.payload.decode())
            if self.newline: 
                value = value.rstrip() + '\n'
            print('notify: [%s]' % value)
            value = dbus.ByteArray([ dbus.Byte(n) for n in value.encode() ])
            d = { 'Value': value }
            self.PropertiesChanged(constants.GATT_CHRC_IFACE, d, [])

    def ReadValue(self, options):
        return dbus.ByteArray([])

    def StartNotify(self):
        print('start notify')
        self.props[constants.GATT_CHRC_IFACE]['Notifying'] = True

    def StopNotify(self):
        print('stop notify')
        self.props[constants.GATT_CHRC_IFACE]['Notifying'] = False


class Transmit(localGATT.Characteristic):
    def __init__(self, service, chrc_id, client):
        self.client = client
        localGATT.Characteristic.__init__(
            self,
            2,
            chrc_id,
            service,
            '',
            False,
            ['write'])

    def WriteValue(self, value, options):
        client = self.client
        value = dbus.ByteArray(value).decode()
        print('writevalue: [%s]' % value)
        topic, sep, payload = value.partition(' ')        
        if sep == ' ':
            client.publish(topic, payload)
        else:
            print('subscribing to', topic)
            client.unsubscribe('#')
            client.subscribe(topic)


# functions

def create_mqtt_proxy(client, newline):

    bus = dbus.SystemBus()
    app = localGATT.Application()
    srv = localGATT.Service(1, MQTT_SRVC, True)

    receive = Receive(srv, MQTT_RX_CHRC, client, newline)
    transmit = Transmit(srv, MQTT_TX_CHRC, client)

    app.add_managed_object(srv)
    app.add_managed_object(receive)
    app.add_managed_object(transmit)

    srv_mng = GATT.GattManager(adapter.list_adapters()[0])
    srv_mng.register_application(app, {})

    dongle = adapter.Adapter(adapter.list_adapters()[0])
    if not dongle.powered:     # bring hci0 up if down
        dongle.powered = True

    advert = advertisement.Advertisement(1, 'peripheral')
    advert.service_UUIDs = [MQTT_SRVC]

    ad_manager = advertisement.AdvertisingManager(dongle.address)
    ad_manager.register_advertisement(advert, {})


def on_connect(client, userdata, flags, rc):
    print("Connected to mqtt with result code %d" % rc)
    if rc == 0: client.subscribe('#')


def create_client(hostname, port, newline):
    client = mqtt.Client()
    create_mqtt_proxy(client, newline)
    client.loop_start()
    client.on_connect = on_connect
    client.connect(hostname, port)
    return client


def main(arg):
    newline = False
    global MQTT_SRVC, MQTT_RX_CHRC, MQTT_TX_CHRC

    while arg:
        if arg[0] == '-n':
            newline = True
            arg = arg[1:]
        else:
            break

    hostname = arg[0] if len(arg) > 0 else '127.0.0.1'
    port = int(arg[1]) if len(arg) > 1 else 1883

    client = create_client(hostname, port, newline)

    try:
        dbus_tools.start_mainloop()
    except:
        print('stopping...')
        client.loop_stop()


if __name__ == '__main__':
    main(sys.argv[1:])

