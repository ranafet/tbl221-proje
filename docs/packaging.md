# Derleme ve yerel paketler

Proje iki bağımsız ikili paket üretir:

- `tbl221-record`: bağımlılıksız kayıt programı, varsayılan yapılandırma, systemd birimi ve man sayfası
- `tbl221-graphui`: PySide6 masaüstü arayüzü, uygulama menüsü girdisi ve man sayfası

Sürüm numarası `Makefile`, iki `pyproject.toml`, `packaging/debian/build.py` ve `packaging/rpm/tbl221.spec` içinde birlikte tutulur.

## Ön koşullar

Temel doğrulama yalnızca Python 3.11+ ve GNU Make gerektirir:

```bash
make test
```

Python dağıtımları için `build` modülü gerekir:

```bash
python3 -m pip install build
make wheels
```

RPM üretimi `rpmbuild` ve GNU tar gerektirir. DEB üreticisi dışarıdan `dpkg-deb` veya `debhelper` gerektirmez.

## DEB

```bash
make package-deb
```

Çıktılar:

```text
dist/deb/tbl221-record_1.0.0_all.deb
dist/deb/tbl221-graphui_1.0.0_all.deb
```

Debian/Ubuntu sürümüne göre PySide6 paket adları farklıysa GraphUI bağımlılıklarının dağıtım sürümüne uyarlanması gerekebilir. Paketleri APT üzerinden kurmak bağımlılıkların çözülmesini sağlar:

```bash
sudo apt install ./dist/deb/tbl221-record_1.0.0_all.deb
sudo apt install ./dist/deb/tbl221-graphui_1.0.0_all.deb
```

## RPM

```bash
make package-rpm
```

Çıktılar dağıtıma özgü RPM alt dizininde, örneğin `dist/rpm/noarch/`, oluşturulur. Kurulum örneği:

```bash
sudo dnf install dist/rpm/noarch/tbl221-record-1.0.0-1.noarch.rpm
sudo dnf install dist/rpm/noarch/tbl221-graphui-1.0.0-1.noarch.rpm
```

openSUSE üzerinde `dnf` yerine `zypper install` kullanılabilir.

## Kurulum yerleşimi

```text
/usr/bin/tbl221-record
/usr/bin/tbl221-graphui
/usr/libexec/tbl221-record/
/usr/libexec/tbl221-graphui/
/usr/lib/systemd/system/tbl221-record.service
/usr/share/applications/tbl221-graphui.desktop
/usr/share/man/man5/
/usr/share/man/man8/
/etc/tbl221-record.toml
/var/lib/tbl221-record/
```

Yapılandırma RPM'de `%config(noreplace)`, DEB'de `conffiles` olarak işaretlenir. Paket kaldırıldığında kullanıcı yapılandırması ve SQLite verileri korunur. Hizmet paket kurulurken sistemin preset politikasına göre etkinleştirilir; elle yönetmek için:

```bash
sudo systemctl enable --now tbl221-record
sudo systemctl status tbl221-record
```

## Tekrarlanabilirlik

DEB üreticisi ve kaynak arşivi `SOURCE_DATE_EPOCH` ortam değişkenini destekler. Temiz çıktı almak için:

```bash
make clean
SOURCE_DATE_EPOCH=0 make package
```
