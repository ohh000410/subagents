"""
plot-digitize 클릭 picker 서버 (human-in-the-loop 축 캘리브레이션).

사용법:
    python picker_server.py <image_path> [port]

- 브라우저로 http://127.0.0.1:<port> 접속 → 이미지 위를 순서대로 클릭.
- 클릭 좌표는 <image폴더>/_clicks.json 에 실시간 저장 (복사 불필요).
- 호출자(메인)는 _clicks.json 을 읽어 캘리브레이션에 사용.

★ 작업별 안내 (2026-07-03 추가) — 정적 HTML의 개수 불일치 문제 해결:
- 이미지와 같은 폴더에 <image폴더>/_task.json 을 두면 HTML 상단에 그대로 렌더된다.
    { "n": 5,
      "title": "figS3a 캘리브",
      "steps": ["① 반원 중심(radial=0.5)", "② radial 1.0(바닥축 '1')",
                 "③ 0°축 상단 끝", "④ -90° 좌측 끝", "⑤ +90° 우측 끝"] }
  → "필요 점 N개"와 각 점 설명이 화면·에이전트 안내와 자동 일치.
  _task.json 이 없으면 기존 generic 예시를 표시한다. do_GET마다 다시 읽으므로
  서버 재시작 없이 _task.json 을 갱신하면 새로고침으로 반영된다.

★ 줌/패닝 (2026-07-03 추가) — 클릭 정밀도:
- Ctrl+휠 = 커서 기준 확대/축소, 드래그(빈 곳)·스크롤 = 패닝, +/−/100%/맞춤 버튼.
- 클릭 좌표는 항상 원본 픽셀(naturalWidth) 기준으로 보정되어 배율과 무관하게 정확.

검증(2026-06-22): 사용자 클릭 캘리브가 자동(외곽호 LSQ)보다 평균오차 2배 낮음
(중심 y를 자동이 55px 틀렸음). 자동 캘리브가 ground truth와 안 맞을 때 이 도구 사용.
"""
import http.server, socketserver, os, sys, json, html as _html

IMG  = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8742
_DIR = os.path.dirname(os.path.abspath(IMG))
CLK  = os.path.join(_DIR, '_clicks.json')
FLAG = os.path.join(_DIR, '_submit.flag')
TASK = os.path.join(_DIR, '_task.json')


def load_task():
    """이미지 폴더의 _task.json 을 읽어 HTML 안내 블록을 만든다. 없으면 generic."""
    if os.path.exists(TASK):
        try:
            with open(TASK, encoding='utf-8') as f:
                t = json.load(f)
            title = _html.escape(str(t.get('title', '클릭 캘리브')))
            n = t.get('n')
            steps = t.get('steps') or []
            n = n if n is not None else len(steps)
            head = f'<b class=lbl>필요 점 {n}개</b> — 순서대로 클릭 후 ✅ 제출'
            if title:
                head = f'<b>{title}</b> · ' + head
            if steps:
                items = ''.join(f'<li>{_html.escape(str(s))}</li>' for s in steps)
                return f'<p>{head}</p><ol style="margin:4px 0 0 18px;padding:0">{items}</ol>'
            return f'<p>{head}</p>'
        except Exception as e:
            return f'<p style="color:#c00">(_task.json 파싱 실패: {_html.escape(str(e))})</p>'
    # fallback: 기존 generic 예시
    return ('<p>순서대로 클릭 → 자동 저장 (복사 불필요).<br>'
            'polar 예: <span class=lbl>① 중심(radial 시작값)</span> → '
            '<span class=lbl>② radial 최외곽</span> '
            '(중심이 시작값과 다르면 ③ 시작값 격자도 클릭). 곡선 점 추가 가능.<br>'
            '<span style="color:#c00">※ _task.json 을 두면 작업별 점 개수·설명이 여기 표시됩니다.</span></p>')


def build_html():
    return '''<!DOCTYPE html><html><head><meta charset="utf-8"><title>Picker</title>
<style>body{font-family:sans-serif;margin:10px}#wrap{display:flex;gap:12px;align-items:flex-start}
#cwrap{overflow:auto;max-width:calc(100vw - 340px);max-height:86vh;border:1px solid #888}
canvas{display:block;cursor:crosshair}
#side{width:300px;flex-shrink:0}textarea{width:100%;height:150px;font-family:monospace}
button{margin:4px 6px 4px 0;padding:6px 12px}.lbl{font-weight:bold;color:#c00}
#status{color:green;font-weight:bold}#zbar{margin:6px 0}#zbar button{padding:4px 10px}
ol li{margin:2px 0}</style></head><body>
<h3>Calibration click tool (auto-save)</h3>
__TASK__
<p style="color:#555;margin:2px 0"><b>★ 미세조정</b>: 점 클릭 후 <b>방향키</b> 1px (<b>Shift+방향키</b> 5px). 기존 점 근처 클릭 = 그 점 선택(마젠타=활성).<br>
<b>★ 줌</b>: <b>Ctrl+마우스휠</b> 확대/축소(커서 기준), 스크롤/드래그 패닝. 크게 볼수록 클릭 정밀도↑.</p>
<div id=zbar><button onclick=zoomBy(1.25)>＋ 확대</button><button onclick=zoomBy(0.8)>－ 축소</button>
<button onclick=setZoom(1)>100%</button><button onclick=fitWidth()>맞춤</button>
<span id=zlbl>100%</span></div>
<div id=wrap><div id=cwrap><canvas id=c></canvas></div>
<div id=side><button onclick=undo()>마지막 취소</button><button onclick=reset()>초기화</button>
<button onclick=submitClicks() style="background:#bfe3bf;font-weight:bold;width:100%;margin-top:8px;padding:10px">✅ 제출 → Claude가 자동 진행</button>
<p id=status>대기 중</p><textarea id=out readonly></textarea></div></div>
<script>
const img=new Image();img.src="/image.png";
const c=document.getElementById("c"),ctx=c.getContext("2d"),out=document.getElementById("out"),st=document.getElementById("status");
const cwrap=document.getElementById("cwrap"),zlbl=document.getElementById("zlbl");
let pts=[], active=-1, zoom=1;
img.onload=()=>{c.width=img.naturalWidth;c.height=img.naturalHeight;applyZoom();redraw();};
function applyZoom(){c.style.width=(c.width*zoom)+"px";c.style.height=(c.height*zoom)+"px";zlbl.textContent=Math.round(zoom*100)+"%";}
function setZoom(z){zoom=Math.max(0.1,Math.min(12,z));applyZoom();redraw();}
function zoomBy(f){setZoom(zoom*f);}
function fitWidth(){if(c.width)setZoom((cwrap.clientWidth-4)/c.width);}
function redraw(){const z=zoom||1;
 // 마커 크기를 배율에 반비례로 그려 화면상 항상 일정(작게) 유지 → 확대 시에도 세부·정밀 클릭 보존
 const R=6/z, CR=28/z, LW1=2.5/z, LW2=1.5/z, F=22/z, OFF=11/z;
 ctx.clearRect(0,0,c.width,c.height);ctx.drawImage(img,0,0);
 pts.forEach((p,i)=>{
  if(i===active){
   ctx.strokeStyle="#ff00ff";ctx.lineWidth=LW1;
   ctx.beginPath();ctx.moveTo(p[0]-CR,p[1]);ctx.lineTo(p[0]+CR,p[1]);ctx.moveTo(p[0],p[1]-CR);ctx.lineTo(p[0],p[1]+CR);ctx.stroke();
   ctx.fillStyle="#ff00ff";ctx.beginPath();ctx.arc(p[0],p[1],R,0,7);ctx.fill();
   ctx.strokeStyle="#fff";ctx.lineWidth=LW2;ctx.beginPath();ctx.arc(p[0],p[1],R,0,7);ctx.stroke();
  } else {
   ctx.fillStyle="red";ctx.beginPath();ctx.arc(p[0],p[1],R,0,7);ctx.fill();
  }
  ctx.fillStyle="#0000cc";ctx.font="bold "+F+"px sans-serif";ctx.fillText(i+1,p[0]+OFF,p[1]-OFF);});}
function save(){fetch("/click",{method:"POST",body:JSON.stringify(pts)})
 .then(()=>{st.textContent="저장됨 ("+pts.length+"점, 활성="+(active+1)+")";}).catch(()=>{st.textContent="저장 실패";});
 out.value=pts.map((p,i)=>(i===active?"▶":" ")+(i+1)+": ("+p[0]+", "+p[1]+")").join("\\n");}
c.onclick=(e)=>{const r=c.getBoundingClientRect();const sx=c.width/r.width,sy=c.height/r.height;
 const x=Math.round(e.offsetX*sx),y=Math.round(e.offsetY*sy);
 let ni=-1,nd=1e9; pts.forEach((p,i)=>{const d=Math.hypot(p[0]-x,p[1]-y);if(d<nd){nd=d;ni=i;}});
 if(ni>=0 && nd<12/zoom){active=ni;} else {pts.push([x,y]);active=pts.length-1;}
 redraw();save();};
cwrap.addEventListener("wheel",(e)=>{if(!e.ctrlKey)return;e.preventDefault();
 const before=zoom;setZoom(zoom*(e.deltaY<0?1.1:0.9));
 // 커서 아래 지점을 고정: 스크롤 위치를 배율 변화에 맞춰 보정
 const rect=cwrap.getBoundingClientRect();const cx=e.clientX-rect.left,cy=e.clientY-rect.top;
 const k=zoom/before;
 cwrap.scrollLeft=(cwrap.scrollLeft+cx)*k-cx;
 cwrap.scrollTop=(cwrap.scrollTop+cy)*k-cy;},{passive:false});
window.addEventListener("keydown",(e)=>{
 if(active<0||active>=pts.length)return;
 const s=e.shiftKey?5:1; let m=true;
 if(e.key==="ArrowUp")pts[active][1]-=s; else if(e.key==="ArrowDown")pts[active][1]+=s;
 else if(e.key==="ArrowLeft")pts[active][0]-=s; else if(e.key==="ArrowRight")pts[active][0]+=s; else m=false;
 if(m){e.preventDefault();redraw();save();}});
function undo(){pts.pop();active=pts.length-1;redraw();save();}
function reset(){pts=[];active=-1;redraw();save();}
function submitClicks(){save();fetch("/submit",{method:"POST"}).then(()=>{st.textContent="✅ 제출됨! Claude가 자동으로 이어서 진행합니다.";}).catch(()=>{st.textContent="제출 실패";});}
</script></body></html>'''.replace('__TASK__', load_task())


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == '/':
            body = build_html().encode('utf-8')
            self.send_response(200); self.send_header('Content-type','text/html; charset=utf-8'); self.end_headers()
            self.wfile.write(body)
        elif self.path == '/image.png':
            with open(IMG,'rb') as f: data=f.read()
            self.send_response(200); self.send_header('Content-type','image/png'); self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path == '/click':
            n=int(self.headers.get('Content-Length',0)); body=self.rfile.read(n)
            with open(CLK,'w',encoding='utf-8') as f: f.write(body.decode('utf-8'))
            self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
        elif self.path == '/submit':
            with open(FLAG,'w',encoding='utf-8') as f: f.write('1')
            self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
        else:
            self.send_response(404); self.end_headers()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORT), H) as httpd:
    print(f'serving http://127.0.0.1:{PORT}  (image: {IMG})')
    print(f'clicks -> {CLK}')
    if os.path.exists(TASK):
        print(f'task   -> {TASK}')
    httpd.serve_forever()
