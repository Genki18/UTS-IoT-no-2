from _future_ import annotations
from flask import Flask, jsonify, redirect, url_for, send_from_directory, request
from flask_cors import CORS
import mysql.connector as mysql
from mysql.connector import Error
import threading, webbrowser, os
from typing import Any, Tuple, Optional

# =============== CONFIG ===============
DB_CFG = {
    "host":     os.getenv("DB_HOST", "127.0.0.1"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "iot_db"),
}
AUTO_OPEN_BROWSER = os.getenv("AUTO_OPEN_BROWSER", "1") == "1"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")  # contoh: "http://127.0.0.1:5500,http://localhost:5500"

app = Flask(_name_)
CORS(app, resources={r"/*": {"origins": [o.strip() for o in CORS_ORIGINS.split(",")]}})

# =============== DB HELPERS ===============
def _connect():
    """Buat koneksi MySQL baru."""
    return mysql.connect(**DB_CFG)

def qrows(sql: str, args: Tuple[Any, ...] = ()) -> list[dict]:
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, args)
        data = cur.fetchall()
        return data or []
    finally:
        try: cur.close()
        except Exception: pass
        conn.close()

def qscalar(sql: str, args: Tuple[Any, ...] = ()) -> Optional[float]:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, args)
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        try: cur.close()
        except Exception: pass
        conn.close()

# =============== RESPONSE TWEAKS ===============
@app.after_request
def add_no_cache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp

@app.errorhandler(Exception)
def handle_any_error(e):
    # biar error tampil rapih sebagai JSON
    return jsonify({"ok": False, "error": str(e)}), 500

# =============== DASHBOARD (serve index.html) ===============
@app.get("/dashboard")
def serve_dashboard():
    return send_from_directory(os.getcwd(), "index.html")

@app.get("/")
def home():
    # langsung ke dashboard
    return redirect(url_for("serve_dashboard"))

# =============== DEBUG / HEALTH ===============
@app.get("/_health")
def _health():
    try:
        cnt = qscalar("SELECT COUNT(*) FROM data_sensor") or 0
        return jsonify({"ok": True, "count": int(cnt)})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/_debug")
def _debug():
    sample = qrows("""
        SELECT id, suhu, humidity, lux,
                DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i:%S') AS ts
        FROM data_sensor
        ORDER BY id DESC
        LIMIT 5
    """)
    agg = qrows("""
        SELECT
          MAX(suhu)     AS suhumax,
          MIN(suhu)     AS suhummin,
          AVG(suhu)     AS suhurata,
          MAX(humidity) AS max_humid
        FROM data_sensor
        WHERE (suhu IS NOT NULL AND suhu > 0) OR (humidity IS NOT NULL AND humidity > 0)
    """)
    return jsonify({"sample": sample, "agg": (agg[0] if agg else {})})

# =============== API RINGKAS ===============
@app.get("/summary")
def summary():
    """Ringkasan angka saja: max/min/avg suhu dan humidity max."""
    suhumax   = qscalar("SELECT MAX(suhu) FROM data_sensor WHERE suhu IS NOT NULL AND suhu > 0")
    suhummin  = qscalar("SELECT MIN(suhu) FROM data_sensor WHERE suhu IS NOT NULL AND suhu > 0")
    suhurata  = qscalar("SELECT AVG(suhu) FROM data_sensor WHERE suhu IS NOT NULL AND suhu > 0")
    max_humid = qscalar("SELECT MAX(humidity) FROM data_sensor WHERE humidity IS NOT NULL AND humidity > 0")

    def f(x):
        try: return round(float(x), 2)
        except (TypeError, ValueError): return 0.0

    return jsonify({
        "suhumax": f(suhumax),
        "suhumin": f(suhummin),
        "suhurata": f(suhurata),
        "humidmax": f(max_humid),
    })

# =============== API TOP (seperti soal) ===============
@app.get("/data_sensor")
def data_sensor():
    """
    Mengembalikan JSON gabungan: ringkasan + baris data teratas (suhu=max atau humidity=max).
    Query params:
      - limit: jumlah baris top_rows (default 10, max 100)
      - order: 'asc' atau 'desc' berdasarkan timestamp (default asc)
    """
    # --- query params ---
    try:
        limit = min(max(int(request.args.get("limit", 10)), 1), 100)
    except ValueError:
        limit = 10
    order = request.args.get("order", "asc").lower()
    order = "ASC" if order == "asc" else "DESC"

    # --- ringkasan (abaikan NULL/0) ---
    suhumax   = qscalar("SELECT MAX(suhu) FROM data_sensor WHERE suhu IS NOT NULL AND suhu > 0")
    suhummin  = qscalar("SELECT MIN(suhu) FROM data_sensor WHERE suhu IS NOT NULL AND suhu > 0")
    suhurata  = qscalar("SELECT AVG(suhu) FROM data_sensor WHERE suhu IS NOT NULL AND suhu > 0")
    max_humid = qscalar("SELECT MAX(humidity) FROM data_sensor WHERE humidity IS NOT NULL AND humidity > 0")

    # --- top rows (aman placeholder & fleksibel order/limit) ---
    if suhumax is None and max_humid is None:
        top_rows = qrows(f"""
            SELECT id AS idx, suhu AS suhun, humidity AS humid, lux AS kecerahan,
                   DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i:%S') AS timestamp
            FROM data_sensor
            WHERE timestamp IS NOT NULL
            ORDER BY timestamp {order}
            LIMIT {limit}
        """)
    else:
        top_rows = qrows(f"""
            SELECT id AS idx, suhu AS suhun, humidity AS humid, lux AS kecerahan,
                   DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i:%S') AS timestamp
            FROM data_sensor
            WHERE (
                ( %s IS NOT NULL AND suhu = %s )
             OR ( %s IS NOT NULL AND humidity = %s )
            ) AND timestamp IS NOT NULL
            ORDER BY timestamp {order}
            LIMIT {limit}
        """, (suhumax, suhumax, max_humid, max_humid))

    # --- month-year suhu max (aman ONLY_FULL_GROUP_BY) ---
    if suhumax is None:
        month_year = []
    else:
        month_year = qrows("""
          SELECT DATE_FORMAT(t.min_ts, '%m-%Y') AS month_year
          FROM (
              SELECT MIN(timestamp) AS min_ts
              FROM data_sensor
              WHERE timestamp IS NOT NULL AND suhu = %s
              GROUP BY YEAR(timestamp), MONTH(timestamp)
          ) AS t
          ORDER BY t.min_ts
        """, (suhumax,))

    def f(x):
        try: return round(float(x), 2)
        except (TypeError, ValueError): return 0.0

    return jsonify({
        "suhumax": f(suhumax),
        "suhumin": f(suhummin),
        "suhurata": f(suhurata),
        "nilai_suhu_max_humid_max": top_rows,
        "month_year_max": month_year
    })

# =============== API FEED (LATEST N ROWS) ===============
@app.get("/feed")
def feed():
    """
    Mengembalikan N baris TERBARU dari tabel untuk kebutuhan realtime.
    Query params:
      - limit: default 20, max 200
      - order: 'desc' (terbaru dulu) atau 'asc'
    """
    try:
        limit = min(max(int(request.args.get("limit", 20)), 1), 200)
    except ValueError:
        limit = 20
    order = request.args.get("order", "desc").lower()
    order = "DESC" if order != "asc" else "ASC"

    rows = qrows(f"""
        SELECT
          id   AS idx,
          suhu AS suhun,
          humidity AS humid,
          lux  AS kecerahan,
          DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i:%S') AS timestamp
        FROM data_sensor
        WHERE timestamp IS NOT NULL
        ORDER BY timestamp {order}
        LIMIT {limit}
    """)
    return jsonify({"rows": rows, "limit": limit, "order": order})

# =============== AUTO OPEN BROWSER ===============
def _open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if _name_ == "_main_":
    if AUTO_OPEN_BROWSER:
        threading.Timer(1.0, _open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=True)