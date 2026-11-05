
import argparse
import json
import random
import time
import threading

import paho.mqtt.client as mqtt

from datetime import datetime, timezone


SITE_ID = "TELECOM-SITE-001"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

CONTROL_TOPIC = f"telecom/site/{SITE_ID}/control/faults"

MQTT_TOPICS = {
    "TOWER-SENSOR-001": "tower",
    "BACKHAUL-MONITOR-001": "backhaul",
    "RAN-MONITOR-001": "ran",
    "POWER-MONITOR-001": "power"
}

ALLOWED_FAULTS = {
    "backhaul_failure",
    "overheating",
    "power_failure",
    "congestion",
    "sensor_failure"
}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def clamp(value, minimum, maximum):
    return round(max(minimum, min(value, maximum)), 2)


class TelecomSimulator:

    def __init__(self, scenario="normal"):

        self.temperature = 29.0
        self.latency = 24.0
        self.signal_strength = -82.0
        self.battery_level = 96.0

        # Protect fault state shared by MQTT and simulator threads.
        self._fault_lock = threading.Lock()

        # Preserve existing startup scenario functionality.
        self.active_faults = set()

        if scenario != "normal":
            self.active_faults.add(scenario)

    def is_fault_active(self, fault):

        with self._fault_lock:
            return fault in self.active_faults

    def get_active_faults(self):

        with self._fault_lock:
            return sorted(self.active_faults)

    def activate_fault(self, fault):

        if fault not in ALLOWED_FAULTS:
            return False

        with self._fault_lock:
            self.active_faults.add(fault)

        return True

    def clear_fault(self, fault):

        with self._fault_lock:
            self.active_faults.discard(fault)

    def clear_all_faults(self):

        with self._fault_lock:
            self.active_faults.clear()

    def tower_sensor(self):

        if self.is_fault_active("sensor_failure"):

            return {
                "device_id": "TOWER-SENSOR-001",
                "device_type": "ENVIRONMENTAL_SENSOR",
                "status": "CRITICAL",
                "telemetry": {
                    "temperature": {
                        "value": None,
                        "unit": "°C"
                    },
                    "sensor_available": False
                }
            }

        if self.is_fault_active("overheating"):

            return {
                "device_id": "TOWER-SENSOR-001",
                "device_type": "ENVIRONMENTAL_SENSOR",
                "status": "CRITICAL",
                "telemetry": {
                    "temperature": {
                        "value": 85.0,
                        "unit": "°C"
                    },
                    "sensor_available": True
                }
            }

        self.temperature = clamp(
            self.temperature + random.uniform(-1.2, 1.2),
            20,
            50
        )

        status = (
            "CRITICAL" if self.temperature >= 45
            else "WARNING" if self.temperature >= 38
            else "HEALTHY"
        )

        return {
            "device_id": "TOWER-SENSOR-001",
            "device_type": "ENVIRONMENTAL_SENSOR",
            "status": status,
            "telemetry": {
                "temperature": {
                    "value": self.temperature,
                    "unit": "°C"
                },
                "sensor_available": True
            }
        }

    def backhaul_monitor(self):

        if self.is_fault_active("backhaul_failure"):

            return {
                "device_id": "BACKHAUL-MONITOR-001",
                "device_type": "BACKHAUL_MONITOR",
                "status": "CRITICAL",
                "telemetry": {
                    "latency": {
                        "value": 999,
                        "unit": "ms"
                    },
                    "packet_loss": {
                        "value": 100,
                        "unit": "%"
                    },
                    "throughput": {
                        "value": 0,
                        "unit": "Mbps"
                    },
                    "link_available": False
                }
            }

        self.latency = clamp(
            self.latency + random.uniform(-4, 4),
            10,
            150
        )

        packet_loss = round(random.uniform(0, 2), 2)
        throughput = round(random.uniform(80, 950), 2)

        status = (
            "WARNING" if self.latency > 80 or packet_loss > 1
            else "HEALTHY"
        )

        return {
            "device_id": "BACKHAUL-MONITOR-001",
            "device_type": "BACKHAUL_MONITOR",
            "status": status,
            "telemetry": {
                "latency": {
                    "value": self.latency,
                    "unit": "ms"
                },
                "packet_loss": {
                    "value": packet_loss,
                    "unit": "%"
                },
                "throughput": {
                    "value": throughput,
                    "unit": "Mbps"
                },
                "link_available": True
            }
        }

    def ran_monitor(self):

        if self.is_fault_active("congestion"):

            return {
                "device_id": "RAN-MONITOR-001",
                "device_type": "RAN_PERFORMANCE_MONITOR",
                "status": "CRITICAL",
                "telemetry": {
                    "signal_strength": {
                        "value": self.signal_strength,
                        "unit": "dBm"
                    },
                    "bandwidth_utilization": {
                        "value": 98.0,
                        "unit": "%"
                    },
                    "congestion": True
                }
            }

        self.signal_strength = clamp(
            self.signal_strength + random.uniform(-3, 3),
            -110,
            -60
        )

        utilization = round(random.uniform(15, 95), 2)

        status = (
            "WARNING" if utilization >= 80
            else "HEALTHY"
        )

        return {
            "device_id": "RAN-MONITOR-001",
            "device_type": "RAN_PERFORMANCE_MONITOR",
            "status": status,
            "telemetry": {
                "signal_strength": {
                    "value": self.signal_strength,
                    "unit": "dBm"
                },
                "bandwidth_utilization": {
                    "value": utilization,
                    "unit": "%"
                },
                "congestion": utilization >= 80
            }
        }

    def power_monitor(self):

        if self.is_fault_active("power_failure"):

            return {
                "device_id": "POWER-MONITOR-001",
                "device_type": "POWER_MONITOR",
                "status": "CRITICAL",
                "telemetry": {
                    "voltage": {
                        "value": 0,
                        "unit": "V"
                    },
                    "battery_level": {
                        "value": 0,
                        "unit": "%"
                    },
                    "power_available": False
                }
            }

        self.battery_level = clamp(
            self.battery_level + random.uniform(-0.3, 0.2),
            70,
            100
        )

        voltage = round(random.uniform(47, 54), 2)

        status = (
            "WARNING" if self.battery_level < 80
            else "HEALTHY"
        )

        return {
            "device_id": "POWER-MONITOR-001",
            "device_type": "POWER_MONITOR",
            "status": status,
            "telemetry": {
                "voltage": {
                    "value": voltage,
                    "unit": "V"
                },
                "battery_level": {
                    "value": self.battery_level,
                    "unit": "%"
                },
                "power_available": True
            }
        }


def on_connect(client, userdata, flags, reason_code, properties):

    if reason_code == 0:

        print("[MQTT] Simulator connected to broker.")

        userdata["connected"].set()

        client.subscribe(CONTROL_TOPIC, qos=1)

        print(f"[CONTROL] Subscribed to {CONTROL_TOPIC}")

    else:

        print(f"[MQTT] Connection failed: {reason_code}")



def on_message(client, userdata, message):

    simulator = userdata["simulator"]

    try:
        raw_payload = message.payload.decode("utf-8")

        print(f"[CONTROL DEBUG] Raw payload: {raw_payload!r}")

        command = json.loads(raw_payload)

        if not isinstance(command, dict):
            print("[CONTROL] Rejected: command must be a JSON object.")
            return

        if command.get("site_id") != SITE_ID:
            print("[CONTROL] Rejected: unknown site.")
            return

        action = command.get("action")
        fault = command.get("fault")

        if action == "activate":

            if not isinstance(fault, str) or fault not in ALLOWED_FAULTS:
                print("[CONTROL] Rejected: invalid fault.")
                return

            simulator.activate_fault(fault)
            print(f"[FAULT ACTIVATED] {fault}")

        elif action == "clear":

            if not isinstance(fault, str) or fault not in ALLOWED_FAULTS:
                print("[CONTROL] Rejected: invalid fault.")
                return

            simulator.clear_fault(fault)
            print(f"[FAULT CLEARED] {fault}")

        elif action == "clear_all":

            simulator.clear_all_faults()
            print("[FAULT CONTROL] All faults cleared.")

        else:
            print(f"[CONTROL] Rejected: unsupported action {action!r}")

    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"[CONTROL] Invalid JSON: {error}")

    except Exception as error:
        print(f"[CONTROL] Command processing error: {error}")


def main():

    parser = argparse.ArgumentParser(
        description="Virtual Telecommunications Device Simulator"
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Seconds between telemetry cycles"
    )

    parser.add_argument(
        "--scenario",
        choices=[
            "normal",
            "backhaul_failure",
            "overheating",
            "congestion",
            "power_failure",
            "sensor_failure"
        ],
        default="normal",
        help="Select the initial simulation scenario"
    )

    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval must be greater than zero")

    simulator = TelecomSimulator(args.scenario)

    devices = [
        simulator.tower_sensor,
        simulator.backhaul_monitor,
        simulator.ran_monitor,
        simulator.power_monitor
    ]

    connected = threading.Event()

    userdata = {
        "simulator": simulator,
        "connected": connected
    }

    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="telecom-digital-twin-simulator",
        userdata=userdata
    )

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    print("=" * 65)
    print(" TELECOM DIGITAL TWIN - VIRTUAL DEVICE SIMULATOR")
    print("=" * 65)
    print(f"Site ID: {SITE_ID}")
    print(f"Devices: {len(devices)}")
    print(f"Reporting interval: {args.interval} seconds")
    print(f"Initial scenario: {args.scenario}")
    print(f"Active faults: {simulator.get_active_faults()}")
    print("Data source: SIMULATED")
    print("Runtime fault control: ENABLED")
    print("Press CTRL+C to stop.")
    print("=" * 65)

    try:

        print(
            f"Connecting to MQTT broker "
            f"{MQTT_BROKER}:{MQTT_PORT}..."
        )

        mqtt_client.connect(
            MQTT_BROKER,
            MQTT_PORT,
            keepalive=60
        )

        mqtt_client.loop_start()

        if not connected.wait(timeout=10):
            raise RuntimeError("MQTT broker connection timed out.")

        while True:

            active_faults = simulator.get_active_faults()

            for device_function in devices:

                event = {
                    "site_id": SITE_ID,
                    "timestamp": timestamp(),
                    "simulation": True,
                    "data_source": "SIMULATED",
                    "active_faults": active_faults,
                    **device_function()
                }

                device_id = event["device_id"]
                topic_suffix = MQTT_TOPICS[device_id]

                topic = (
                    f"telecom/site/{SITE_ID}/{topic_suffix}"
                )

                payload = json.dumps(event)

                result = mqtt_client.publish(
                    topic,
                    payload,
                    qos=1
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:

                    print(
                        f"[MQTT PUBLISHED] {device_id} "
                        f"| Status: {event['status']} "
                        f"| Active faults: {active_faults}",
                        flush=True
                    )

                else:

                    print(
                        f"[MQTT ERROR] Failed to publish {device_id}"
                    )

            time.sleep(args.interval)

    except KeyboardInterrupt:

        print("\nSimulator stopped successfully.")

    finally:

        mqtt_client.disconnect()
        mqtt_client.loop_stop()


if __name__ == "__main__":
    main()
