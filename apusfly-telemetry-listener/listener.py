import os
import json
import paho.mqtt.client as mqtt
import psycopg2
from psycopg2.extras import RealDictCursor

# =======================
# SUPABASE CONNECTION
# =======================

def get_conn():
    return psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        database=os.getenv("SUPABASE_DB"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD"),
        port=os.getenv("SUPABASE_PORT"),
        sslmode="require"
    )

conn = get_conn()
cursor = conn.cursor()

print("✅ Connected to Supabase")

# =======================
# SAFE INSERT FUNCTION
# =======================

def insert_telemetry(data):
    global conn, cursor

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
        data.get("drone_id", "unknown"),
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

# =======================
# MQTT CALLBACKS
# =======================

def on_connect(client, userdata, flags, rc):
    print("✅ MQTT Connected with code:", rc)

    client.subscribe("apusfly/drone/telemetry")
    print("📡 Subscribed to apusfly/drone/telemetry")


def on_message(client, userdata, msg):
    global conn, cursor

    try:
        payload = msg.payload.decode()
        print("📨 Received raw:", payload)

        data = json.loads(payload)

        # =======================
        # VALIDATION
        # =======================
        if not isinstance(data, dict):
            print("❌ Invalid payload format")
            return

        if "lat" not in data or "lng" not in data:
            print("⚠️ Missing GPS data, skipping")
            return

        # =======================
        # INSERT INTO DB
        # =======================
        insert_telemetry(data)

        print("💾 Saved to Supabase ✔")

    except psycopg2.Error as db_err:
        print("❌ DB ERROR:", db_err)

        # reconnect if needed
        conn = get_conn()
        cursor = conn.cursor()

    except Exception as e:
        print("❌ GENERAL ERROR:", e)

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