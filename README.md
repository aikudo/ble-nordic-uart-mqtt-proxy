
ble-uart-mqtt-server
====================

This repo contains two servers for a BLE peripheral: the first is a BLE UART 
echo server and the second is a BLE MQTT PROXY server.  

The repo also
contains a BLE client called ping.py which can communicate
with both peripheral servers.  All programs have been tested on 
a Raspberry Pi.  All three are written in Python.

echo server
-----------

The echo server simply exposes a BLE UART service and echoes 
any data sent to it.  The server must be run as root.  
Writing to the service using a BLE client, like Adafruit 
or Nordic's BLE UART App, will result in the BLE UART data 
being sent back to the client.

To run the echo service executing the following is enough:

```
     $ sudo python3 echo_server.py
```

The client, ping.py, can be used to test the echo server.
Run it as root and it will send the same message over and over to the
BLE peripheral with the mac address given on the command line.  All BLE UART responses will be printed back.  
For example to ping the echo service on B8:27:EB:08:5E:F3 run:

```
     $ sudo python3 ping.py B8:27:EB:08:5E:F3
```

remote server
-----------------

The remote.py server takes a list of commands, each a line in a file, and
remotely executes them on the BLE server.  The server uses the control
pad feature of the Adafruit LE Connect App to run the commands.

The up arrow runs the current command. The down arrow kills the process
if running.  The left and right rotates through the command list to
set the current command.  For example:

```
     $ sudo python3 remote.py remote.txt
```



MQTT proxy server
-----------------

Basically the MQTT Proxy service is my attempt at creating a MQTT Proxy
profile for BLE.  I was inspired by the HTTP Proxy profile 
that is already a BLE standard.  My MQTT Proxy service, rather than 
ferrying HTTP requests over to some HTTP server using a BLE 
peripheral service as a proxy, instead ferries MQTT subscribe and publish 
requests from a peripheral over to a MQTT service for a BLE client, as well as
ferry messages back.

Why might this be useful?  Using a MQTT proxy, your BLE client, say 
a temperature sensor, can now publish its readings using low power 
BLE instead of having to connect using WiFi or ethernet or some other way,
like proxying readings via I2C to another computer who can.

My use case for the service is for controlling a standalone SDR radio in the field.  If the
SDR radio is programmed to respond to MQTT messages, a BLE client
like a phone could be used to remotely tell it to record or to change 
its frequency or gain.  In addition if the SDR radio sent MQTT messages, 
a BLE proxy server could be used to send the messages to the BLE client
for monitoring.

The MQTT Proxy uses the same descriptor ids that the Nordic
UART service uses.  Of course you can use your own uuids if you want.

To publish a message using the proxy, write a stream value to
the peripheral using the following format, where topic and message
are separated by a space:

     <topic> <message>

MQTT messages subscribed to will be received by the BLE client 
in the same space separated format.

To subscribe to a topic, send the following with no space after
the topic.  You will be unsubscribed from any prior subscription.
Initially your BLE peripheral will be subscribed to every topic, ie '#'.

     <topic>
    
To start the MQTT Proxy service run for example:

     sudo python3 mqttproxy_server.py 192.168.0.9 1883

Here, 192.168.0.9 is the ip address of the MQTT service and
1883 is its port.

To test, run the ping.py client against it.  Ping will publish the
message "mqtt message" to topic "/topic"

     sudo python3 ping.py B8:27:EB:08:5E:F3

Listen to the MQTT queue to ensure the messages are proxied.

     mosquitto_sub -h 192.168.0.9 -p 1883 -v -t '#'


Dependencies
------------

Install the following to run a BLE peripheral server.

     sudo apt-get upgrade -y   # to get new bluetooth mac address on pi
     sudo apt-get install python3-dev
     sudo apt-get install libdbus-1-dev
     sudo apt-get install libdbus-glib-1-dev
     sudo apt-get install python3-gi
     sudo pip3 install dbus-python
     sudo pip3 install bluezero
     sudo pip3 install paho-mqtt

     sudo cp ukBaz.bluezero.conf /etc/dbus-1/system.d/
     # copied from https://github.com/ukBaz/python-bluezero
     sudo vi /lib/systemd/system/bluetooth.service
     # append --experimental to line with ExecStart
     sudo reboot

Install the following to run a BLE client, namely ping.py.

     sudo apt-get install libglib2.0-dev
     sudo pip3 install bluepy

To create a MQTT queue, you can install mosquitto.
Append the line "listener 1883" to 
/etc/mosquitto/mosquitto.conf to make the queue public.

- Copyright (c) 2017,2018 roseengineering
