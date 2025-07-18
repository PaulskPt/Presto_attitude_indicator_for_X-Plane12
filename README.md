## Presto attitude indicator for X-Plane12

First a "Thank you!" to Pimoroni and its collaborators for this nice new product, the Pimoroni Presto (standalone: PIM725 or kit: PIM765)
[product](https://shop.pimoroni.com/products/presto?variant=54894104019323)

This is a modified version of the example ```Demo for the Multi-Sensor Stick``` that comes with the [software](https://github.com/pimoroni/presto) for the Presto.


In it's modified version the attitude indicator uses UDP-datagram messages broadcasted by the X-Plane12 [flightsimulator](https://www.x-plane.com/desktop/buy-it/).

## Preparation

Copy both files: ```attitude_indicator.py``` and ```secrets.py``` from this repo onto your Presto device.
In the file ```secrets.py``` fill-in the SSID and PASSWORD of your local WiFi access point.

## Using the original attitude indicator

You still can use this example in its original way.

To use the data from the Multi-Sensor Stick set global variable "use_xp12" to ```False``` (line 13).

## Using X-Plane12 data

Default the global variable "use_xp12" is set to ```True```.

The X-Plane12 flightsimulator will transmit chosen ```datasets``` to a given ```IP-address``` of the ```client``` (this Presto).
```

X-Plane12 > Settings > Data Output >
             activate "Send network data output"
             fill-in the IP address of your Presto device (the IP will be shown at moment of WiFi connection)
             leave the port number to the default nr: 49707.
             See UDP_PORT in line 16.
             in the "General Data Output" page:
             select line "17 Pitch, roll & heading" and activate this in column "Network via UDP"
             If you want to use the Presto display as a function of a Joystick deflection, then
             select line "8 Joystick  aileron/elevator/rudders" and activate this in column "Network via UDP"
             In this case also set the global variable "use_joystick_data" to True (line 13)

```

## Notes
1) the WiFi functionality is only used when the global variable "use_xp12" is set to: ```True```.
2) to see more output: set global variable "my_debug" to ```True``` (line 12)
3) the sensitivity for the deflection of the attitude indicator can be changed by altering the variables: type08_mult and/or type17_mult below:
```
    234 # UDP msg type sensitivity factors
    235 if use_xp12:
    236     msg_type = None
    237     type08_mult = 10000 #  (attitude indicator as function of Joystick movement)
    238     type17_mult = 100   # (attitude indicator as function of Aircraft movement (default))

```

Images: see folder [images](https://github.com/PaulskPt/Presto_attitude_indicator_for_X-Plane12/tree/main/Images)

This example is in the folder [example](https://github.com/PaulskPt/Presto_attitude_indicator_for_X-Plane12/tree/main/example).

For a short video impression see: [video](https://imgur.com/a/rfMumGc)

This is the first try to change the current attitude indicator example for use with the X-Plane12 flightsimulator software.
Suggestions are welcome.

## Known problems
App start problem that was reported here has been solved
  
