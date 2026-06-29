# Fruit Ninja — MediaPipe

Web kameranı ve el hareketlerini kullanarak oynanan, Fruit Ninja tarzında bir Python oyunu. İşaret parmağınla düşen meyveleri kes, skorunu yükselt ve 25 meyve kestiğinde **BOOM!** patlamasını tetikle.

## Özellikler

- **El algılama:** MediaPipe Hand Landmarker ile işaret parmağı ucu (landmark 8) takip edilir
- **Düşen meyveler:** Ekranın üstünden hızlıca düşen, şeffaf PNG meyve görselleri
- **Kesme efektleri:** Meyve ikiye bölünür, sıvı damlacıkları ve tahta üzerinde leke efekti
- **Bıçak izi:** Hızlı parmak hareketinde ince, beyaz “kayan yıldız” tarzı kesim çizgisi
- **Ahşap arka plan:** Fruit Ninja tarzı kesikli tahta dokusu
- **Skor sistemi:** Anlık skor, en iyi skor kaydı ve son kesilen meyve ikonu
- **Bomba sayacı:** 25 meyve kesildiğinde patlama animasyonu; sayaç sıfırlanır ve oyun devam eder

## Kullanılan Teknolojiler

| Kütüphane | Görev |
|-----------|--------|
| **OpenCV** | Kamera, görüntü işleme, PNG overlay, oyun döngüsü |
| **MediaPipe** | El ve parmak ucu algılama |
| **NumPy** | Arka plan ve efekt hesaplamaları |

## Proje Yapısı

```
fruit_ninja_mediapipe/
│
├── main.py                 # Ana oyun dosyası
├── hand_landmarker.task    # MediaPipe el algılama modeli (gerekli)
├── best_score.txt          # En iyi skor (otomatik oluşur)
├── README.md
│
├── assets/                 # Şeffaf arka planlı meyve PNG'leri
│   ├── cherry.png
│   ├── grape.png
│   ├── lemon.png
│   ├── orange.png
│   ├── pineapple.png
│   └── watermelon.png
│
└── venv/                   # Python sanal ortamı (isteğe bağlı)
```

## Kurulum

### Gereksinimler

- Python 3.10+
- Web kamerası
- Windows / macOS / Linux

### Adımlar

1. Projeyi bilgisayarına indir veya klonla.

2. Sanal ortam oluştur (önerilir):

```bash
python -m venv venv
```

3. Sanal ortamı aktifleştir:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

4. Bağımlılıkları yükle:

```bash
pip install opencv-python mediapipe numpy
```

> `hand_landmarker.task` dosyası proje kökünde bulunmalıdır. Yoksa [MediaPipe Hand Landmarker](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker) modelini indirip proje klasörüne koy.

## Oyunu Çalıştırma

```bash
python main.py
```

**Windows (sanal ortam ile):**
```powershell
cd fruit_ninja_mediapipe
.\venv\Scripts\python.exe main.py
```

## Nasıl Oynanır?

1. Oyun açıldığında kameranı eline göre konumlandır.
2. Elini kameraya göster; işaret parmağın algılanır.
3. Parmağını **hızlıca** düşen meyvelerin üzerinden geçirerek kes.
4. Her kesim +1 skor verir.
5. **25 meyve** kestiğinde ekranda **BOOM!** patlaması görünür; sayaç sıfırlanır, oyun devam eder.
6. Çıkmak için **Q** tuşuna bas. En iyi skorun `best_score.txt` dosyasına kaydedilir.

## Arayüz

| Öğe | Açıklama |
|-----|----------|
| Sol üst ikon | Son kesilen meyve |
| Sarı sayı | Mevcut skor |
| BEST | En yüksek skor |
| Bomba: X/25 | Patlamaya kalan kesim sayısı |
| BOOM! | 25 kesimde görünen patlama yazısı |

## Kendi Meyveni Ekleme

1. Meyveni **şeffaf arka planlı PNG** olarak çiz (ör. 128×128 veya 256×256).
2. Dosyayı `assets/` klasörüne koy (ör. `apple.png`).
3. Oyunu yeniden başlat — meyve otomatik yüklenir.

PNG dosyasında **alpha kanalı** (şeffaflık) olması gerekir; aksi halde meyve kutu gibi görünür.

## Oyun Mantığı (Kısa)

```
while oyun çalışıyor:
    kameradan el pozisyonunu oku
    ahşap arka planı çiz
    meyveleri yukarıdan aşağı hareket ettir
    parmak hızlı hareket ediyorsa kesim çizgisini çiz
    parmak / çizgi meyveye değerse → kes, skor artır, efekt oluştur
    25 kesim → BOOM! → sayaç sıfırla
    ekranı göster
```

## Sorun Giderme

| Sorun | Olası çözüm |
|-------|-------------|
| Kamera açılmıyor | Başka uygulama kamerayı kullanıyor olabilir; kapatıp tekrar dene |
| El algılanmıyor | Elini kameraya net göster; aydınlık ortamda dene |
| Meyve görünmüyor | `assets/` içinde şeffaf PNG olduğundan emin ol |
| `hand_landmarker.task` hatası | Model dosyasının proje kökünde olduğunu kontrol et |

## Lisans

Bu proje eğitim ve kişisel kullanım amaçlıdır. Fruit Ninja ismi ve görsel stili Halfbrick Studios'a aittir; bu proje resmi bir ürün değildir.
