from flask import Flask, jsonify
import pymysql

app = Flask(__name__)

# --- KONFIGURASI DATABASE ---
db = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='sensor_db',
    cursorclass=pymysql.cursors.DictCursor
)

@app.route('/data_sensor', methods=['GET'])
def get_data_sensor():
    cursor = db.cursor()

    # Ambil suhu max, min, dan rata-rata
    cursor.execute("SELECT MAX(suhu) AS suhumax, MIN(suhu) AS suhumin, AVG(suhu) AS suhurata FROM data_sensor")
    stats = cursor.fetchone()

    suhumax = stats['suhumax']
    suhumin = stats['suhumin']
    suhurata = round(float(stats['suhurata']), 2)

    # Ambil humidity max
    cursor.execute("SELECT MAX(humidity) AS hummax FROM data_sensor")
    hummax = cursor.fetchone()['hummax']

    # Ambil data yang sesuai dengan suhu max dan humidity max
    cursor.execute("""
        SELECT id AS idx, suhu AS suhun, humidity AS humid, lux AS kecerahan, timestamp
        FROM data_sensor
        WHERE suhu = %s AND humidity = %s
        ORDER BY timestamp
    """, (suhumax, hummax))
    rows = cursor.fetchall()

    nilai_suhu_max_humid_max = []
    month_year_max = []

    for r in rows:
        nilai_suhu_max_humid_max.append({
            "idx": r['idx'],
            "suhun": r['suhun'],
            "humid": r['humid'],
            "kecerahan": r['kecerahan'],
            "timestamp": r['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        })

        # format "month_year": "9-2010"
        ts = r['timestamp']
        month = ts.month
        year = ts.year
        month_year_max.append({
            "month_year": f"{month}-{year}"
        })

    hasil = {
        "suhumax": suhumax,
        "suhumin": suhumin,
        "suhurata": suhurata,
        "nilai_suhu_max_humid_max": nilai_suhu_max_humid_max,
        "month_year_max": month_year_max
    }

    return jsonify(hasil)

if __name__ == '__main__':
    app.run(debug=True)