# CenterFrame PDF

[ [English](README.md) | [한국어](README.ko.md) ]

**드래그 앤 드롭 또는 명령줄을 통해 손쉽게 상장과 같은 PDF의 내용을 중앙에 배치합니다.**

---

## 목차

1. [특징](#특징)
2. [빠른 시작](#빠른-시작)
3. [설치](#설치)
4. [사용법](#사용법)
5. [독립 실행 파일 만들기](#독립-실행-파일-만들기)
6. [기여](#기여)
7. [라이선스](#라이선스)

---

## 특징

- **자동 중앙 정렬** – `center_pdf` 함수가 각 페이지의 내용을 분석하여 가로세로 중심에 배치하고 잘림을 방지합니다.
- **CLI 유틸리티** – `center_pdf.py`를 실행하면 `pdfs` 폴더의 모든 PDF가 일괄 변환됩니다.
- **드래그 앤 드롭 GUI** – PyQt6 기반의 사용자 친화적인 앱(`pdf_transfer_app.py`)을 제공하며 Windows와 macOS에서 동작합니다.
- **진행률 표시와 취소 기능** – GUI에서 변환 상태를 확인하고 언제든 작업을 취소할 수 있습니다.
- **설정 유지** – 선택한 출력 폴더 경로가 Qt `QSettings`를 통해 저장됩니다.

---

## 빠른 시작

```bash
# 1. 의존성 설치
uv venv --python=3.11
uv sync

# 2. GUI 실행
uv run pdf_transfer_app.py
```

---

## 설치

Python 3.11 이상과 `pip`이 필요합니다. 필요한 패키지는 `pyproject.toml`에 명시되어 있습니다:

```
pdfplumber
pypdf2
pyqt6
```

직접 설치하거나 `uv sync` 명령을 사용할 수 있습니다.

---

## 사용법

### 명령줄

`center_pdf.py`를 실행하면 `pdfs` 폴더에 있는 모든 PDF가 `centered_` 접두사와 함께 새 파일로 저장됩니다.

```bash
uv run center_pdf.py
```

### GUI 애플리케이션

1. `python pdf_transfer_app.py`로 앱을 실행합니다.
2. 출력 폴더를 지정합니다.
3. PDF 파일을 목록에 드래그하거나 **파일 추가...** 버튼을 사용합니다.
4. **변환 시작**을 누르면 각 파일의 진행 상황이 표시됩니다.

---

## 독립 실행 파일 만들기

PyInstaller를 사용하여 파이썬 환경이 없는 곳에서도 실행 가능한 파일을 만들 수 있습니다.

```bash
pyinstaller --onefile --windowed pdf_transfer_app.py
```

생성된 실행 파일은 별도의 파이썬 설치 없이 동작합니다.

---

## 기여

1. 저장소를 포크하고 브랜치를 만듭니다: `git checkout -b feature/my-change`.
2. 명확한 메시지와 함께 커밋합니다.
3. 브랜치를 푸시하고 Pull Request를 생성합니다.

가능한 경우 코드 스타일은 PEP 8을 따르고 적절한 테스트를 포함해 주세요.

---

## 라이선스

본 프로젝트는 **GNU General Public License v3.0** 하에 배포됩니다. 자세한 내용은 [`LICENSE`](LICENSE)를 참고하세요.
