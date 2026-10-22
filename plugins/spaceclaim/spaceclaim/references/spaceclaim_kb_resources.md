# SpaceClaim KB·외부 자료

우선순위: references → .NET reflection → 로컬 XML doc grep → 로컬 .chm → 외부 KB/Forum → 사용자 GUI record.

## 로컬 (`%AWP_ROOT261%\scdm\SpaceClaim.Api.V261\`)

| 파일 | 용도 |
|---|---|
| `SpaceClaim.Api.V261.xml` | .NET XML 문서, grep 으로 검색 |
| `API_Class_Library.chm` / `API_Combined_Class_Library.chm` | 전체 API |
| `API_Scripting_Class_Library.chm` | Scripting (IronPython wrapper) — 사용 대상 |
| `SpaceClaim_API.chm` | 일반 API |
| `SpaceClaim.Api.V261.dll` | reflection |

다른 ScriptApi 버전(V14~V261): `scdm/SpaceClaim.Api.V<NNN>/`.

## 외부

| URL | 용도 |
|---|---|
| `https://ansyshelp.ansys.com/public/Views/Secured/corp/v261/en/spaceclaim/Discovery/user_manual/scripting.html` | v261 scripting overview |
| `https://help.spaceclaim.com/2017.0.0/en/Content/Scripting.htm` | scripting 입문 (구버전, 기본 패턴 동일) |
| `https://help.spaceclaim.com/2017.0.0/en/Content/Revolving_edges.htm` / `.../2015.0.0/en/Content/Revolving_faces.htm` | RevolveEdges / RevolveFaces GUI |
| `https://ansyshelp.ansys.com/public/Views/Secured/corp/v261/en/discovery/user_manual/scripting.html` | Discovery scripting (API 다름) |
| `https://forum.ansys.com/` · `https://innovationspace.ansys.com/forum` · `https://discuss.ansys.com/` | Forum |
| `https://www.padtinc.com/2022/05/05/scripting-in-ansys-spaceclaim-part-1/` | PADT 입문 |
| `https://github.com/miromx/Ansys_SpaceClaim_scripts` · `https://github.com/inr-kit/SpaceClaim_scripts` | script 예제 |
| `https://blog.cadfem.net/en/python-scripting-in-ansys-discovery-only-for-nerds` · `https://www.mechead.com/random-beam-generation-using-spaceclaim-python-api/` | 기타 |

## KB fetch (Ansys 403 우회)

WebFetch 는 Ansys KB 에서 403. Chrome UA + `-L`:

```bash
curl -s -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -o "~/AppData/Local/Temp/kb_page.html" "<KB_URL>"
python -c "
import re
html = open(r'~\AppData\Local\Temp\kb_page.html', 'r', encoding='utf-8').read()
text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', ' ', text); text = re.sub(r'\s+', ' ', text)
idx = text.find('<제목 단어>'); print(text[idx:idx+10000] if idx > 0 else text[:3000])
"
```
작업 후 임시 HTML 삭제. `ansyshelp.ansys.com` 로그인 벽: `/account/secured?returnurl=/Views/Secured/...` → `/public/Views/Secured/...`.

검색: `"<클래스명>.Execute" SpaceClaim ironpython` / `"<error message>" SpaceClaim`. `.chm` 추출: `hh.exe -decompile <out_dir> <chm_file>`.
