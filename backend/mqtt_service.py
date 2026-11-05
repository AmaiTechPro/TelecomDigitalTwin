
import json
import threading
import asyncio

import paho.mqtt.client as mqtt

from websocket_manager import manager
from telemetry_store import update_telemetry


MQTT_BROKER = "localhost"
MQTT_PORT = 1883

SITE_ID = "TELECOM-SITE-001"

# Telemetry topics only. This excludes the nested control topic.
MQTT_TOPIC = f"telecom/site/{SITE_ID}/+"

# Dedicated topic for simulator fault-control commands.
CONTROL_TOPIC = f"telecom/site/{SITE_ID}/control/faults"


class MQTTService:

    def __init__(self):
        self.connected = threading.Event()
        self.loop = None

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="telecom-digital-twin-api"
        )

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def set_event_loop(self, loop):
        self.loop = loop

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

            if event.get("site_id") != SITE_ID:
                print("[MQTT] Ignored event from unknown site")
                return

            if update_telemetry(event):

                print(
                    f"[MQTT] Updated {event.get('device_id')} "
                    f"| Status: {event.get('status')}"
                )

                # Broadcast telemetry to connected WebSocket clients.
                if self.loop is not None and not self.loop.is_closed():

                    future = asyncio.run_coroutine_threadsafe(
                        manager.broadcast(event),
                        self.loop
                    )

                    def report_broadcast_error(result):
                        try:
                            result.result()
                        except Exception as error:
                            print(
                                f"[WEBSOCKET] Broadcast failed: {error}"
                            )

                    future.add_done_callback(report_broadcast_error)

        except (UnicodeDecodeError, json.JSONDecodeError):
            print(f"[MQTT] Invalid JSON received: {message.topic}")

        except Exception as error:
            print(f"[MQTT] Message processing error: {error}")

    def publish_command(self, command: dict) -> bool:
        """
        Publish a fault-control command to the simulator.
        Returns True only when the MQTT publish is acknowledged.
        """

        if not self.connected.is_set():
            print("[MQTT CONTROL] Cannot publish: MQTT is disconnected")
            return False

        try:
            payload = json.dumps(command)

            result = self.client.publish(
                CONTROL_TOPIC,
                payload=payload,
                qos=1,
                retain=False
            )

            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(
                    f"[MQTT CONTROL] Publish failed: "
                    f"{mqtt.error_string(result.rc)}"
                )
                return False

            # Wait briefly for the broker's QoS 1 acknowledgement.
            result.wait_for_publish(timeout=3)

            if not result.is_published():
                print("[MQTT CONTROL] Publish acknowledgement timed out")
                return False

            print(
                f"[MQTT CONTROL] Command acknowledged by broker: "
                f"{command.get('action')}"
            )

            return True

        except Exception as error:
            print(f"[MQTT CONTROL] Publishing error: {error}")
            return False

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
