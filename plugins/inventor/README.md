# inventor

부품 3D 모델과 2D 도면을 만듭니다.

에이전트 설명(Claude 가 맡길지 고를 때 읽는 글): Inventor 2027 COM 에이전트. 기계 부품·조립품을 3D 모델(.ipt/.iam)로 만들거나 STEP/IPT/IAM을 2D 도면(.idw/.pdf)으로 만들 때, 또는 COM API·모델링·도면 오류를 진단할 때 사용. 상담 모드는 진단(코드·근거만, memory write 금지), 실행 모드는 .ipt/.iam 또는 .idw/.pdf 생성→체적 되읽기· 충돌검사·시각검증까지 수행 후 검증된 함정만 기록. SPEOS·ANSYS용 형상과 광학 곡면은 spaceclaim 담당.

## 설치

```
/plugin marketplace add ohh000410/subagents
/plugin install inventor@ohh000410-subagents
```

설치하면 에이전트 이름은 `inventor:inventor` 입니다.

## 필요한 것

| 항목 | 값 |
|---|---|
| Inventor 2027 | `C:\Program Files\Autodesk\Inventor 2027\Bin\Inventor.exe` |
| COM ProgID | `Inventor.Application` |
| venv | 환경 값(PC 마다 다름) |
| IDW Template | `C:\Users\Public\Documents\Autodesk\Inventor 2027\Templates\en-US\Metric\ANSI (mm).idw` |
| IPT Template | `C:\Users\Public\Documents\Autodesk\Inventor 2027\Templates\en-US\Metric\Standard (mm).ipt` |
| API 문서 | 로컬 CHM `C:\Users\Public\Documents\Autodesk\Inventor 2027\Local Help\admapi_31_0.chm` 우선 → `https://help.autodesk.com/view/INVNTOR/2025/ENU/` |

`app.Visible = True` 필수. `False` → `Profiles.AddForSolid` 실패, 모달 정지 감지 불가.

도구가 쓰는 Python 패키지: `pywin32`

## 처음 쓸 때

- 에이전트가 환경 값(앱 경로·venv)을 찾지 못하면 묻습니다. 확인한 값은 에이전트 메모리 `~/.claude/agent-memory/inventor-inventor/` 에 남습니다.
- 도구 설명: `inventor/tools/README.md`.

## 들어 있는 것

- `agents/inventor.md` — 에이전트 정의(공통 규칙 + 본문)
- `inventor/references/` — 6개 파일
- `inventor/tools/` — 5개 파일
- `policies/` — 공통 정책(실패 처리, GUI 창 멈춤 대처)
- `LICENSE` — MIT

## 라이선스

이 저장소의 파일(에이전트 지시문·references·도구)은 MIT 라이선스입니다(`LICENSE`). 에이전트가 다루는 앱(Inventor, Ansys SpaceClaim·SPEOS·Lumerical, Origin, PowerPoint)과 도구가 쓰는 Python 패키지는 들어 있지 않으며, 각자의 라이선스로 설치하고 그 약관을 따라야 합니다.
