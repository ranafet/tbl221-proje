# OCI test konteyneri

Kök dizindeki `Containerfile`, OCI görüntü yapılandırması ve katman biçimiyle uyumlu araçlar için hazırlanmıştır. Görüntü Python 3.13 ve PySide6 içerir; testleri ayrıcalıksız `65532:65532` kullanıcısıyla çalıştırır.

Konteyner şu kontrolleri uygular:

1. Python kaynaklarını `compileall` ile doğrular.
2. Recorder birim testlerini çalıştırır.
3. Konteynerin `/proc` ve dosya sistemi verilerinden gerçek bir ölçüm alıp geçici SQLite veritabanına yazmasını doğrular.
4. GraphUI uygulamasını Qt `offscreen` platformuyla başlatıp kontrollü biçimde kapatır.

## Podman

Görüntüyü oluşturup çalıştırmak için:

```bash
podman build --file Containerfile --tag tbl221-monitor-test:1.0.0 .
podman run --rm tbl221-monitor-test:1.0.0
```

Aynı işlemin Make hedefi:

```bash
make container-test
```

## Docker

```bash
docker build --file Containerfile --tag tbl221-monitor-test:1.0.0 .
docker run --rm tbl221-monitor-test:1.0.0
```

veya:

```bash
make container-test CONTAINER_ENGINE=docker
```

## Buildah

Buildah ile yalnızca görüntüyü oluşturmak için:

```bash
buildah bud --file Containerfile --tag tbl221-monitor-test:1.0.0 .
```

## Tasarım notları

- `.containerignore`, Git verileri, yerel paket çıktıları, sanal ortamlar ve derleme artıklarını bağlam dışında bırakır.
- Test veritabanı `/tmp` altında oluşturulur ve test sonunda silinir.
- Görüntü servis dağıtımı için değil, tekrarlanabilir test çalıştırmaları için tasarlanmıştır.
- PySide6 tekerlekleri görüntü oluşturulurken Python Package Index üzerinden indirildiği için ilk derlemede ağ erişimi gerekir.
