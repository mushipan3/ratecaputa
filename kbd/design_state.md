# ラテカピュータ キーボード 設計状態ファイル

> このファイルはAIエージェントの引き継ぎ用です。作業開始時に必ず読み込んでください。
> 更新日: 2026-04-23

---

## プロジェクト概要

オリジナルのラテカピュータに付属していたキーボードを復刻し、TinyBASICエミュレータ内蔵の
スタンドアロンデバイスとしても動作するキーボードを製作する。

- メインコントローラ: Waveshare ESP32-C6 Touch LCD（キーボード上部に埋め込み）
- キースキャナ: CH32V003 UIAPduino Pro（I2C subordinate、GPIO不足を補う）
- キー配列: ABCDEFG順（QWERTY非準拠、オリジナル準拠）
- 動作モード: スタンドアロン（TinyBASIC）/ BTキーボード（ラテカピュータ本体に接続）

---

## フォルダ構成

```
latecaputa-kbd/
├── design_state.md          # このファイル
├── docs/
│   ├── concept.md           # プロジェクト概要・背景
│   └── setup_ch32v003.md    # CH32V003開発環境セットアップ手順
├── waveshare-c6/            # ESP32-C6ファームウェア（ESP-IDF）
│   ├── main/main.c          # メインアプリ
│   └── components/
│       ├── kbd_scanner/     # キースキャンI2C受信コンポーネント
│       ├── esp_bsp/         # BSP（ディスプレイ・タッチ・I2C等）
│       └── esp_lcd_jd9853/  # LCDドライバ
└── ch32v003/                # CH32V003ファームウェア（PlatformIO）
    ├── src/main.c           # キースキャンI2C送信
    └── include/keymap.h     # ABCDEFGキーマップ定義
```

---

## ハードウェア仕様

- LCD: JD9853、320×172 ランドスケープ
- タッチ: AXS5106（I2C 0x63）
- IMU: QMI8658（I2C 0x6B）
- CH32V003 ↔ ESP32-C6: I2C接続（CH32V003がsubordinate）
- 電源: バッテリ内蔵（充電回路含む）

---

## 現在の作業状況

### 完了済み
- プロジェクト概念設計・ハードウェア構成確定
- BSPコンポーネント移植（bsp_display, bsp_touch, bsp_i2c等）
- kbd_scannerコンポーネント作成（I2Cキースキャン受信）
- CH32V003キースキャンファームウェア（src/main.c, keymap.h）

### 進行中
（なし）

### 次にやること
- TinyBASICエミュレータ実装（ESP32-C6側）
- BTキーボードHIDプロファイル実装（BLE HID）
- LVGL UI：TinyBASIC画面出力・キー入力表示
- CH32V003とESP32-C6のI2C通信プロトコル確定・テスト
- 基板設計（KiCad）

---

## 設計上の重要な制約・決定事項

- CH32V003はGPIO数が少ないため、マトリクススキャンをI2C経由でESP32-C6に渡す
- BTキーボードモードとスタンドアロンモードはモード切り替えスイッチで分岐
- TinyBASICエミュレータはオリジナルのラテカピュータの動作を忠実に再現する方針

---

## 環境・ツールチェーン

| 用途 | ツール | 状態 |
|------|--------|------|
| ESP32-C6ファームウェア | ESP-IDF (idf.py) | 設定済み |
| CH32V003ファームウェア | VSCode + PlatformIO + ch32v003fun | 設定済み |
| PCB設計 | KiCad | 未着手 |

---

## AIエージェントへの引き継ぎ指示

1. このファイルと `docs/concept.md` を最初に読むこと
2. ESP32-C6側: `waveshare-c6/main/main.c` がエントリポイント
3. CH32V003側: `ch32v003/src/main.c` がエントリポイント
4. 作業完了後は「現在の作業状況」と「次にやること」を更新すること
