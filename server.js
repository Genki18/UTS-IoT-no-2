const express = require("express");
const mysql = require("mysql");
const cors = require("cors");

const app = express();
const port = 3000;

app.use(cors());

// 🔧 Konfigurasi koneksi database
const db = mysql.createConnection({
  host: "localhost",
  user: "root",
  password: "",
  database: "hidroponik_iot",
});

// 🔌 Koneksi ke database
db.connect((err) => {
  if (err) {
    console.error("❌ Koneksi database gagal:", err);
  } else {
    console.log("✅ Terhubung ke MySQL (database: hidroponik_iot)");
  }
});

// 📊 Endpoint: Ambil 10 data sensor terakhir + suhu max/min/rata2
app.get("/api/sensor", (req, res) => {
  const sql = `
    SELECT 
      id,
      suhu,
      humidity AS kelembapan,
      lux AS kecerahan,
      timestamp
    FROM data_sensor
    ORDER BY id DESC 
    LIMIT 10
  `;

  db.query(sql, (err, result) => {
    if (err) {
      console.error("❌ Query error:", err);
      return res.status(500).json({ status: "error", message: "Gagal mengambil data sensor" });
    }

    // Hitung suhu max, min, rata-rata
    if (result.length > 0) {
      const suhuValues = result.map((row) => row.suhu);
      const suhuMax = Math.max(...suhuValues);
      const suhuMin = Math.min(...suhuValues);
      const suhuAvg = (
        suhuValues.reduce((a, b) => a + b, 0) / suhuValues.length
      ).toFixed(2);

      return res.json({
        status: "success",
        data: result,
        statistik: {
          suhuMax,
          suhuMin,
          suhuAvg,
        },
      });
    } else {
      return res.json({
        status: "success",
        data: [],
        statistik: null,
      });
    }
  });
});

// 🌡️ Endpoint: Ambil data sensor terbaru (1 record terakhir)
app.get("/api/sensor/latest", (req, res) => {
  const sql = `
    SELECT 
      id,
      suhu,
      humidity AS kelembapan,
      lux AS kecerahan,
      timestamp
    FROM data_sensor
    ORDER BY id DESC 
    LIMIT 1
  `;
  db.query(sql, (err, result) => {
    if (err) {
      console.error("❌ Query error:", err);
      return res.status(500).json({ status: "error", message: "Gagal mengambil data terbaru" });
    }

    if (result.length > 0) {
      res.json({
        status: "success",
        data: result[0],
      });
    } else {
      res.json({
        status: "success",
        data: null,
      });
    }
  });
});

// 🚀 Jalankan server
app.listen(port, () => {
  console.log(`🚀 Server berjalan di http://localhost:${port}`);
});
