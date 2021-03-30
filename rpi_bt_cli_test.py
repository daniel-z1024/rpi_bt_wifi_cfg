import json
import subprocess
import bluetooth


def bluetooth_enable():
    subprocess.call(['bluetoothctl', 'power', 'on'])
    subprocess.call(['bluetoothctl', 'discoverable', 'on'])


def bluetooth_find_device():
    target_name = "raspberrypi4b"
    target_address = None

    print('Detect bluetooth devices nearby...')
 
    nearby_devices = bluetooth.discover_devices(lookup_names = True)

    print("Found %d devices" % len(nearby_devices))

    for addr,name in nearby_devices:
        print("  %s - %s" % (addr, name))
        if target_name == bluetooth.lookup_name(addr):
            target_address = addr
 
    if target_address is None:
        print("Could not find target bluetooth device nearby")
        exit(0)

    print("Found target bluetooth device with address ", target_address)

    return target_address


def bluetooth_cli_connect(addr, port):
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((addr, port))
    
    return sock


def bluetooth_cli_send(sock, data):
    print(f'TxMsg: {data}')
    sock.send(data)


def bluetooth_cli_recv(sock):
    total_data = ''
    recv_size = 0
    try:
        # First get the data size that will be sent by server
        data = sock.recv(1024)
        data_size = int(data.decode('utf-8'))
        print(f'RxDataSize: {data_size}')

        while recv_size < data_size:
            if data_size - recv_size > 1024:
                size = 1024
            else:
                size = data_size - recv_size
            data = sock.recv(size)
            data_len = len(data)
            recv_size += data_len
            print(f'{recv_size}/{data_size} data received')
            total_data += data.decode("utf-8")

        json_data = json.loads(total_data)

        return json_data
    except bluetooth.btcommon.BluetoothError:
        print('Connection closed by server, exit!')
        sock.close()
        exit(0)


def bluetooth_cli_get_wifi_list(sock):
    bluetooth_cli_send(sock, '{"Command":"GetWiFiScanList"}')

    json_data = bluetooth_cli_recv(sock)
    print('Rx Wi-Fi scan list:')
    print(json_data)


def bluetooth_cli_get_wifi_connect_status(sock):
    bluetooth_cli_send(sock, '{"Command":"GetWiFiConnectionStatus"}')

    json_data = bluetooth_cli_recv(sock)
    print('Rx current Wi-Fi connection status:')
    print(json_data)


def main():
    bluetooth_enable()

    target_addr = bluetooth_find_device()

    sock = bluetooth_cli_connect(target_addr, 1)

    bluetooth_cli_get_wifi_list(sock)

    bluetooth_cli_get_wifi_connect_status(sock)

    print('Close socket and exit...')
    sock.close()


if __name__ == "__main__":
    main()
