<p align="center">
  <a href="./README.md">简体中文</a> |
  <a href="./README.en.md">English</a> |
  <a href="./README.zh-TW.md">繁體中文</a> |
  <a href="./README.ja.md">日本語</a> |
  <a href="./README.ko.md">한국어</a>
</p>

# TokenMeter

<p align="center">
  <strong>Windows 向け AI Token 使用量・コスト・残高モニター</strong><br>
  <sub>DeepSeek と Xiaomi MiMo の AI Token Usage, Cost & Balance Monitor。</sub>
</p>

TokenMeter は、DeepSeek と Xiaomi MiMo の Token 消費量、API コスト、アカウント残高、履歴傾向を確認する軽量な Windows デスクトップツールです。システムトレイに常駐し、フローティングウィジェットと展開可能な詳細パネルを提供します。

## 機能

- DeepSeek と Xiaomi MiMo に対応し、プロバイダーごとにキャッシュを分離。
- ドラッグ、画面端への吸着、位置記憶、フォーカス喪失時の折りたたみに対応。
- ライト、ダーク、Windows システム連動テーマ。
- 残高、Token 使用量、コスト推移、モデル統計、時間帯グラフ、年間アクティビティヒートマップ。
- DeepSeek のピーク料金通知、専用 Chrome セッションによる MiMo Cookie の取得と更新。
- 通信障害時も最後の成功データを表示し、履歴をローカル SQLite に保存。
- API Key、Bearer Token、Cookie は Windows 資格情報マネージャーに保存。
- データディレクトリ移行、自動更新、単一インスタンス実行。

## スクリーンショット

| ライトテーマ | ダークテーマ |
| --- | --- |
| ![TokenMeter ライトテーマ](docs/images/token-spider-ui-v3-light.png) | ![TokenMeter ダークテーマ](docs/images/token-spider-ui-v3-dark.png) |

## 動作要件

- Windows 10 または Windows 11。ソース実行には Python 3.11+。
- DeepSeek または Xiaomi MiMo Token Plan アカウントと対応する Cookie / Token。
- 公式残高 API 用の DeepSeek API Key は任意。

> [!IMPORTANT]
> 使用量データは Web コンソールのエンドポイントに依存し、MiMo Cookie には `api-platform_ph` が必要です。API やリスク制御の変更で一時的に取得できない場合があります。必ず自分の資格情報だけを安全に使用してください。

## ダウンロード

[GitHub Releases](https://github.com/zensoku142/TokenMeter/releases/latest) から `TokenMeter-v{version}-windows-x64.exe` をダウンロードします。ポータブル版に Python は不要です。SmartScreen が表示された場合は `SHA256SUMS.txt` を照合してください。

## クイックスタート

```powershell
git clone https://github.com/zensoku142/TokenMeter.git
cd TokenMeter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## 初回設定

1. アプリを起動し、フローティングウィジェットをクリックします。
2. 「設定」で DeepSeek または Xiaomi MiMo を選択します。
3. Bearer Token、Cookie、または任意の DeepSeek API Key を入力します。MiMo の Cookie 取得機能は `api-platform_ph` も自動抽出します。
4. 保存して更新します。既定の更新間隔は 60 秒です。

`config.example.py` は項目説明専用で、`config.py` へコピーする必要はありません。旧 `config.py` は初回起動時に可能な範囲で移行されます。

## ローカルデータとプライバシー

旧 TokenSpider との互換性のため、TokenMeter は現在も `%APPDATA%\TokenSpider` を既定のデータディレクトリとして使用します。Windows 資格情報のターゲットは `TokenSpider/` で始まり、単一インスタンス Mutex は `Local\TokenSpider.SingleInstance` のままなので、再ログインは不要です。このディレクトリを手動で削除・改名しないでください。将来 `%APPDATA%\TokenMeter` に移行する場合は、アプリが自動かつトランザクション方式で行う必要があります。

主なファイルは `config.json`、`usage.db`、`widget-state.json`、`TokenSpider.log` です。設定から新しい空のローカルディレクトリへ、再起動後に全データを移せます。ネットワーク共有は非対応です。機密情報は `config.json` に書き込まれません。

## 自動更新

更新確認は `zensoku142/TokenMeter` の GitHub Releases を使用します。新しい添付名は `TokenMeter-*` で、旧 `TokenSpider-*` と `TokenScope-*` も認識します。`TokenSpider.exe` または `TokenScope.exe` からの更新は既存の安定パスを維持し、古いショートカットを保護します。バージョン付きファイルは `TokenMeter.exe` に移行します。

## テスト

```powershell
python -m pytest -q
```

Qt テストは利用可能な Windows デスクトップセッションでの実行を推奨します。

## ビルド

```powershell
python -m pip install pyinstaller
.\.venv\Scripts\pyinstaller.exe --clean --noconfirm TokenMeter.spec
python scripts/build_release.py
```

スクリプトは `dist\TokenMeter.exe`、`dist\TokenMeterUpdater.exe`、2 個のバージョン付き添付、`dist\SHA256SUMS.txt` を生成します。検証済み環境は Python 3.12、PyInstaller 6.21、PySide6 6.11 で、UPX は任意です。

## プロジェクト構成

```text
TokenMeter/
├── api/providers/       # DeepSeek / Xiaomi MiMo アダプター
├── data/                # 集約と SQLite 履歴
├── tests/               # 単体 / Qt テスト
├── ui/                  # PySide6 UI
├── app_identity.py      # 表示名と互換 ID
├── config_manager.py    # 設定、資格情報、ログ
├── main.py              # エントリーポイント
└── TokenMeter.spec      # PyInstaller 設定
```

## トラブルシューティング

- 未設定：設定でプロバイダーと資格情報を入力してください。
- 資格情報の期限切れ：Cookie を再取得してください。MiMo は最初に専用ブラウザーセッションを試します。
- レート制限：しばらく待ってから更新し、間隔を繰り返し短縮しないでください。
- データが古い：`%APPDATA%\TokenSpider\TokenSpider.log` を確認してください。
- ウィンドウがない：システムトレイを確認してください。実行できるのは 1 インスタンスだけです。

## バージョンと Release

現在のバージョン：`1.9.1`。変更履歴とチェックサムは [GitHub Releases](https://github.com/zensoku142/TokenMeter/releases) を参照してください。

## License

現在、独立したライセンスファイルはありません。使用または再配布の前にメンテナーへ確認してください。
