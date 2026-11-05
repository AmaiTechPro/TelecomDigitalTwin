
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

MQTT_TOPICS = {
    "TOWER-SENSOR-001": "tower",
    "BACKHAUL-MONITOR-001": "backhaul",
    "RAN-MONITOR-001": "ran",
    "POWER-MONITOR-001": "power"
}

def timestamp():
    return datetime.now(timezone.utc).isoformat()


def clamp(value, minimum, maximum):
    return round(max(minimum, min(value, maximum)), 2)


class TelecomSimulator:

    def __init__(self, scenario="normal"):
        self.scenario = scenario
        self.temperature = 29.0
        self.latency = 24.0
        self.signal_strength = -82.0
        self.battery_level = 96.0

    def tower_sensor(self):
        if self.scenario == "sensor_failure":
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
        self.temperature = clamp(
            self.temperature + random.uniform(-1.2, 1.2),
            20, 50
        )
        if self.scenario == "overheating":
         return {
        "device_id": "TOWER-SENSOR-001",
        "device_type": "ENVIRONMENTAL_SENSOR",
        "status": "CRITICAL",
        "telemetry": {
            "temperature": {"value": 85, "unit": "°C"}
        }
    }

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
                }
            }
        }

    def backhaul_monitor(self):
        if self.scenario == "backhaul_failure":
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
            10, 150
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
        if self.scenario == "congestion":
         return {
        "device_id": "RAN-MONITOR-001",
        "device_type": "RAN_PERFORMANCE_MONITOR",
        "status": "CRITICAL",
        "telemetry": {
            "signal_strength": {"value": -82, "unit": "dBm"},
            "bandwidth_utilization": {"value": 98, "unit": "%"},
            "congestion": True
        }
    }
        self.signal_strength = clamp(
            self.signal_strength + random.uniform(-3, 3),
            -110, -60
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
        if self.scenario == "power_failure":
         return {
        "device_id": "POWER-MONITOR-001",
        "device_type": "POWER_MONITOR",
        "status": "CRITICAL",
        "telemetry": {
            "voltage": {"value": 0, "unit": "V"},
            "battery_level": {"value": 0, "unit": "%"},
            "power_available": False
        }
    }
        self.battery_level = clamp(
            self.battery_level + random.uniform(-0.3, 0.2),
            70, 100
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
        print("MQTT broker connection successful.")
        userdata.set()
    else:
        print(f"MQTT connection failed: {reason_code}")

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
    help="Select the simulation scenario"
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

    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="telecom-digital-twin-simulator",
        userdata=connected
    )

    mqtt_client.on_connect = on_connect

    print("=" * 65)
    print(" TELECOM DIGITAL TWIN - VIRTUAL DEVICE SIMULATOR")
    print("=" * 65)
    print(f"Site ID: {SITE_ID}")
    print(f"Devices: {len(devices)}")
    print(f"Reporting interval: {args.interval} seconds")
    print(f"Scenario: {args.scenario}")
    print("Data source: SIMULATED")
    print("Press CTRL+C to stop.")
    print("=" * 65)

    try:
        print(f"Connecting to MQTT broker {MQTT_BROKER}:{MQTT_PORT}...")

        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()

        if not connected.wait(timeout=10):
            raise RuntimeError("MQTT broker connection timed out.")

        while True:

            for device_function in devices:

                event = {
                    "site_id": SITE_ID,
                    "timestamp": timestamp(),
                    "simulation": True,
                    "data_source": "SIMULATED",
                    **device_function()
                }

                device_id = event["device_id"]
                topic_suffix = MQTT_TOPICS[device_id]

                topic = f"telecom/site/{SITE_ID}/{topic_suffix}"

                payload = json.dumps(event)

                result = mqtt_client.publish(
                    topic,
                    payload,
                    qos=1
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(
                        f"[MQTT PUBLISHED] {topic} {payload}",
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
