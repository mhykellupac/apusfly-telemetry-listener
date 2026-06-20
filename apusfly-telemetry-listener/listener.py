import os
import json
import paho.mqtt.client as mqtt
import psycopg2

# =======================
# SUPABASE CONNECTION
# =======================

conn = psycopg2.connect(
    host=os.getenv("SUPABASE_HOST"),
    database=os.getenv("SUPABASE_DB"),
    user=os.getenv("SUPABASE_USER"),
    password=os.getenv("SUPABASE_PASSWORD"),
    port=os.getenv("SUPABASE_PORT"),
    sslmode="require"
)

cursor = conn.cursor()

print("✅ Connected to Supabase")

# =======================
# MQTT CALLBACKS
# =======================

def on_connect(client, userdata, flags, rc):
    print("✅ MQTT Connected with code:", rc)

    client.subscribe("apusfly/drone/telemetry")
    print("📡 Subscribed to apusfly/drone/telemetry")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()

        print("📨 Received:", payload)

        data = json.loads(payload)

        sql = """
        INSERT INTO public."ApusFly_DroneTelemetryData"
        (
            drone_id,
            latitude,
            longitude,
            altitude,
            speed,
            battery,
            current_waypoint,
            total_waypoints,
            status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            data.get("drone_id"),
            data.get("lat"),
            data.get("lng"),
            data.get("altitude"),
            data.get("speed"),
            data.get("battery"),
            data.get("current_waypoint"),
            data.get("total_waypoints"),
            data.get("status", "flying")
        )

        cursor.execute(sql, values)
        conn.commit()

        print("💾 Saved to Supabase ✔")

    except Exception as e:
        print("❌ Error:", e)

# =======================
# MQTT SETUP
# =======================

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

print("🔌 Connecting to HiveMQ...")

client.connect("broker.hivemq.com", 1883, 60)

print("🚀 Listening for drone telemetry...")

client.loop_forever()