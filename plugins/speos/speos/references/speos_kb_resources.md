# SPEOS KB·외부 자료

우선순위: `references/speos_*.md` → 로컬 .NET reflection → 로컬 XML doc·설치 문서 → Ansys SPEOS 공식/developer portal → forum → GUI record.

| 로컬 | 용도 |
|---|---|
| `C:\Program Files\ANSYS Inc\ANSYS Student\v261\Optical Products\Speos\` | 설치·manifest·default options |
| `C:\Program Files\ANSYS Inc\ANSYS Student\v261\scdm\SpaceClaim.exe` | plug-in host |
| `C:\Program Files\ANSYS Inc\ANSYS Student\v261\scdm\SpaceClaim.Api.V261\SpaceClaim.Api.V261.xml` | host API reflection 보조 |

| URL | 용도 |
|---|---|
| `https://developer.ansys.com/docs/speos` | developer portal |
| `https://speos.docs.pyansys.com/version/stable/` · `https://github.com/ansys/pyspeos` | PySpeos |
| `https://ansyshelp.ansys.com/` | 공식 help |
| `https://innovationspace.ansys.com/forum` · `https://discuss.ansys.com/` | forum |

검색: `"App.Automation.SIM" "<class or property>"` / `"SpeosDes" "<class or error>"` / `"SPEOS" "SensorIrradiance"` / `"SPEOS" "Report.html"` / `"SPEOS" "SpaceClaim" "manifest"`.

Ansys 403 → Chrome UA + `-L`:
```bash
curl -s -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -o "~/AppData/Local/Temp/speos_kb_page.html" "<KB_URL>"
```
임시 HTML 은 작업 후 삭제.
