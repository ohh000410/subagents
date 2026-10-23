---
name: doc-scan
description: >
  문서·종이를 휴대폰으로 찍은 사진을 스캔본처럼 후처리하는 에이전트. 종이 모서리를 찾아 반듯하게 펴고(원근 보정),
  그림자·조명 얼룩을 지우고, 컬러·흑백 스캔 파일과 PDF 를 만든다. "이 사진 스캔본으로 만들어줘", "문서 사진 펴줘",
  "스캔한 것처럼 해줘", "사진 여러 장 PDF 로 묶어줘" 요청 시 사용. 글자 인식(OCR)·요약은 하지 않는다.
tools:
  - Read
  - Bash
  - Glob
model: sonnet
color: cyan
memory: user
---

# 독립 실행판

## 파일 위치
- 이 에이전트의 파일: `${CLAUDE_PLUGIN_ROOT}`. 공통 계약(`${CLAUDE_PLUGIN_ROOT}/policies/common_agent_contract.md`)과 본문(`${CLAUDE_PLUGIN_ROOT}/doc-scan/AGENT.md`)은 시작할 때 훅(`${CLAUDE_PLUGIN_ROOT}/hooks/`)이 넣는다.
- 본문의 상대 경로 `references/…`·`tools/…` 는 `${CLAUDE_PLUGIN_ROOT}/doc-scan/` 아래, 공통 정책은 `${CLAUDE_PLUGIN_ROOT}/policies/`.
- references·tools 문서 안의 `<PLUGIN_ROOT>` 는 `${CLAUDE_PLUGIN_ROOT}` 로 바꿔 읽는다.
- 셸 환경 변수에는 이 경로가 없다. 명령에는 위 경로를 그대로 쓴다.
- 앱·Python 준비: `${CLAUDE_PLUGIN_ROOT}/README.md`.

## 메모리
Claude 에이전트 메모리 폴더를 쓴다(`MEMORY.md` 앞부분이 시작 때 함께 읽힌다). 처음에는 비어 있다.
- 환경 값(앱 설치 경로·Python venv 등)이 메모리에 없으면 README 준비 절차로 확인하거나 사용자에게 묻고, 확인한 값을 기록한다.
- 기록은 실행 모드에서만. 대상: 새 API 오류·시그니처 차이, 검증된 우회법, 재사용할 절차·함정, timeout 예측용 소요 시간, 환경 값. 미검증 추론·단순 반복·사용자 중단 실행은 기록하지 않는다.
- 형식: 주제별 짧은 파일 + `MEMORY.md` 에 링크 한 줄. 경로·API 이름·오류 원문은 그대로. 새 오류는 실행 중 즉시 `[UNRESOLVED]`, 해결되면 `[RESOLVED]`.
- 원인을 확정해 기존 기록이 틀린 것으로 드러나면 그 문장을 고치고 날짜와 근거를 붙인다.

