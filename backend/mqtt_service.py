import json
import threading

import paho.mqtt.client as mqtt

from telemetry_store import update_telemetry


MQTT_BROKER = "localhost"
MQTT_PORT = 1883

MQTT_TOPIC = "telecom/site/TELECOM-SITE-001/#"


class MQTTService:

    def __init__(self):
        self.connected = threading.Event()

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="telecom-digital-twin-api"
        )

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, reason_code, properties):

        if reason_code == 0:
            self.connected.set()

            print("[MQTT] Connected to Mosquitto")

            client.subscribe(MQTT_TOPIC, qos=1)

            print(f"[MQTT] Subscribed to {MQTT_TOPIC}")

        else:
            self.connected.clear()
            print(f"[MQTT] Connection failed: {reason_code}")

    def on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties
    ):
        self.connected.clear()
        print(f"[MQTT] Disconnected: {reason_code}")

    def on_message(self, client, userdata, message):

        try:
            event = json.loads(message.payload.decode("utf-8"))

            if not isinstance(event, dict):
                print("[MQTT] Ignored non-object JSON message")
                return

            if event.get("site_id") != "TELECOM-SITE-001":
                print("[MQTT] Ignored event from unknown site")
                return

            if update_telemetry(event):
                print(
                    f"[MQTT] Updated {event.get('device_id')} "
                    f"| Status: {event.get('status')}"
                )

        except (UnicodeDecodeError, json.JSONDecodeError):
            print(f"[MQTT] Invalid JSON received: {message.topic}")

        except Exception as error:
            print(f"[MQTT] Message processing error: {error}")

    def start(self):

        print("[MQTT] Starting MQTT service...")

        self.client.connect_async(
            MQTT_BROKER,
            MQTT_PORT,
            60
        )

        self.client.loop_start()

    def stop(self):

        print("[MQTT] Stopping MQTT service...")

        self.client.disconnect()
        self.client.loop_stop()

        self.connected.clear()

    def is_connected(self):
        return self.connected.is_set()


mqtt_service = MQTTService()