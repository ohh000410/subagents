# Lumerical FDTD 에이전트 실행 절차

실패·미지 API·공식 예제 확인 시만.

## 재시도 한도

같은 증상만 센다. 수정 후 증상이 바뀌면 리셋, 이전 증상으로 회귀하면 리셋 안 함.

| 실패 지점 | 재실행 비용 | 한도 |
|---|---|---|
| 완주 전 (스크립트·`LumApiError`·import·속성명) | 초 | 3회 |
| 완주 후 (결과 이상·미수렴·추출) | 분~시간 | 2회 |

초과 → KB 대조. KB 로 원인 찾은 뒤 수정에 한도 1회 더. 소진 → §5 escalate. 총 소요 ≤ 한도 × timeout.

## 1. 공식 KB 예제

로컬에 보존한 공식 KB 예제(이 PC 환경 값)가 있으면 먼저 본다. 없으면 Ansys KB 다운로드. WebFetch 403 → `curl` + Chrome UA (`fdtd_kb_resources.md`).

## 2. KB 예제 inspect

```python
fdtd = lumapi.FDTD(hide=False); fdtd.load(KB_FSP_PATH)
fdtd.getnamed("FDTD", "x min bc"); fdtd.getnamed("source", "injection axis"); fdtd.getnamed("monitor", "override global monitor settings")
```
추출: FDTD region · BC · source · monitor · material · mesh refinement · normalization.

## 3. 비교 우선순위

simulation time/autoshutoff → mesh refinement → PML profile/layers → BC → TFSF/source/monitor 위치 → monitor output → 결과 추출 → sourcepower/sourceintensity 정규화

## 4. API 에러

`LumApiError`·속성명·시그니처 불일치 → 워크스테이션 기존 lumapi 스크립트 Grep → `fdtd_lumapi_patterns_basic/advanced.md`, `fdtd_pitfalls_api.md` → KB/Forum → 수정 재실행 → 해결분 memory 기록.

## 5. Escalate 형식

```text
[API 에러 막힘]
원인: <LumApiError 메시지 또는 증상>
시도한 것:
  - <시도 1>
  - <시도 2>
필요한 도움: <사용자 결정/추가 권한/다른 도구>
컨텍스트: <스크립트 경로, 현재 상태>
```
