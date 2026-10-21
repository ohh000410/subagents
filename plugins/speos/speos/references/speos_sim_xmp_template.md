# SPEOS Sim — XMP Template (자동 measure)

.xmp 에 measure(Ellipse Flux 등) 자동 적용 → Report.html / .xml 에 값 export.

```xml
<?xml version="1.0" encoding="ISO-8859-1"?>
<XMP_Template>
  <OptisMapType>3</OptisMapType>
  <OptisValueType>0</OptisValueType>
  <!-- ... default options ... -->
  <AreasVector>
    <OptisMapAreaAndMeasures>
      <AreaClass class="OptisMapAreaTypeSurfaceEllipse">
        <OptisMapArea>
          <Name>"Focal_Plane_Bottom"</Name>
          <OptisMapSurfaceEllipse>
            <Sampling>10000</Sampling>
            <X>0</X><Y>0</Y>            <!-- center mm -->
            <RX>20</RX><RY>20</RY>      <!-- radius mm -->
          </OptisMapSurfaceEllipse>
        </OptisMapArea>
      </AreaClass>
      <MeasuresVector>
        <OptisMapMeasure>
          <Type>8</Type>                                       <!-- 8 = Flux -->
          <!-- ... default options ... -->
        </OptisMapMeasure>
      </MeasuresVector>
    </OptisMapAreaAndMeasures>
  </AreasVector>
</XMP_Template>
```

## Python 자동 생성 (검증)

참조 구현 `snippets/make_template.py`. `make_ellipse_flux_template(out_path, center_x, center_y, rx, ry, ...)` 함수로 다양한 위치·크기 template 생성 가능.
연결: `sens.XMPTemplateFile = r"C:\...\template.xml"; sens.Compute()`. 검증: `sens.XMPTemplateFileFullPath` (RO).
.xmp 시각: `Optical Products/Viewers/XmpViewer.exe`.

## Report.html 의 두 flux

| 패턴 | 의미 |
|---|---|
| `<li>Flux: X W</li>` | sensor 전체 영역 total flux |
| `<td class="value">X W</td>` | 템플릿 영역(Ellipse) 측정 flux |

area flux 는 `<td class="value">` 파싱. `<li>Flux:</li>` 만 파싱하면 다중 sensor 가 전부 같은 값으로 보임.

## 다중 sensor 동시 sim

```python
sim.Sensors.Set(Selection.Create([sens_r19.Subject, sens_r20.Subject, sens_r21.Subject]).Items)
```
Report.html sensor 별 섹션 `<h2>Focal_Plane_r19:92</h2>`:
```python
h2_pattern = re.compile(r"<h2>([^<:]+):\d+</h2>")
matches = list(h2_pattern.finditer(text))
for i, m in enumerate(matches):
    sensor_name = m.group(1).strip()
    section = text[m.end(): matches[i+1].start() if i+1 < len(matches) else len(text)]
    vm = re.search(r'<td class="value">([\d.eE+\-]+)\s*W</td>', section)
```
