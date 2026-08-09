# --- Home Assistant / MQTT Settings ---
CLIENT_ID = "pi-fire-alarm"
HA_BROKER_IP = "10.0.0.69"
HA_MQTT_PORT = 1883
HA_MQTT_USER = "your_username"
HA_MQTT_PASS = "your_secret_password"

# --- Hardware Settings ---
GPIO_PIN = 16
HOLD_TIME = 1.5
DEBOUNCE = 0.5
PULL_UP = False

# --- MQTT Topics ---
TOPIC_ACTION = "home/fire_alarm/action"
TOPIC_AVAILABILITY = "home/fire_alarm/availability"
