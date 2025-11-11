from machine import Pin
from time import sleep
import dht

# Inisialisasi pin
sensor = dht.DHT11(Pin(8))       # Sensor DHT11 di pin 8
led_hijau = Pin(5, Pin.OUT)
led_kuning = Pin(10, Pin.OUT)
led_merah = Pin(12, Pin.OUT)
relay_pompa = Pin(7, Pin.OUT)
buzzer = Pin(9, Pin.OUT)

while True:
    try:
        sensor.measure()
        suhu = sensor.temperature()
        kelembapan = sensor.humidity()
        print("Suhu: {}°C | Kelembapan: {}%".format(suhu, kelembapan))

        # Kondisi LED dan buzzer
        if suhu > 35:
            led_merah.on()
            led_kuning.off()
            led_hijau.off()
            buzzer.on()
            relay_pompa.on()     # hidupkan pompa
        elif 30 <= suhu <= 35:
            led_merah.off()
            led_kuning.on()
            led_hijau.off()
            buzzer.off()
            relay_pompa.off()
        else:  # suhu < 30
            led_merah.off()
            led_kuning.off()
            led_hijau.on()
            buzzer.off()
            relay_pompa.off()

        sleep(2)  # delay 2 detik antar pembacaan

    except OSError as e:
        print("Gagal membaca sensor:", e)