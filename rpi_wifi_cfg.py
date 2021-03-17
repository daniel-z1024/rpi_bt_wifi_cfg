#!/usr/bin/python3
# -*- coding:utf-8 -*-

import time
import os
import json
import subprocess
import codecs
import bluetooth
from wifi import Cell, Scheme


wifi_interface_name = 'wlan0'

def get_wifi_info(interface):    
    # Get all detected Wi-Fi cells
    cells = Cell.all(interface)

    index = 1
    js = {'Cells':[], 'Current':{} }

    # Get info of each cell
    for cell in cells:
        #print(f'{cell.ssid}, {type(cell.ssid)}')
        if len(cell.ssid) != 0 and cell.ssid.find('\\x') < 0:
            js['Cells'].append(
                {
                    'id':index,
                    'ssid':cell.ssid.encode('raw_unicode_escape').decode('utf-8'),
                    'mac':cell.address,
                    'signal':cell.signal,
                    'frequency':cell.frequency,
                    'encrypted':cell.encrypted,
                    'quality':cell.quality
                }
            )
            index += 1

    # Get current Wi-Fi cell info if connected
    p = subprocess.Popen(['wpa_cli', '-i', interface, 'status'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    p.wait()
    result=out.decode().strip().split('\n')
    for l in result:
        if l.startswith('ssid='):
            js['Current']['ssid']=l.split('=')[1]
        elif l.startswith('freq='):
            js['Current']['freq']=l.split('=')[1]
        elif l.startswith('bssid='):
            js['Current']['mac']=l.split("=")[1].upper()
        elif l.startswith('ip_address='):
            js['Current']['ip']=l.split('=')[1]

    # Convert all cell info to JSON data
    js_data = json.dumps(js, indent=4, separators=(',', ': '))

    return js_data


try:
    os.system("bluetoothctl power on")
    os.system("bluetoothctl discoverable on")
    while True:
        js = get_wifi_info(wifi_interface_name)
        print(js)

        server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        server_sock.bind(("", bluetooth.PORT_ANY))
        server_sock.listen(1)

        port = server_sock.getsockname()[1]

        uuid = "815425a5-bfac-47bf-9321-c5ff980b5e11"

        bluetooth.advertise_service(server_sock,
				                    "RPI Wi-Fi Config",
                                    service_id = uuid,
                                    service_classes = [uuid, bluetooth.SERIAL_PORT_CLASS],
                                    profiles = [bluetooth.SERIAL_PORT_PROFILE])

        print(f'Waiting for connection on RFCOMM channel {port}')

        client_sock, client_info = server_sock.accept()
        print(f'Accepted connection from {client_info}')

        client_sock.close()
        server_sock.close()

        time.sleep(10)

except KeyboardInterrupt as e:
    print(e)
    print('\nExiting\n')
