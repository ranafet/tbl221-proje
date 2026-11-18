# TBL221 Linux Sistem Kaynakları İzleme

Bu proje Linux'ta CPU, bellek, takas, disk, süreç sayısı ve load average değerlerini periyodik ölçer; zaman damgasıyla SQLite'a kaydeder, eşik aşımında uyarı üretir ve verileri PySide6 arayüzünde grafikleştirir.

## Bileşenler

- `tbl221-record/`: bağımlılıksız Python kayıt servisi, SQLite katmanı, TOML yapılandırması ve systemd kurulumu
- `tbl221-graphui/`: canlı kartlar, çizgi grafikler, uyarı tablosu ve CSV aktarımı sunan masaüstü arayüzü
- `report/report.tex`: araştırma, mimari ve test senaryolarını içeren proje raporu
- `docs/commands.md`: Linux kaynak izleme komutları ve test reçeteleri

## Kılavuz sayfaları

Her iki programın sistem yönetimi kılavuzları 8. bölüm biçimindedir:

- `docs/tbl221-record.8`
- `docs/tbl221-graphui.8`

Kaynak ağaçtan görüntülemek için örneğin `man ./docs/tbl221-record.8` komutunu kullanın.

## Hızlı başlangıç (root gerektirmez)

Python 3.11 veya üzeri gereklidir.

```bash
cd tbl221-record
python3 main.py --once --database /tmp/tbl221-record.db --verbose
python3 main.py --database /tmp/tbl221-record.db --interval 2
```

Başka bir terminalde arayüzü çalıştırın:

```bash
cd tbl221-graphui
python3 -m pip install PySide6
python3 main.py --database /tmp/tbl221-record.db
```

## Yapılandırma

Örnek dosya `tbl221-record/config/default.toml` içindedir. Ölçüm aralığı, veritabanı/disk yolu, saklama süresi ve CPU/bellek/disk/load eşikleri değiştirilebilir. Aynı kaynak için tekrar uyarılar `cooldown_seconds` süresince bastırılır.

```bash
python3 tbl221-record/main.py --config tbl221-record/config/default.toml
```

Komut satırındaki `--database` ve `--interval` değerleri TOML ayarlarını geçersiz kılar. `TBL221_CONFIG` ve GUI için `TBL221_DATABASE` ortam değişkenleri de desteklenir.

## systemd kurulumu

Kurucu kaynakları `/opt/tbl221-record` altına, yapılandırmayı `/etc/tbl221-record.toml` yoluna ve servisi `/etc/systemd/system` altına yerleştirir. Mevcut yapılandırmayı veya ölçüm verilerini silmez.

```bash
sudo python3 tbl221-record/install.py install
systemctl status tbl221-record
journalctl -u tbl221-record -f
```

Kaldırma (veri ve yapılandırma korunur):

```bash
sudo python3 tbl221-record/install.py uninstall
```

## Derleme ve paketleme

Kullanılabilir hedefleri görmek ve kaynakları doğrulamak için:

```bash
make help
make test
```

Python wheel/sdist çıktıları için `python-build`, RPM için `rpmbuild` gerekir. Debian paketleyici yalnızca Python standart kütüphanesini kullanır:

```bash
make wheels
make package-deb
make package-rpm
# Her iki yerel paket biçimi:
make package
```

Üretilen paketler `dist/deb/` ve `dist/rpm/` altına yazılır. Yerel paket kurulumu programları `/usr` altına, yapılandırmayı `/etc/tbl221-record.toml` yoluna ve systemd birimini `/usr/lib/systemd/system` altına yerleştirir. Ayrıntılar `docs/packaging.md` dosyasındadır.

## Test

```bash
make test
```

Normal kullanım, kontrollü yük ve servis yeniden başlatma adımları `docs/commands.md` dosyasında verilmiştir.
