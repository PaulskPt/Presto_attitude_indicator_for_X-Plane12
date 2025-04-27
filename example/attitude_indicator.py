# ICON [[(-4.5, 16.82), (-9.92, 6.75), (-19.99, 1.33), (-16.1, -2.5), (-8.17, -1.13), (-2.58, -6.71), (-19.93, -14.1), (-15.33, -18.8), (5.73, -15.08), (12.52, -21.87), (13.6, -22.66), (15.25, -23.11), (16.46, -23.05), (17.73, -22.63), (19.14, -21.42), (19.62, -20.63), (19.97, -19.45), (19.99, -18.25), (19.79, -17.33), (19.32, -16.37), (18.79, -15.72), (11.92, -8.84), (15.64, 12.17), (10.99, 16.82), (3.54, -0.53), (-2.04, 5.05), (-0.61, 12.93), (-4.5, 16.82)]]
# NAME Attitude Indicator
# DESC A Demo for the Multi-Sensor Stick
# Modified version for use with X-Plane12 by Paulus Schulinck (Github handle: @PaulskPt)
from presto import Presto # type: ignore
from picovector import ANTIALIAS_FAST, PicoVector, Polygon, Transform # type: ignore
import machine # type: ignore
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ # type: ignore
import time

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
t = Transform()
normal = Transform()
vector.set_transform(t)

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

if use_xp12:
    UDP_PORT = 49707
    import ezwifi # from ezwifi import EzWiFi # type: ignore
    import socket
    import struct
    # wifi = EzWiFi()
    UDP_IP = ""
    ip = None
    connected = False
    sock = None
    secr = None
    try_cnt = 0
    try_cnt_max = 9
    
    def connect_handler(wifi):
        global connected, ip, secr
        connected = wifi.isconnected()
        ip = wifi.ipv4()
        secr = wifi._secrets()[0]
        # stats = wifi._statuses
        if my_debug:
            print("Hurray! We have a WiFi connection!")
            # print(f"dir(wifi) = {dir(wifi)}")
            print(f"access point SSID = {secr}")
            print(f"ezwifi.ipv4() = {ip}")
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

    def failed_handler(wifi):
        print("Afff...WiFi connection failed!")
        #pass
    
    try:
        #wifi.connect()  # connectd is wifi <generator object 'connect' at 11038b90>object! ()
        ezwifi.connect(verbose=True if my_debug == True else False,
                       connected=connect_handler, failed=failed_handler)
    except ValueError as e:
        while True:
            show_message(e) # type: ignore
    except ImportError as e:
        while True:
            show_message(e) # type: ignore

    if connected == True:
        print(f"Connected to: \"{secr}\"")
        print(f"ip = {ip}")
    else:
        print("wifi not connected")
        raise RuntimeError
            
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
def show_message(text):
    display.set_pen(GRAY)
    display.clear()
    display.set_pen(WHITE)
    display.text(f"{text}", 5, 10, WIDTH, 2)
    presto.update()

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

def setup():
    pass    
    
def main():
    global use_xp12, sock, x_prev, y_prev
    TAG = "main(): "

    setup()
    
    data = None
    addr = None
    ax = 0.0
    ay = 0.0
    az = 0.0
    
    x_axis = 0.0
    y_axis = 0.0
    alpha = 0.15
    
    # UDP msg type sensitivity factors
    msg_type = None
    type08_mult = 10000
    type17_mult = 100
    le_data = 0
    
    while True:
        
        if use_xp12:
            if sock is None:
                if my_debug:
                    print(f"type(sock) = {type(sock)}. Check WiFi. Cannot continue...")
                raise RuntimeError
            else:
                deadline = time.ticks_ms() + 5000 # 5 seconds
                if my_debug:
                    print(f"socket timeout deadline = {deadline} mSecs")
                sock.setblocking(False)  # Switch off blocking.
                while True:
                    try:
                        t_out = deadline - time.ticks_ms()
                        print(f"timeout = {t_out} mSecs")
                        sock.settimeout(t_out)
                        # Receive a packet
                        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
                        if isinstance(data, bytes):
                            if my_debug:
                                print(f"data = \"{data}\"")
                            le_data = len(data)
                            if le_data > 0:
                                if my_debug:
                                    print(f"length data received: {le_data}") # usual: 221 bytes
                                break
                    except TimeoutError as exc:
                        print(f"X-Plane12 receive socket timed out with error: {exc}")
                    except OSError as exc:
                        errnr = exc.args[0]
                        if errnr == 11: # EAGAIN
                            if my_debug:
                                print(f"EAGAIN error occurred. Skipping.")
                            continue
                        else:
                            print(TAG + f"Error: {exc}")
                
                # Decode the packet. Result is a python dict (like a map in C) with values from X-Plane.
                # Example:                         magnetic           true
                #   'roll': 1.05, 'pitch': -4.38, 'heading': 275.43, 'heading2': 271.84}
                if data is None:
                    ax = 0.0 # Make that the attitude indicator is set horizontal
                    ay = 0.0
                    y_axis = 370,
                    y_prev = 370,
                    y_axis = 370,
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
                            ax = values["aileron"]   * type08_mult  # pitch
                            ay = values["elevation"] * type08_mult  # roll
                            az = values["rudder"]    * type08_mult  # heading

                            if not my_debug:
                                t1 = "ax: {:9.5f}, ay: {:9.4f}, az: {:8.2f}".format(ax, ay, az)
                                print(TAG + f"data from X-Plane12: {t1}")
                                # print(TAG + f" values: {values}")
                        else:
                            if my_debug:
                                print(TAG + f"No data received of type: 8")
                    else:
                        if values["type"] == 17: # = aircraft attitude
                            ax = values["roll"]    * type17_mult  # pitch
                            ay = values["pitch"]   * type17_mult  # roll
                            az = values["heading"] * type17_mult  # heading

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
                    

        # Apply some smoothing to the X and Y
        # and cap the Y with min/max
        if my_debug:
            print(TAG + f"y_axis = {y_axis}, alpha = {alpha}, ay  {ay}, y_prev = {y_prev}")
        y_axis = max(-11000, min(int(alpha * ay + (1 - alpha) * y_prev), 11000))
        # print(TAG + f"y_axis = {y_axis}")
        y_prev = y_axis

        x_axis = int(alpha * ax + (1 - alpha) * x_prev)
        x_prev = x_axis

        if my_debug:
            print(TAG + f"ax = {ax}, ay = {ay}, az = {az}")
            print(TAG + f"y_axis = {y_axis}, y_prev = {y_prev}, y_axis = {y_axis}, y_prev = {y_prev}")
        # Draw the ground
        t.reset()
        t.rotate(-x_axis / 180, (WIDTH // 2, HEIGHT // 2))
        t.translate(0, y_axis / 100)

        vector.set_transform(t)
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

if __name__ == '__main__':
    main()