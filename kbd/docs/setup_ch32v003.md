# CH32V003 開発環境セットアップ

## 必要なもの

- VSCode
- PlatformIO 拡張機能
- WCH-Link (CH32V003の書き込み/デバッグアダプタ)

---

## 1. PlatformIO インストール

VSCode の拡張機能タブで `PlatformIO IDE` を検索してインストール。

または CLI:
```bash
pip install platformio
```

---

## 2. Community CH32V プラットフォームのインストール

`platformio.ini` に以下が記載済みなので、初回ビルド時に自動インストールされる：

```ini
platform = https://github.com/Community-PIO-CH32V/platform-ch32v.git
```

手動でインストールする場合:
```bash
pio platform install https://github.com/Community-PIO-CH32V/platform-ch32v.git
```

---

## 3. WCH-Link ドライバ (Windows/WSL)

WSL2 から WCH-Link を使うには `usbipd-win` でUSBをアタッチする：

```powershell
# Windows PowerShell (管理者)
usbipd list
usbipd bind --busid <BUS-ID>
usbipd attach --wsl --busid <BUS-ID>
```

```bash
# WSL2 側で確認
lsusb | grep WCH
```

---

## 4. ビルドと書き込み

```bash
cd /home/mushipan3/esp_projects/latecaputa-kbd/ch32v003

# ビルド
pio run

# 書き込み
pio run --target upload

# シリアルモニタ
pio device monitor
```

---

## 5. プロジェクト構成

```
ch32v003/
├── platformio.ini          # PlatformIO設定 (board, framework, lib_deps)
├── include/
│   └── keymap.h            # キーマップ定義 (ABCDEFG配列)
└── src/
    └── main.c              # キースキャナ + I2Cスレーブ
```

---

## 今後の実装TODO

1. **GPIO配線確認** — UIAPduino Pro の実ピン番号に合わせて `kbd_gpio_init()` を実装
2. **キーマトリクス確定** — 実機のキー数・配線に合わせて `keymap.h` を更新
3. **I2Cスレーブ実装** — ch32v003fun の I2C API を使って `i2c_slave_init()` と割り込みハンドラを完成
4. **デバウンス** — 必要に応じてデバウンスフィルタを追加
