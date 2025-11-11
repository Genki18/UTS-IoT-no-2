# bridge_mqtt_to_mysql.py
import json
import warnings
from paho.mqtt.client import Client, MQTTMessage
import mysql.connector as mysql

warnings.filterwarnings("ignore")

# ---------- MQTT ----------
BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "esp32/sensor"
CLIENT_ID = "bridge-saver-mysql"

# ---------- MySQL ----------
DB_CFG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",        # isi jika ada
    "database": "iot_db",
    "autocommit": True,
}

# ---------- MySQL init ----------
conn = mysql.connect(**DB_CFG)
cur  = conn.cursor()

# Buat tabel kalau belum ada
cur.execute("""
CREATE TABLE IF NOT EXISTS data_sensor(
  id INT AUTO_INCREMENT PRIMARY KEY,
  suhu FLOAT,
  humidity FLOAT,
  lux FLOAT,
  timestamp DATETIME      -- pakai backtick biar aman
)
""")

# Buat index kalau belum ada (kompatibel untuk MySQL semua versi)
cur.execute("""
SELECT COUNT(1)
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA=%s AND TABLE_NAME='data_sensor' AND INDEX_NAME='idx_ts'
""", (DB_CFG["database"],))
exists = cur.fetchone()[0]
if not exists:
    cur.execute("CREATE INDEX idx_ts ON data_sensor (timestamp)")

print("MySQL ready.")

# ---------- Fungsi simpan ----------
def save_row(suhu: float, hum: float, lux: float) -> None:
    try:
        conn.ping(reconnect=True, attempts=1, delay=0)
    except Exception:
        pass
    cur.execute(
        "INSERT INTO data_sensor (suhu, humidity, lux, timestamp) VALUES (%s, %s, %s, NOW())",
        (suhu, hum, lux)
    )

# ---------- MQTT callbacks ----------
def on_connect(cli: Client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("MQTT connected.")
        cli.subscribe(TOPIC, qos=1)
        print("Subscribed:", TOPIC)
    else:
        print("MQTT connect failed rc=", rc)

def on_message(cli: Client, userdata, msg: MQTTMessage):
    try:
        payload = msg.payload.decode("utf-8", "ignore")
        data = json.loads(payload)
        suhu = float(data.get("temperature", 0) or 0)
        hum  = float(data.get("humidity", 0) or 0)
        lux  = float(data.get("lux", 0) or 0)
        save_row(suhu, hum, lux)
        print(f"Saved: T={suhu} H={hum} L={lux}")
    except json.JSONDecodeError:
        print("Skip: payload bukan JSON")
    except Exception as e:
        print("Error save:", e)

def on_disconnect(cli: Client, userdata, rc, properties=None):
    print("MQTT disconnected rc=", rc)

# ---------- MQTT setup ----------
cli = Client(client_id=CLIENT_ID)
cli.will_set("esp32/bridge_status", payload="OFFLINE", qos=1, retain=True)
cli.on_connect = on_connect
cli.on_message = on_message
cli.on_disconnect = on_disconnect
cli.reconnect_delay_set(min_delay=2, max_delay=30)

cli.connect(BROKER, PORT, keepalive=60)
cli.publish("esp32/bridge_status", payload="ONLINE", qos=1, retain=True)

print("Bridge connected. Waiting messages on", TOPIC)
try:
    cli.loop_forever()
except KeyboardInterrupt:
    print("\nStopping bridge...")
finally:
    try:
        cli.publish("esp32/bridge_status", payload="OFFLINE", qos=1, retain=True)
    except:
        pass
    try:
        cli.disconnect()
    except:
        pass
    try:
        cur.close()
        conn.close()
    except:
        pass