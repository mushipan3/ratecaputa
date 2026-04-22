# ラテカピュータ 全体設計状態ファイル

> このファイルはAIエージェントの引き継ぎ用です。作業開始時に必ず読み込んでください。
> 更新日: 2026-04-23

---

## プロジェクト概要

ラテカセ（カセットテープケース）にコンピュータを組み込む自作PC/マイコンプロジェクト。
複数のデバイスが連携して一台のラテカピュータとして動作する。

---

## 全体構成

```
ratecaputa/
├── honai/              ← 本体（詳細は honai/design_state.md を参照）
│   ├── waveshare-c6/   ← 電源管理UI・メインコントローラ（ESP-IDF）
│   ├── xiao-c6/        ← サブコントローラ（PlatformIO）
│   ├── raspberry-pi/   ← メインコンピュータ（未着手）
│   ├── windows/        ← Windows連携（未着手）
│   └── cad/            ← 本体筐体CAD（CadQuery）
└── kbd/                ← キーボード（詳細は kbd/design_state.md を参照）
    ├── waveshare-c6/   ← キーボードメインコントローラ（ESP-IDF）
    ├── ch32v003/       ← キーマトリクス スキャナ（PlatformIO）
    ├── cad/            ← キーボード筐体CAD（未着手）
    └── pcb/            ← キーボード基板設計 KiCad（未着手）
```

---

## サブプロジェクト状況

| サブ | 状態 | 次のステップ |
|---|---|---|
| 本体 | 進行中 | 詳細は `honai/design_state.md` 参照 |
| キーボード | 進行中 | 詳細は `kbd/design_state.md` 参照 |

---

## AIエージェントへの引き継ぎ指示

- 本体の作業: `honai/` で Claude / orchestrator.py を起動し `honai/design_state.md` を読むこと
- キーボードの作業: `kbd/` で起動し `kbd/design_state.md` を読むこと
- 全体の方針・構成の話はこのファイルを参照すること
- 運用マニュアル: `~/docs/ratecaputa_dev_guide.md`
