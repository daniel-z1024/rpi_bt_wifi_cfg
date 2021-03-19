import os
import struct
import json
import bluetooth

os.system("bluetoothctl power on")
os.system("bluetoothctl discoverable on")

port = 1

target_name = "raspberrypi4b"
target_address = None
 
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

sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((target_address, port))

print('Send request message')
sock.send('Get')

data = sock.recv(1024)
data_size = int(data.decode('utf-8'))
print(f'Receive data size {data_size}')

total_data = ''
recv_size = 0

try:
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
    #json_data = json.dumps(json_data, indent=4, separators=(',', ': '))

    print('Received JSON data:')
    print(json_data)
    
    sock.close()
except (BlockingIOError, ConnectionResetError):
    sock.close()

