// Konfigurasi URL API (Node.js Express)
const apiUrl = "http://localhost:3000/api/sensor";

// Fungsi utama untuk memuat data dari API
async function loadData() {
  const dashboard = document.getElementById("dashboard");
  const tableBody = document.getElementById("tableBody");

  try {
    // Tampilkan status loading
    dashboard.innerHTML = `<div class="loading">⏳ Memuat data dari server...</div>`;
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center;">Loading...</td></tr>`;

    // Ambil data dari API
    const response = await fetch(apiUrl);
    const data = await response.json();

    console.log("Data dari API:", data);

    if (!data || data.length === 0) {
      dashboard.innerHTML = `<div class="error">⚠️ Tidak ada data sensor.</div>`;
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center;">Data kosong</td></tr>`;
      return;
    }

    // Ambil suhu max, min, rata-rata untuk dashboard
    const suhuValues = data.map(item => item.suhu);
    const suhumax = Math.max(...suhuValues);
    const suhumin = Math.min(...suhuValues);
    const suhurata = suhuValues.reduce((a, b) => a + b, 0) / suhuValues.length;

    const summary = { suhumax, suhumin, suhurata };
    displayDashboard(summary);

    // Tampilkan tabel riwayat data
    displayTable(data);
  } catch (error) {
    console.error("❌ Gagal memuat data:", error);
    dashboard.innerHTML = `<div class="error">❌ Tidak dapat terhubung ke server.<br>Pastikan Node.js berjalan di port 3000.</div>`;
  }
}

// Fungsi menampilkan dashboard ringkasan
function displayDashboard(data) {
  const dashboard = document.getElementById("dashboard");
  const status = getStatus(data.suhumax);

  dashboard.innerHTML = `
    <div class="card">
      <div class="card-header"><div class="icon temp">🌡️</div><div><div class="card-title">Suhu Maksimum</div></div></div>
      <div class="card-value">${data.suhumax.toFixed(1)}<span class="card-unit">°C</span></div>
      <div class="card-time">${status.text}</div>
    </div>

    <div class="card">
      <div class="card-header"><div class="icon humidity">💧</div><div><div class="card-title">Suhu Minimum</div></div></div>
      <div class="card-value">${data.suhumin.toFixed(1)}<span class="card-unit">°C</span></div>
      <div class="card-time">Data minimum</div>
    </div>

    <div class="card">
      <div class="card-header"><div class="icon light">☀️</div><div><div class="card-title">Rata-rata Suhu</div></div></div>
      <div class="card-value">${data.suhurata.toFixed(1)}<span class="card-unit">°C</span></div>
      <div class="card-time">Data rata-rata</div>
    </div>
  `;
}

// Fungsi menampilkan tabel
function displayTable(rows) {
  const tableBody = document.getElementById("tableBody");
  if (!rows || rows.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center;">Tidak ada data</td></tr>`;
    return;
  }

  let html = "";
  rows.forEach((item, index) => {
    const status = getStatus(item.suhu);
    html += `
      <tr>
        <td>${index + 1}</td>
        <td>${item.suhu.toFixed(1)}</td>
        <td>${item.kelembapan.toFixed(1)}</td>
        <td>${item.kecerahan.toFixed(1)}</td>
        <td><span class="status ${status.class}">${status.text}</span></td>
        <td>${formatDate(item.timestamp)}</td>
      </tr>
    `;
  });
  tableBody.innerHTML = html;
}

// Fungsi menentukan status suhu
function getStatus(suhu) {
  if (suhu > 35) {
    return { text: "BAHAYA", class: "danger" };
  } else if (suhu >= 30 && suhu <= 35) {
    return { text: "PERINGATAN", class: "warning" };
  } else {
    return { text: "NORMAL", class: "normal" };
  }
}

// Format waktu
function formatDate(timestamp) {
  const date = new Date(timestamp);
  if (isNaN(date)) return timestamp;
  return date.toLocaleString("id-ID", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Jalankan otomatis
loadData();
setInterval(loadData, 5000);
