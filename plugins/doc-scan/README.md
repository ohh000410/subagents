# doc-scan

문서 사진을 스캔본·PDF 로 만듭니다.

에이전트 설명(Claude 가 맡길지 고를 때 읽는 글): 문서·종이를 휴대폰으로 찍은 사진을 스캔본처럼 후처리하는 에이전트. 종이 모서리를 찾아 반듯하게 펴고(원근 보정), 그림자·조명 얼룩을 지우고, 컬러·흑백 스캔 파일과 PDF 를 만든다. "이 사진 스캔본으로 만들어줘", "문서 사진 펴줘", "스캔한 것처럼 해줘", "사진 여러 장 PDF 로 묶어줘" 요청 시 사용. 글자 인식(OCR)·요약은 하지 않는다.

## 설치

```
/plugin marketplace add ohh000410/subagents
/plugin install doc-scan@ohh000410-subagents
```

설치하면 에이전트 이름은 `doc-scan:doc-scan` 입니다. 이 에이전트가 뜰 때만 도는 훅(`hooks/hooks.json`)이 함께 설치되어,
공통 규칙과 본문을 넣습니다.

## 필요한 것

- Windows PowerShell(Windows 에 기본으로 있음) — 위 훅이 씁니다.
| 항목 | 값 |
|---|---|
| 도구 | `doc-scan\tools\.venv\Scripts\python.exe doc-scan\tools\scan.py` — 마지막 줄 JSON. 없으면 `doc-scan\tools\setup.ps1` |
| 읽는 형식 | jpg·png·heic(아이폰)·webp·bmp·tif. EXIF 회전 반영 |
| 쓰는 형식 | color → `<이름>_color.jpg`, gray → `_gray.png`, bw → `_bw.png`, `--pdf <이름>.pdf`(첫 번째 mode 로) |

도구·예제 코드가 쓰는 Python 패키지: `numpy`, `opencv-python-headless`, `pillow`, `pillow-heif`

## 처음 쓸 때

- 에이전트가 환경 값(앱 경로·venv)을 찾지 못하면 묻습니다. 확인한 값은 에이전트 메모리 `~/.claude/agent-memory/doc-scan-doc-scan/` 에 남습니다.
- 도구 환경: `doc-scan/tools/setup.ps1` 이 `doc-scan/tools/.venv` 를 만듭니다. 플러그인을 업데이트하면 다시 만듭니다.

## 들어 있는 것

- `agents/doc-scan.md` — 에이전트 껍데기(이름·설명·도구·모델, 파일 위치·메모리 안내)
- `doc-scan/AGENT.md` — 본문. 에이전트가 뜰 때 훅이 공통 계약과 함께 넣는다
- `hooks/` — 그 훅(`doc-scan:doc-scan` 이 뜰 때만, Windows PowerShell)
- `doc-scan/references/` — 1개 파일
- `doc-scan/tools/` — 5개 파일
- `policies/` — 공통 계약(훅이 넣음), 공통 정책(실패 처리, GUI 창 멈춤 대처)
- `LICENSE` — MIT

## 라이선스

이 저장소의 파일(에이전트 지시문·references·도구)은 MIT 라이선스입니다(`LICENSE`). 에이전트가 다루는 앱(Inventor, Ansys SpaceClaim·SPEOS·Lumerical, Origin, PowerPoint)과 도구가 쓰는 Python 패키지는 들어 있지 않으며, 각자의 라이선스로 설치하고 그 약관을 따라야 합니다.
