# yadisk-shadow

Yandex Disk Shared Folders Metadata & Files Downloader

## Usage

Download shared folder metadata (file tree):

```bash
# Full tree meta
yadisk-shadow Metadata -l "https://disk.yandex.ru/d/XXXXXXXXXXXXXX" -o "metadata.json"

# Subfolder meta
yadisk-shadow Metadata -l "https://disk.yandex.ru/d/XXXXXXXXXXXXXX" -o "metadata.json" -s "/my/shared/subfolder"
```

Download files:

```bash
yadisk-shadow Download -d "/my/parent/directory" -m "metadata.json"
```
