
import json
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "telecom/site/TELECOM-SITE-001/test"

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to Mosquitto successfully!")

        payload = {
            "site_id": "TELECOM-SITE-001",
            "device_id": "PYTHON-TEST-001",
            "status": "HEALTHY",
            "message": "Python MQTT integration successful",
            "simulation": True
        }

        result = client.publish(
            TOPIC,
            json.dumps(payload),
            qos=1
        )

        print(f"Published to: {TOPIC}")
        print(f"Publish result: {result.rc}")
    else:
        print(f"Connection failed: {reason_code}")

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="telecom-digital-twin-test"
)

client.on_connect = on_connect

try:
    print(f"Connecting to {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, keepalive=60)

    client.loop_start()
    time.sleep(3)
    client.loop_stop()
    client.disconnect()

    print("MQTT test completed.")

except Exception as error:
    print(f"MQTT connection error: {error}")
