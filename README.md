# Firealarm Lightswitch
## This time with Home Assistant

Basically works on anything that's a switch, just needs a pull-up resistor wired to a raspberry pi (zero W in my case).

This uses MQTT to communicate with my personal homeassistant server when the switch is pressed, or held.

Then the homeassistant server handles the request in any way I like.

