import paho.mqtt.client as mqtt
import json
import psycopg2
from datetime import datetime

# DB connection
conn = psycopg2.connect(
    host="YOUR_HOST",
    database="YOUR_DB",
    user="YOUR_USER",
    password="YOUR_PASS"
)
cur = conn.cursor()

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        print("RAW DATA:", data)

        drone_id = data.get("device_sn") or data.get("drone_id")
        lat = data.get("latitude")
        lon = data.get("longitude")
        alt = data.get("altitude")
        battery = data.get("battery")
        speed = data.get("speed")
        timestamp = datetime.utcnow()

        if not drone_id:
            print("Skipping invalid packet")
            return

        cur.execute("""
            INSERT INTO drone_telemetry
            (drone_id, latitude, longitude, altitude, battery, speed, timestamp)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (drone_id, lat, lon, alt, battery, speed, timestamp))

        conn.commit()
        print("Saved:", drone_id)

    except Exception as e:
        print("Error:", e)


client = mqtt.Client()
client.on_message = on_message

client.connect("YOUR_DJI_MQTT_HOST", 1883, 60)

# IMPORTANT: subscribe to ALL topics first (no Thing Model filtering)
client.subscribe("#")

client.loop_forever()