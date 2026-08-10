import signal
import sys
import threading

from gpiozero import Button
from paho.mqtt import client as mqtt_client

# Import env variables
import config as cfg

# Dictionary to track state across functions
state = {
    "long_press_fired": False
}

### MQTT Setup and Callbacks ###
def on_connect(client, userdata, flags, reason_code, properties):
    """
    Callback triggered when the MQTT client successfully connects to the broker.
    Check if reason_code is 0 (success) and publish "online" to the availability topic.
    """
    if reason_code == 0:
        # Broadcast that the Pi is alive and well
        client.publish(cfg.TOPIC_AVAILABILITY, "online", qos=1, retain=True)
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {reason_code}")

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """Callback triggered when disconnected."""
    print(f"Disconnected with reason code: {reason_code}")

def setup_mqtt():
    """
    Initializes the MQTT client, sets the Last Will and Testament, 
    connects to the broker, and starts the background network loop.
    Returns the configured client object.
    """
    client = mqtt_client.Client(
        client_id=cfg.CLIENT_ID,
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
    )

    # Configure
    if cfg.HA_MQTT_USER and cfg.HA_MQTT_PASS:
        client.username_pw_set(cfg.HA_MQTT_USER, cfg.HA_MQTT_PASS)
    client.will_set(cfg.TOPIC_AVAILABILITY, "offline", qos=1, retain=True)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    print(f"Connecting to {cfg.HA_BROKER_IP}:{cfg.HA_MQTT_PORT}...")
    client.connect(cfg.HA_BROKER_IP, cfg.HA_MQTT_PORT, keepalive=60) # Keepalive every 60s
    client.loop_start() # Spawns background network thread
    
    return client

### GPIO Button Handlers ###
def setup_gpio_button():
    """
    Initializes the GPIO button with the specified pin, pull-up/down configuration,
    debounce time, and hold time. Registers the event callbacks for short and long presses.
    Returns the configured Button object.
    """
    button = Button(
        cfg.GPIO_PIN,
        pull_up=cfg.PULL_UP,
        bounce_time=cfg.DEBOUNCE,
        hold_time=cfg.HOLD_TIME
    )

    # Register event callbacks
    button.when_released = handle_short_press
    button.when_held = handle_long_press

    print(f"Initialized GPIO button on pin {cfg.GPIO_PIN}")
    
    return button

def handle_long_press():
    """
    Triggered when the button is held past the HOLD_TIME threshold.
    Set the state flag, print a debug message, and publish the LONG_PRESS payload.
    """
    state["long_press_fired"] = True
    client.publish(cfg.TOPIC_ACTION, "LONG_PRESS", qos=1)
    print("Long Press: published LONG_PRESS to MQTT")

def handle_short_press():
    """
    Triggered when the button is released.
    Check the state flag. If a long press just finished, reset the flag and do nothing.
    If it's a true short press, publish the SHORT_PRESS payload.
    """
    if state["long_press_fired"]:
        # If this was a long press, just reset the flag upon button release
        state["long_press_fired"] = False
    else:
        # If the flag is false, the hold time was never reached. It's a true short press.
        print("Short Press: published SHORT_PRESS to MQTT")
        client.publish(cfg.TOPIC_ACTION, "SHORT_PRESS", qos=1)

### Additional Helper Functions ###
def graceful_exit(sig, frame):
    """
    Catches termination signals to shut down cleanly.
    Publish "offline", stop the MQTT background loop, disconnect, and call sys.exit(0).
    """
    print('Shutting down')
    
    if 'client' in globals():
        client.publish(cfg.TOPIC_AVAILABILITY, "offline", qos=1, retain=True)
        client.loop_stop()
        client.disconnect()
        
    if 'button' in globals():
        button.close()

    sys.exit(0)

### Main Execution Block ###
if __name__ == "__main__":
    # 1. Register signal handlers for SIGINT and SIGTERM to point to graceful_exit
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)

    # Set up MQTT via helper and store the client
    client = setup_mqtt()

    # Set up GPIO button
    button = setup_gpio_button()

    # Setup complete, put main thread to sleep
    print("Setup complete, system active. CPU sleeping while waiting for hardware interrupts...")

    threading.Event().wait()
