#!/usr/bin/python3
# -*- coding:utf-8 -*-

import time
import json
import subprocess
import bluetooth
from wifi import Cell


wifi_interface_name = 'wlan0'


def bluetooth_enable():
    subprocess.call(['bluetoothctl', 'power', 'on'])
    subprocess.call(['bluetoothctl', 'discoverable', 'on'])


def get_wifi_info(interface):    
    # Get all detected Wi-Fi cells
    cells = Cell.all(interface)

    index = 1
    js = {'Cells':[], 'Current':{} }

    # Get info of each cell
    for cell in cells:
        if cell.ssid != '' and cell.ssid.find('\\x') < 0:
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
    
    # Print Wi-Fi info list
    print('Detected Wi-Fi:')
    for l in js['Cells']:
        print(l)

    print('Connected Wi-Fi:')
    print(js['Current'])

    # Convert all cell info to JSON data
    #js_data = json.dumps(js, indent=4, separators=(',', ': '))
    js_data = json.dumps(js)

    return js_data


def bluetooth_start_server():
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.bind(("", bluetooth.PORT_ANY))
    sock.listen(1)

    port = sock.getsockname()[1]

    uuid = "815425a5-bfac-47bf-9321-c5ff980b5e11"

    bluetooth.advertise_service(sock,
                                "RPI Wi-Fi Config",
                                service_id = uuid,
                                service_classes = [uuid, bluetooth.SERIAL_PORT_CLASS],
                                profiles = [bluetooth.SERIAL_PORT_PROFILE])

    print(f'Waiting for connection on RFCOMM channel {port}')

    return sock


def send_json_data(sock, js):
    # Convert JSON data to byte stream
    data = bytes(js, encoding='utf-8')

    # Send byte stream length to client
    size = len(data)
    print(f'Send byte stream length {size}')
    sock.send(str(size).encode('utf-8'))
    
    # Send byte stream content to client
    print(f'Send byte stream content')
    sock.send(data)


def send_wifi_info(sock):
    # Get current Wi-Fi info
    js = get_wifi_info(wifi_interface_name)
    send_json_data(sock, js)


def main_task():
    try:
        while True:
            # Enable bluetooth function
            bluetooth_enable()

            # Start bluetooth RFCOMM server
            server_sock = bluetooth_start_server()

            # Wait for client connection
            print('Waiting for client connection')
            client_sock = 0
            client_sock, client_info = server_sock.accept()
            print(f'Accepted connection from {client_info}')

            while True:
                # Waiting for command from client
                print('Waiting for command from client')
                try:
                    data = client_sock.recv(1024)
                except bluetooth.btcommon.BluetoothError:
                    # Client connection closed
                    print('Connection closed by client')
                    client_sock.close()
                    server_sock.close()
                    break

                # Parse received command
                data = data.decode('utf-8')
                print(f'RECV Command: {data}')

                data = data.lower()
                if data == 'get':
                    send_wifi_info(client_sock)

            # Interval time before starting next server listening
            print('Time delay...')
            time.sleep(10)

    except KeyboardInterrupt as e:
        if client_sock != 0:
            client_sock.close()
        server_sock.close()
        print(e)
        print('Exiting\n')


def main():
    # Scan Wi-Fi one time when startup
    get_wifi_info(wifi_interface_name)

    # Run main task
    main_task()


if __name__ == "__main__":
    main()
