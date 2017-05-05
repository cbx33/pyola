# pyola

pyOLA is a python DMX-512 lighting system in very early alpha stages. It is designed to be based
around channel modifiers, rather than static scenes. It has the ability to cross fade between scenes
and the ability to have constantly moving scenes. IT supports a number of modifiers which can be applied
to scenes to allow the continual movement of a channel during a set scene. For example, you may want the
tilt/pan channels to follow sin/cos paths to get a circular motion. This would be set into the scene and
would not require continual setting of keyframed scenes to obtain the movement.

## Suppored Modifiers
Currently there is early support for the following modifiers
* COS
* SIN
* Spline (curve/waypoints)
* Polygon (waypoints)
* Random
* Wave (audio trigger)
* Wiimote (basic acc support)

## Supported Hardware
Assuming you have OLA installed, along with the python bindings (more on this soon).

pyOLA has been tested with the Eurolight DMX512-PRO USB, running under the OLA project, on Fedora 25. Some
steps are necessary to get this to work.

1) Plug in the USB hardware
2) Use ```lsusb``` to find the bus/port number of the device, eg ```Bus 002 Device 004: ID 04d8:fa63 Microchip Technology, Inc. ```
3) Use these to ```chmod 777``` the device file to allow normal users to access it.
4) Run ```olad```

There is almost certainly a better way to do this, but the udev rules tested didn't appear to work

Also, using the Eurolight box requires an extra step in the beginning. The kernel tries to assign the ```cdc_acm```
module to the device making it unusable with pyOLA, you will then need to assign the device to OLA using the web system.
