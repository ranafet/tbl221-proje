# Linux kaynak komutları ve test planı

## Kaynak izleme komutları

### `top`

Süreçleri ve toplam CPU/bellek durumunu etkileşimli gösterir. `1` ile çekirdekler ayrı görülebilir, `P` CPU'ya, `M` belleğe göre sıralar, `q` çıkar.

```bash
top
top -b -n 1
```

İkinci biçim tek anlık görüntü üretir ve betiklerde kullanılabilir.

### `ps`

Süreçlerin anlık listesini verir. Aşağıdaki örnek en fazla CPU tüketen 10 süreci gösterir:

```bash
ps -eo pid,ppid,user,%cpu,%mem,stat,comm --sort=-%cpu | sed -n '1,11p'
```

`STAT` alanında `R` çalışan, `S` uyuyan, `D` kesilemeyen bekleme, `Z` zombi süreci belirtir.

### `free`

Fiziksel bellek ve takas kullanımını gösterir:

```bash
free -h
free -s 2
```

Linux dosya önbelleğini gerektiğinde serbest bırakabildiği için kullanılabilir belleği değerlendirirken `free` yerine özellikle `available` sütunu dikkate alınmalıdır. Uygulama da `/proc/meminfo` içindeki `MemAvailable` değerini kullanır.

### `df`

Bağlı dosya sistemlerinin toplam, kullanılan ve kullanılabilir alanını gösterir:

```bash
df -h
df -h /
df -i /
```

`-i`, byte alanı yerine inode tüketimini gösterir.

### `du`

Dosya ve dizinlerin kapladığı alanı hesaplar:

```bash
du -sh /var/log
du -h --max-depth=1 /var | sort -h
```

`df` dosya sistemi düzeyini, `du` erişilebilen dosyaların toplamını ölçer; silinmiş fakat bir süreççe açık tutulan dosyalar nedeniyle sonuçlar farklı olabilir.

## Uygulama testleri

Aşağıdaki testlerde root gerektirmeyen geçici veritabanı kullanılabilir.

### 1. Normal kullanım

```bash
python3 tbl221-record/main.py --database /tmp/tbl221-test.db --interval 1 --verbose
```

10 saniye sonra `Ctrl+C` ile durdurulur. Beklenen: yaklaşık 10 kayıt, 0--100 arası CPU/bellek/disk yüzdeleri ve temiz kapanış. Kontrol:

```bash
python3 -c "import sqlite3; c=sqlite3.connect('/tmp/tbl221-test.db'); print(c.execute('select count(*), min(cpu_percent), max(cpu_percent) from readings').fetchone())"
```

### 2. Kontrollü CPU yükü ve uyarı

Test yapılandırmasında CPU eşiği düşük tutulur veya varsayılan %85 kullanılır. Yük, mevcut mantıksal CPU sayısı kadar süreçle ve sınırlı süreyle oluşturulabilir:

```bash
python3 -c "import multiprocessing,time; end=time.time()+15; f=lambda: exec('while time.time()<end: pass'); ps=[multiprocessing.Process(target=f) for _ in range(multiprocessing.cpu_count())]; [p.start() for p in ps]; [p.join() for p in ps]"
```

Beklenen: CPU grafiğinde belirgin artış; eşik aşılırsa `alerts` tablosunda kayıt ve servis günlüğünde `WARNING`. Sonuç:

```bash
python3 -c "import sqlite3; c=sqlite3.connect('/tmp/tbl221-test.db'); print(c.execute('select datetime(timestamp,\"unixepoch\",\"localtime\"),message from alerts order by id desc limit 5').fetchall())"
```

### 3. systemd yeniden başlatma

Kurulumdan sonra:

```bash
sudo systemctl restart tbl221-record
systemctl is-active tbl221-record
systemctl show tbl221-record -p NRestarts -p ActiveEnterTimestamp
journalctl -u tbl221-record --since "2 minutes ago" --no-pager
```

Beklenen: `active`, yeni bir "Kaynak izleme başladı" günlüğü ve yeniden başlatmadan önce/sonra aynı SQLite dosyasına devam eden zaman damgalı kayıtlar.

### Otomatik test

```bash
python3 -m unittest discover -s tbl221-record/tests -v
python3 -m compileall -q tbl221-record tbl221-graphui
```
