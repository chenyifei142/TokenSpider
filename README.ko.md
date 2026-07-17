<p align="center">
  <a href="./README.md">简体中文</a> |
  <a href="./README.en.md">English</a> |
  <a href="./README.zh-TW.md">繁體中文</a> |
  <a href="./README.ja.md">日本語</a> |
  <a href="./README.ko.md">한국어</a>
</p>

# TokenMeter

<p align="center">
  <strong>Windows용 AI Token 사용량, 비용 및 잔액 모니터</strong><br>
  <sub>DeepSeek 및 Xiaomi MiMo용 AI Token Usage, Cost & Balance Monitor.</sub>
</p>

TokenMeter는 DeepSeek와 Xiaomi MiMo의 Token 소비량, API 비용, 계정 잔액 및 과거 추세를 확인하는 가벼운 Windows 데스크톱 도구입니다. 시스템 트레이에 상주하며 플로팅 위젯과 확장 가능한 상세 패널을 제공합니다.

## 기능

- DeepSeek와 Xiaomi MiMo를 지원하며 공급자별 캐시를 분리합니다.
- 드래그, 화면 가장자리 부착, 위치 기억 및 포커스 해제 시 접기를 지원합니다.
- 라이트, 다크 및 Windows 시스템 연동 테마를 제공합니다.
- 잔액, Token 사용량, 비용 추세, 모델 통계, 시간대별 차트와 연간 활동 히트맵을 표시합니다.
- DeepSeek 피크 요금 알림과 전용 Chrome 세션을 통한 MiMo Cookie 수집 및 갱신을 지원합니다.
- 네트워크 오류 시 마지막 성공 데이터를 유지하고 기록은 로컬 SQLite에 저장합니다.
- API Key, Bearer Token 및 Cookie를 Windows 자격 증명 관리자에 저장합니다.
- 데이터 디렉터리 이전, 자동 업데이트 및 단일 인스턴스 실행을 지원합니다.

## 화면

| 라이트 테마 | 다크 테마 |
| --- | --- |
| ![TokenMeter 라이트 테마](docs/images/token-spider-ui-v3-light.png) | ![TokenMeter 다크 테마](docs/images/token-spider-ui-v3-dark.png) |

## 시스템 요구 사항

- Windows 10 또는 Windows 11. 소스 실행에는 Python 3.11+가 필요합니다.
- DeepSeek 또는 Xiaomi MiMo Token Plan 계정과 해당 Cookie / Token.
- 공식 잔액 API용 DeepSeek API Key는 선택 사항입니다.

> [!IMPORTANT]
> 사용량 데이터는 웹 콘솔 엔드포인트에 의존하며 MiMo Cookie에는 `api-platform_ph`가 포함되어야 합니다. 플랫폼 API나 위험 제어 정책 변경으로 데이터가 일시적으로 영향을 받을 수 있습니다. 본인 자격 증명만 안전하게 사용하세요.

## 다운로드

[GitHub Releases](https://github.com/zensoku142/TokenMeter/releases/latest)에서 `TokenMeter-v{version}-windows-x64.exe`를 다운로드하세요. 포터블 빌드는 Python이 필요하지 않습니다. SmartScreen 경고가 표시되면 먼저 `SHA256SUMS.txt`와 대조하세요.

## 빠른 시작

```powershell
git clone https://github.com/zensoku142/TokenMeter.git
cd TokenMeter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## 최초 설정

1. 앱을 시작하고 플로팅 위젯을 클릭해 패널을 엽니다.
2. 설정에서 DeepSeek 또는 Xiaomi MiMo를 선택합니다.
3. Bearer Token, Cookie 또는 선택적 DeepSeek API Key를 입력합니다. MiMo Cookie 가져오기 기능은 `api-platform_ph`도 자동 추출합니다.
4. 저장 후 새로 고칩니다. 기본 새로 고침 간격은 60초입니다.

`config.example.py`는 필드 설명용이므로 `config.py`로 복사할 필요가 없습니다. 기존 `config.py`는 첫 실행 시 가능한 경우 이전됩니다.

## 로컬 데이터 및 개인정보

이전 TokenSpider 버전과의 호환성을 위해 TokenMeter는 현재도 `%APPDATA%\TokenSpider`를 기본 데이터 디렉터리로 사용합니다. Windows 자격 증명 대상은 계속 `TokenSpider/`로 시작하고 단일 인스턴스 Mutex는 `Local\TokenSpider.SingleInstance`로 유지되므로 다시 로그인할 필요가 없습니다. 이 디렉터리를 수동으로 삭제하거나 이름을 바꾸지 마세요. 향후 `%APPDATA%\TokenMeter`로 이전할 경우 앱이 자동으로 트랜잭션 방식으로 수행해야 합니다.

주요 파일은 `config.json`, `usage.db`, `widget-state.json`, `TokenSpider.log`입니다. 설정에서 새 빈 로컬 디렉터리를 선택하면 재시작 후 모든 데이터를 이전할 수 있습니다. 네트워크 공유는 지원하지 않으며 민감한 자격 증명은 `config.json`에 기록되지 않습니다.

## 자동 업데이트

업데이트 확인은 `zensoku142/TokenMeter`의 GitHub Releases를 사용합니다. 새 첨부 파일은 `TokenMeter-*` 이름을 사용하며 기존 `TokenSpider-*`와 `TokenScope-*`도 인식합니다. `TokenSpider.exe` 또는 `TokenScope.exe`에서 업데이트하면 기존 안정 경로를 유지해 이전 바로 가기가 계속 작동합니다. 버전이 포함된 다운로드 파일은 `TokenMeter.exe`로 이전됩니다.

## 테스트

```powershell
python -m pytest -q
```

Qt 테스트는 사용 가능한 Windows 데스크톱 세션에서 실행하는 것이 좋습니다.

## 빌드

```powershell
python -m pip install pyinstaller
.\.venv\Scripts\pyinstaller.exe --clean --noconfirm TokenMeter.spec
python scripts/build_release.py
```

릴리스 스크립트는 `dist\TokenMeter.exe`, `dist\TokenMeterUpdater.exe`, 버전이 포함된 첨부 파일 2개와 `dist\SHA256SUMS.txt`를 생성합니다. 검증된 환경은 Python 3.12, PyInstaller 6.21, PySide6 6.11이며 UPX는 선택 사항입니다.

## 프로젝트 구조

```text
TokenMeter/
├── api/providers/       # DeepSeek 및 Xiaomi MiMo 어댑터
├── data/                # 집계 및 SQLite 기록
├── tests/               # 단위 및 Qt 테스트
├── ui/                  # PySide6 인터페이스
├── app_identity.py      # 표시 브랜드 및 호환 ID
├── config_manager.py    # 설정, 자격 증명 및 로그
├── main.py              # 앱 진입점
└── TokenMeter.spec      # PyInstaller 설정
```

## 문제 해결

- 미설정: 설정에서 공급자를 선택하고 자격 증명을 입력하세요.
- 자격 증명 만료: Cookie를 다시 가져오세요. MiMo는 먼저 전용 브라우저 세션을 시도합니다.
- 요청 제한 또는 위험 제어: 잠시 기다린 후 새로 고치고 간격을 반복해서 줄이지 마세요.
- 오래된 데이터: `%APPDATA%\TokenSpider\TokenSpider.log`를 확인하세요.
- 창이 없음: 시스템 트레이를 확인하세요. 한 인스턴스만 실행할 수 있습니다.

## 버전 및 Release

현재 버전: `1.9.1`. 변경 사항과 체크섬은 [GitHub Releases](https://github.com/zensoku142/TokenMeter/releases)에서 확인하세요.

## License

현재 저장소에는 별도 라이선스 파일이 없습니다. 사용 또는 재배포 전에 관리자에게 권한을 확인하세요.
