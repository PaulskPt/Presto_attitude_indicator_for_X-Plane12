# ICON [[(-4.5, 16.82), (-9.92, 6.75), (-19.99, 1.33), (-16.1, -2.5), (-8.17, -1.13), (-2.58, -6.71), (-19.93, -14.1), (-15.33, -18.8), (5.73, -15.08), (12.52, -21.87), (13.6, -22.66), (15.25, -23.11), (16.46, -23.05), (17.73, -22.63), (19.14, -21.42), (19.62, -20.63), (19.97, -19.45), (19.99, -18.25), (19.79, -17.33), (19.32, -16.37), (18.79, -15.72), (11.92, -8.84), (15.64, 12.17), (10.99, 16.82), (3.54, -0.53), (-2.04, 5.05), (-0.61, 12.93), (-4.5, 16.82)]]
# NAME Attitude Indicator
# DESC A Demo for the Multi-Sensor Stick
from presto import Presto
from picovector import ANTIALIAS_FAST, PicoVector, Polygon, Transform
import machine
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ
import time

# Script modified version for use with X-Plane12 by Paulus Schulinck (Github handle: @PaulskPt)

my_debug = False
use_xp12 = True
use_joystick_data = False

# Setup for the Presto display
presto = Presto(ambient_light=False)
display = presto.display
WIDTH, HEIGHT = display.get_bounds()
CX = WIDTH // 2
CY = HEIGHT // 2
x, y = 0, CY
x_prev = x
y_prev = y

# Colours
GRAY = display.create_pen(42, 52, 57)
BLACK = display.create_pen(0, 0, 0)
SKY_COLOUR = display.create_pen(86, 159, 201)
GROUND_COLOUR = display.create_pen(101, 81, 63)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(200, 0, 0)

# Pico Vector
vector = PicoVector(display)
vector.set_antialiasing(ANTIALIAS_FAST)
trf = Transform()
normal = Transform()
vector.set_transform(trf)

# Setup some of our vector shapes
background_rect = Polygon()
background_rect.rectangle(0, 0, WIDTH, HEIGHT)
background_rect.circle(CX, CY, 109)

instrument_outline = Polygon().circle(CX, CY, 110, stroke=8)

ground = Polygon().rectangle(0, HEIGHT // 2, WIDTH, HEIGHT)
horizon = Polygon().rectangle(0, HEIGHT // 2, WIDTH, 2)
pitch_lines = Polygon()

for line in range(1, 7):
    if line % 2:
        pitch_lines.rectangle(CX - 10, CY - line * 14, 20, 1.5)
        pitch_lines.rectangle(CX - 10, CY + line * 14, 20, 1.5)
    else:
        pitch_lines.rectangle(CX - 30, CY - line * 14, 60, 1.5)
        pitch_lines.rectangle(CX - 30, CY + line * 14, 60, 1.5)

craft_centre = Polygon().circle(CX, CY - 1, 2)
craft_left = Polygon().rectangle(CX - 70, CY - 1, 50, 2, (2, 2, 2, 2))
craft_right = Polygon().rectangle(CX + 20, CY - 1, 50, 2, (2, 2, 2, 2))
craft_arc = Polygon().arc(CX, CY, 22, -90, 90, stroke=2)
    
def show_message(text):
    display.set_pen(GRAY)
    display.clear()
    display.set_pen(WHITE)
    display.text(f"{text}", 5, 10, WIDTH, 2)
    presto.update()
    
# see: https:/github.com/pimoroni/presto/blob/main/docs/picovector.md
def disp_text(txt):
    hPos = 5
    vPos = 30
    display.set_pen(GRAY)
    display.clear()
    display.set_pen(RED)
    display.text(txt, hPos, vPos, WIDTH, 2)
    display.set_pen(WHITE)
    presto.update()


if use_xp12:
    import socket
    import struct
    UDP_PORT = 49707
    UDP_IP = ""
    ip = None
    connected = False
    sock = None
    secr = None
    try_cnt = 0
    try_cnt_max = 9
    
    connected = presto.wifi.isconnected()
    if not connected:
        show_message("Connecting WiFi")
        connected = presto.connect()
    else:
        print(f"Wifi already connected")
    
    ip = presto.wifi.ipv4()
    secr = presto.wifi._secrets()[0]
    
    if connected:
        t1 = "WiFi connected to\n{:s}".format(secr)
    else:
        t1 = "Afff...WiFi connection\nto {:s}\nfailed".format(secr)
    show_message(t1)
    
    # stats = presto.wifi._statuses
    if my_debug:
        print("Hurray! We have a WiFi connection!")
        # print(f"dir(presto.wifi) = {dir(presto.wifi)}")
        print(f"access point SSID = {secr}")
        print(f"presto.wifi.ipv4() = {ip}")
        """
            stats = {
             0: 'IDLE', \
             1: 'CONNECTING', \
            -3: 'WRONG PASSWORD', \
            -2: 'NO AP FOUND', \
            -1: 'CONNECT_FAIL', \
             3: 'GOT_IP'}
        """
        # print(f"stats = {stats}")
      
    if ip is not None:
        UDP_IP = str(ip)
        if my_debug:
            print(f"UDP_IP = {UDP_IP}")
        sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
        sock.bind((UDP_IP, UDP_PORT))
        if sock is None:
            print("Creating sock failed. Exiting...")
            raise RuntimeError
        else:
            if my_debug:
                print(f"We have a socket: {sock}.")

                
def DecodeDataMessage(message):
    TAG = "DecodeDataMessage(): "
    # Message consists of 4 byte type and 8 times a 4byte float value.
    # Write the results in a python dict. 
    values = {}
    typelen = 4
    type = int.from_bytes(message[0:typelen], 'little') # byteorder='little')
    if my_debug:
        print(TAG + f"type = {type}")
        
    if type != 8 and type != 17:
        values["type"] = type  # Create a default result with at least the key "type" in it.
        
    data = message[typelen:]
    dataFLOATS = None
    if use_joystick_data:
        if type == 8:
            if not my_debug:
                print(TAG + f"Type {type}")
            dataFLOATS = struct.unpack("<ffffffff",data)
            values["type"]=type
            values["elevation"]=dataFLOATS[0]
            values["aileron"]=dataFLOATS[1]
            values["rudder"]=dataFLOATS[2]
            values["not_used_1"]=dataFLOATS[3]
            values["not_used_2"]=dataFLOATS[4]
            values["not_used_3"]=dataFLOATS[5]
            values["not_used_4"]=dataFLOATS[6]
            values["not_used_5"]=dataFLOATS[7]
        else:
            if my_debug:
                print(TAG + f"Type {type}, not implemented: {dataFLOATS}")
    else:
        if type == 17:
            if my_debug:
                print(TAG + f"Type {type}")
            dataFLOATS = struct.unpack("<ffffffff",data)
            values["type"]=type
            values["pitch"]=dataFLOATS[0]
            values["roll"]=dataFLOATS[1]
            values["heading"]=dataFLOATS[2]
            values["not_used_1"]=dataFLOATS[3]
            values["not_used_2"]=dataFLOATS[4]
            values["not_used_3"]=dataFLOATS[5]
            values["not_used_4"]=dataFLOATS[6]
            values["not_used_5"]=dataFLOATS[7]
        else:
            if my_debug:
                print(TAG + f"Type {type}, not implemented: {dataFLOATS}")
    return values
 
def DecodePacket(data):
    TAG = "DecodePacket(): "
    # Packet consists of 5 byte header and multiple messages.
    if isinstance(data, bytes):
        if my_debug:
            print(TAG + f"param data is of type : {type(data)}. Going to convert to list type")
    valuesout = {}
    headerlen = 5
    header = data[0:headerlen]
    messages = data[headerlen:]
    if(header[:4]==b'DATA'):
        # Divide into 36 byte messages
        messagelen = 36
        for i in range(0,int((len(messages))/messagelen)):
            message = messages[(i*messagelen) : ((i+1)*messagelen)]
            if my_debug:
                print(TAG + f"message to decode = {message}")
            values = DecodeDataMessage(message)
            valuesout.update( values )
    else:
        if my_debug:
            print(TAG + "Packet type not implemented. ")
            print(TAG + "  Header: ", header)
            print(TAG + "  Data: ", messages)
    return valuesout



TAG = "main(): "
data = None
addr = None
ax = 0.0
ay = 0.0
az = 0.0

x_axis = 0.0
y_axis = 0.0
alpha = 0.15

# UDP msg type sensitivity factors
if use_xp12:
    msg_type = None
    type08_mult = 10000
    type17_mult = 100
    le_data = 0
    time_out_cnt = 0
    time_out_max_cnt = 3
    
while True:
    
    if use_xp12:
        if sock is None:
            if my_debug:
                print(TAG + f"type(sock) = {type(sock)}. Check WiFi. Cannot continue...")
            raise RuntimeError
        else:

            sock.setblocking(True)  # Switch on blocking.
            while True:
                try:
                    sock.settimeout(5)  # set timeout to 5 seconds
                    # Receive a packet
                    data, addr = sock.recvfrom(256) # buffer size is 512 bytes
                    if isinstance(data, bytes):
                        if my_debug:
                            print(TAG + f"data received = \"{data}\"")
                        le_data = len(data)
                        if le_data > 0:
                            if not my_debug:
                                # packet length usual: 77 to 221 bytes, depending howmany messages chosen
                                print(TAG + f"length data received: {le_data}") 
                            break
                except OSError as exc:
                    errnr = exc.args[0]
                    if errnr == 110: # ETIMEDOUT
                        time_out_cnt += 1
                        if time_out_cnt > time_out_max_cnt:
                            break  # receiving data failed. Exit
                        if not my_debug:
                            t1 = "socket timed out.\n\n\tIs X-Plane12 running?\n\n\tIs it setup for\nsending data?"
                            disp_text(t1)
                            print(TAG + f"{t1}")
                    elif errnr == 11: # EAGAIN
                        if not my_debug:
                            print(TAG + f"EAGAIN error occurred. Skipping.")
                        continue
                    else:
                        print(TAG + f"Error: {exc}")
            
            # Decode the packet. Result is a python dict (like a map in C) with values from X-Plane.
            # Example:                         magnetic           true
            #   'roll': 1.05, 'pitch': -4.38, 'heading': 275.43, 'heading2': 271.84}
            if data is None:
                ax = 0.0 # Make that the attitude indicator is set horizontal
                ay = 0.0
                x_axis = 370
                x_prev = 370
                y_axis = 370
                y_prev = 370
                if my_debug:
                    print(f"Noting received (yet): data = \"{data}\"")
            else:  
                if my_debug:
                    print(TAG + f"packet received from host with IP-addres: {addr[0]}, via port: {addr[1]}")
                values = DecodePacket(data)
                if "type" in values.keys():
                    msg_type = values["type"]
                    if my_debug:
                        print(f"message type received: {msg_type}")
                else:
                    msg_type = 99 # pseudo for unknown message type
                    
                if msg_type != 8 and msg_type != 17:
                    continue  # go around

                if use_joystick_data: 
                    if values["type"] == 8:  # = Joystick
                        ax = values["aileron"]   * type08_mult  # roll
                        ay = values["elevation"] * type08_mult  # pitch
                        az = int(values["rudder"])  # heading

                        if not my_debug:
                            t1 = "ax: {:9.5f}, ay: {:9.4f}, az: {:8.2f}".format(ax, ay, az)
                            print(TAG + f"data from X-Plane12: {t1}")
                            # print(TAG + f" values: {values}")
                    else:
                        if my_debug:
                            print(TAG + f"No data received of type: 8")
                else:
                    if values["type"] == 17: # = aircraft attitude
                        ax = values["roll"]    * type17_mult * 1.5  # roll
                        ay = values["pitch"]   * type17_mult  # # pitch
                        az = int(values["heading"]) # heading

                        if not my_debug:
                            t1 = "ax: {:9.5f}, ay: {:9.4f}, az: {:8.2f}".format(ax, ay, az)
                            print(TAG + f"data from X-Plane12: {t1}")
                            # print(TAG + f" values: {values}")
                    
                    else:
                        if my_debug:
                            print(TAG + f"No data received of type: 17")
                
                # Clear screen with the SKY colour
                display.set_pen(SKY_COLOUR)
                display.clear()
    else:
        try:
            i2c = machine.I2C()
            sensor = LSM6DS3(i2c, mode=NORMAL_MODE_104HZ)
        except OSError:
            while True:
                show_message("No Multi-Sensor stick detected!\n\nConnect and try again.")
                raise RuntimeError

        # Clear screen with the SKY colour
        display.set_pen(SKY_COLOUR)
        display.clear()

        try:
            # Get the raw readings from the sensor
            ax, ay, az, gx, gy, gz = sensor.get_readings()
        except OSError:
            while True:
                show_message("Multi-Sensor stick disconnected!\n\nReconnect and reset your Presto.")
                

    if use_xp12 and data is None:
        # display.set_pen(BLACK)
        display.set_pen(SKY_COLOUR)
        display.clear()
        ax = 0.0 # Make that the attitude indicator is set horizontal
        ay = 0.0
        x_axis = 370
        x_prev = 370
        y_axis = 370
        y_prev = 370

    # Apply some smoothing to the X and Y
    # and cap the Y with min/max
    if my_debug:
        t1 = "y_axis = {:>6.0f}, alpha = {:4.2f}, ay  {:>6d}, y_prev = {:>6d}".format(y_axis, alpha, ay, y_prev)
        print(TAG + f"{t1}")
    y_axis = max(-11000, min(int(alpha * ay + (1 - alpha) * y_prev), 11000))
    # print(TAG + f"y_axis = {y_axis}")
    y_prev = y_axis

    x_axis = int(alpha * ax + (1 - alpha) * x_prev)
    x_prev = x_axis

    if my_debug:
        t1 = "ax = {:>6d}, ay = {:>6d}, az = {:>6d}".format(ax, ay, az)
        print(TAG + f"{t1}")
        t1 = "x_axis = {:>6.0f}, x_prev = {:>6d}, y_axis = {:>6.0f}, y_prev = {:>6d}".format(x_axis, x_prev, y_axis, y_prev)
        print(TAG + f"{t1}")
    # Draw the ground
    trf.reset()
    trf.rotate(-x_axis / 180, (WIDTH // 2, HEIGHT // 2))
    trf.translate(0, y_axis / 100)

    vector.set_transform(trf)
    display.set_pen(GROUND_COLOUR)
    vector.draw(ground)
    display.set_pen(WHITE)
    vector.draw(horizon)
    vector.draw(pitch_lines)
    vector.set_transform(normal)

    # Draw the aircraft
    display.set_pen(RED)
    vector.draw(craft_centre)
    vector.draw(craft_left)
    vector.draw(craft_right)
    vector.draw(craft_arc)

    display.set_pen(GRAY)
    vector.draw(background_rect)
    display.set_pen(BLACK)
    vector.draw(instrument_outline)

    # Update the screen so we can see our changes
    presto.update()

