# SpaceClaim macro Record — 사용자 협업

SPEOS addin GUI button ↔ API 매칭을 헤드리스로 못 찾을 때. 자율 시도(references → reflection → candidate → KB) 전부 실패 후에만.

## 부탁 표현

```
SPEOS addin의 <기능명> button 정확한 API를 자율로 못 찾아서 부탁드립니다.
시도: (1) reflection — class NA, (2) namespace search — 발견 못 함, (3) KB — 결과 없음.

다음 절차로 30초 도와주세요:
1. Speos GUI 띄움
2. Script Editor 열기 (Ctrl+M)
3. ● Record 시작
4. <button명> 클릭 → dialog 옵션 변경 (특히 <모르는 부분>)
5. ⏹ Stop
6. .py 형식 저장 (File > Save As > Python File)
7. 저장 경로 알려주시면 read 해서 API 추출
```

`.scscript` = ZIP (`_script` + `_apiVersion` + `[Content_Types].xml`). `.py` = plain text → `.py` 요청.
```python
import zipfile
with zipfile.ZipFile('New Script.scscript') as z:
    with z.open('_script') as f: print(f.read().decode('utf-8'))
```

## record 결과 형식

```python
# Python Script, API Version = V252
# <Operation block name>
someObj = SpeosDes.SomeClass.Create(); someObj.Name = Name
# EndBlock
# Automatic Compute
someObj.Compute()
# Set '<field path>'
someObj.SomeProp = <value>
# Select an object for '<field path>'
someObj.NestedProp.Set(Selection.Create(...).Items)    # nested setter
```

- `# Set '<path>'` = property assignment / `# Select an object for '<path>'` = nested selection set / `# Automatic Compute` = 변경마다 자동
- 저장 위치 관례: iter 폴더 `New Script (N).py` (Speos 기본). `%USERPROFILE%\Documents\` 로 갈 수 있어 경로 확인 요청
- 잡힘: ribbon button + dialog + OK, property panel 값, Axis dropdown. 안 잡힘: View 회전·zoom, Script Editor 직접 실행
- 한계: GUI 에 없는 internal API 불가. verbose → 정리 필요. 변형(다른 BuildType) 은 별도 record/reflection

## record 후 references 갱신

`speos_addin_parabolic.md`(SpeosDes) 또는 `speos_addin_body_geometry.md`(body ops) 에 클래스·factory·property·검증 호출 패턴(nested setter) 추가. 함정 → `speos_pitfalls_*.md`.
