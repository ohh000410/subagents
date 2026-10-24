# Project Explorer — 폴더·append

## 폴더 이동·검증

- 기본 명령: `pe_cd /;`, `pe_mkdir "이름";`, `pe_move move:=<창> path:="/폴더";`. 창 이름은 `app.GraphPages`/`MatrixPages`/`WorksheetPages` 로 모음
- 이동 검증: `pe_cd "/폴더"` 의 반환값(없는 폴더는 False — 없는 이름 대조군을 같이 돌림), 메인 창 제목의 `... .opju - /폴더/`, 그 폴더의 창만 보이는 워크스페이스를 PrintWindow 로 캡처(`ImageGrab.grab()` 은 터미널만 찍음)
- 되지 않는 것: `%Z`(이미지 포맷 목록이 나옴), `pe_path()$`(이 빌드에 없음), `doc -e P { }`(프로젝트 전체를 셈), COM `.Folder`/`.FolderPath`/`.Path`(AttributeError)
- 이름 바꾸기: 폴더 = COM `Folder.Name = "새이름"`(`pe_rename` 은 False), 페이지 = `PageBase.Name`. 위치 = `PageBase.PEPath`/`Folder.PEPath`. 폴더를 옮기려면 활성 폴더가 그 폴더의 부모여야 함

## 폴더 삭제 불가

폴더를 지우는 수단은 없음. `pe_rmdir` 은 확인 프롬프트로 무한 대기하고, `Folder.Destroy()` 는 0 을 반환하는 no-op(저장 후 재로드해도 폴더가 남음). 비울 폴더를 만들지 않도록 배치를 설계.

## 프로젝트 append

- `doc -a "<경로>";`(슬래시 경로)는 소스의 폴더 트리 전체를 활성 PE 폴더 아래에 붙임. 이름 충돌은 자동으로 `Book1A`, `Book1B` 로 해결되므로 결과 이름을 추측하지 말고 전후 페이지 이름 집합을 비교. append 순서가 결과 이름을 정하므로 순서를 스크립트에 고정(12개 연속 append 뒤 `app.Save` 0.1초, 재로드 정상)
- 소스에 `Folder1` 래퍼가 붙을지는 예측할 수 없음. 래퍼 폴더는 지울 수 없으므로 루트에서 append 하고, 전후 루트 폴더 집합을 비교해 새 폴더가 있으면 그 래퍼의 이름을 COM 으로 바꾸고 없으면 미리 `pe_cd` 해 둔 폴더를 씀
- 비ASCII 폴더명은 LabTalk 에 넘기지 않음 — ASCII 로 만들고 COM 으로 이름을 바꿈. `doc -a` 의 소스도 ASCII 경로로 복사해 씀

## 모달 함정

`pe_move` 의 대상이 페이지가 이미 있는 폴더이면 "Cannot copy into oneself!" 모달이 떠서 세션이 멈춤. `win -d` 는 복사본을 원본의 폴더에 만듦. `pe_move` 전에 `PEPath` 를 확인.
