// server.js
const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

// Serve static files dari folder "public"
app.use(express.static(path.join(__dirname, 'public')));

// Endpoint JSON sesuai format HTML-mu
app.get('/api/data', (req, res) => {
  const data = {
    suhumax: 36,
    suhumin: 21,
    suhurata: 28.35,
    nilai_suhu_max_humid_max: [
      {
        idx: 101,
        suhun: 36,
        humid: 36,
        kecerahan: 25,
        timestamp: "2010-09-18 07:23:48"
      },
      {
        idx: 226,
        suhun: 36,
        humid: 36,
        kecerahan: 27,
        timestamp: "2011-05-02 12:29:34"
      }
    ],
    month_year_max: [
      { month_year: "9-2010" },
      { month_year: "5-2011" }
    ]
  };

  res.json(data);
});

// fallback: bila buka / maka serve index.html dari public
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server berjalan di http://localhost:${PORT}`);
});