import json
import paho.mqtt.client as mqtt


MQTT_BROKER = "localhost"
MQTT_PORT = 1883

MQTT_TOPIC = "telecom/site/TELECOM-SITE-001/#"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to Mosquitto successfully!")

        client.subscribe(MQTT_TOPIC, qos=1)

        print(f"Subscribed to: {MQTT_TOPIC}")
    else:
        print(f"MQTT connection failed: {reason_code}")


def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode("utf-8"))

        print("\n[TELEMETRY RECEIVED]")
        print(f"Topic: {message.topic}")
        print(f"Device: {payload.get('device_id')}")
        print(f"Status: {payload.get('status')}")
        print(f"Timestamp: {payload.get('timestamp')}")

        print(f"Data: {json.dumps(payload, indent=2)}")

    except json.JSONDecodeError:
        print(f"Invalid JSON received on {message.topic}")

    except Exception as error:
        print(f"Message processing error: {error}")


def main():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="telecom-digital-twin-backend"
    )

    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()

    except KeyboardInterrupt:
        print("\nStopping MQTT subscriber...")

    except Exception as error:
        print(f"MQTT error: {error}")

    finally:
        client.disconnect()
        print("MQTT subscriber stopped.")


if __name__ == "__main__":
    main()