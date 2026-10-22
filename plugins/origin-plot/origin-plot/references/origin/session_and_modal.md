# 세션 시작·종료·저장·모달

`tools/origin_verify.py` 의 세션 검사 근거.

## 세션 시작(깨끗한 프로젝트 보장)

- Origin 2019 의 실제 이미지는 `Origin96_64.exe` 인데 `tasklist` 에는 8.3 이름 `ORIGIN~1.EXE` 로 나오기도 한다(실행 방식에 따라 다름). 이름 매칭이 아무것도 못 잡으면 "재시작"이 같은 오염 세션이 된다 — `2>/dev/null` 이 이 실패를 숨긴다. PID 를 구해(`tasklist` 의 `ORIGIN\S*` 줄이나 PowerShell `Get-Process`) 자기 PID 만 종료한다. Git Bash 의 `tasklist | grep -i origin` 은 실행 중에도 빈 출력이 나올 수 있다
- `Dispatch("Origin.ApplicationSI")` 는 실행 중인 인스턴스에 창과 함께 붙는다. 같은 이름의 `newbook name:=...`·`win -t plot ... <이름>` 은 "Name Already Used" 모달(`#32770`)을 띄워 세션이 멈춘다. 선행 증상: `wks.col1.lname$=` 묶음이 #0 에서 실패(엉뚱한 창에 쓰는 중)
- 모든 빌드는 `app.IsModified=False; app.Execute("doc -n;")` 로 빈 프로젝트에서 시작한다. 단 `doc -n;` 이 앞 세션 잔재를 치워 주지는 않는다 — 앞 스크립트의 `Exit()` 가 끝나기 전에 붙으면 이후 `newbook`/`plotxy` 가 앞 그래프에 레이어로 붙고 `%H` 는 그럴듯한 새 이름을 돌려줘 png 로만 드러난다. `Dispatch` 직후 `app.PageBases.Count == 0` 을 확인하고(새로 뜬 Origin 은 0), 아니면 중단한다
- 막힌 세션은 밖에서 `win32gui.EnumWindows` 로 클래스 `#32770` 창을 찾아 진단한다. 제목이 비ASCII 일 수 있으니 `errors='replace'` 로 출력한다

## 종료와 모달

- 저장 없이 닫을 때는 COM 속성 `app.IsModified = False` 를 먼저 쓰고 `app.Exit()`. 수정된 프로젝트를 그냥 Exit 하면 Save As 모달이 떠서 비대화형 세션이 멈춘다. LabTalk `doc.Modified=0;` 은 True 를 반환하지만 플래그는 1 로 남는다(읽기값도 1) — COM 속성만 믿는다
- `app.Save(새경로)` 뒤에 `doc -s;` 를 부르지 않는다 — `doc -s` 는 불러온 원본 .opju 를 덮어쓴다. `Save` 가 True 면 바로 `app.Exit()`
- `app.IsModified = False` 뒤의 `doc -n;` 은 모달 없이 빈 프로젝트를 만든다
- 모달을 띄우는 명령은 세션을 영구히 멈춘다: `type -o save "path";`, `save`/`open`/`exp*` 계열, 파일 경로를 받는 X-function. 처음 쓰는 명령은 별도 프로세스에서 timeout 을 걸고 시험한다 — timeout 이 곧 "이 명령은 모달" 진단이다
- 정상 종료한 스크립트가 COM 참조를 놓으면 Origin 이 스스로 끝난다. 크래시한 스크립트가 남긴 Origin 은 살아 있다 — 단계를 프로세스로 나눌 때는 각 단계를 `IsModified=False; doc -n;` 으로 시작한다

## Exit 지연과 무작위 com_error

- `app.IsModified=False; app.Exit()` 뒤에도 프로세스가 12초 넘게 남을 수 있다(작업집합이 227 MB 에서 143 MB 로 줄어드는 중). 그 사이 시작한 스크립트는 `Dispatch` 로 살아 있는 옛 프로세스에 붙는다 — 기다린 뒤 확인하고, 남아 있으면 자기 PID 만 종료한다
- 한 세션에서 그래프 페이지 여럿을 만들 때 `com_error` −2147023170(RPC server unavailable)·−2147418113(catastrophic failure)이 매번 다른 줄에서 날 수 있다. 같은 문장이 매번 같은 줄에서 실패하는 문장 오류와 이것으로 구별한다. 원인은 확인되지 않았다

## 실패 위치 특정

복합 LabTalk 문이 어디서 멈췄는지는 진행 카운터로 찾는다 — Origin 은 오류 문구를 주지 않는다. 문장 사이에 `__k=i;` 를 끼우고 실행 후 `LTVar("__k")` 를 읽는다. 값이 전체 문장 수면 모두 통과, 아니면 `stmts[k]` 가 원인이다.

## 명령 문법 확인

처음 쓰는 명령·속성은 설치 폴더 `Origin2019\*.ogs` 를 grep 한다. 거기 나오는 문법은 이 버전에서 유효하다.

## 저장과 경로

- `app.Save(r"C:\...\x.opju")` 는 백슬래시 경로에서 파일을 만든다. 슬래시 경로는 즉시 False 를 반환하고 파일이 없다. `expGraph path:=` 는 반대로 슬래시를 요구한다
- 저장 성공은 반환값이 아니라 파일의 mtime·size 로 판정한다. `doc -s` 가 True 인데 mtime 이 변하지 않은 적이 있어 최종 저장은 COM `Save(path)` 로 한다
- 비ASCII 경로에서 `expGraph` 는 True 를 반환하지만 파일을 만들지 않는다(`app.Save`/`app.Load` 는 정상). export 는 ASCII 임시 폴더에 하고 복사한다
- 실패한 `save -i "x.opju";` 는 `x.opju.oggu` 를 남긴다. 저장과 씨름한 뒤에는 출력 폴더의 `.oggu` 를 지운다
