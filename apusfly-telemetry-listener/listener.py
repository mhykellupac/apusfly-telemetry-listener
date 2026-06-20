import paho.mqtt.client as mqtt
import psycopg2
import json
from datetime import datetime

# =========================
# DATABASE CONNECTION
# =========================
conn = psycopg2.connect(
    host="YOUR_HOST",
    database="YOUR_DB",
    user="YOUR_USER",
    password="YOUR_PASS"
)
cur = conn.cursor()

# =========================
# MQTT MESSAGE HANDLER
# =========================
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        print("DJI RAW:", data)

        # =========================
        # EXTRACT FIELDS
        # =========================
        drone_id = data.get("device_sn") or data.get("drone_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        altitude = data.get("altitude")
        speed = data.get("speed")
        battery = data.get("battery")
        current_waypoint = data.get("current_waypoint")
        total_waypoints = data.get("total_waypoints")
        status = data.get("status", "active")

        if not drone_id:
            print("❌ Missing drone_id, skipping")
            return

        # =========================
        # INSERT INTO YOUR TABLE
        # =========================
        cur.execute("""
            INSERT INTO public."ApusFly_DroneTelemetryData"
            (drone_id, latitude, longitude, altitude, speed,
             battery, current_waypoint, total_waypoints, status, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """, (
            drone_id,
            latitude,
            longitude,
            altitude,
            speed,
            battery,
            current_waypoint,
            total_waypoints,
            status
        ))

        conn.commit()

        print(f"✅ Saved telemetry for {drone_id}")

    except Exception as e:
        print("❌ Error:", e)


# =========================
# MQTT SETUP
# =========================
client = mqtt.Client()
client.on_message = on_message

client.connect("YOUR_MQTT_HOST", 1883, 60)

# IMPORTANT: subscribe to all topics (no Thing Model filtering)
client.subscribe("#")

print("🚁 Listening for DJI telemetry...")
client.loop_forever()