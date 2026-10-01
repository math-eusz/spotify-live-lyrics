"""Synthetic render CPU comparison; excludes I/O, network and a real terminal.

Run: python benchmarks/render.py [path-to-sylrics-source]
900 frames at 120x36 cells, 180 Hz clock, words-beta and activity visualizer.
Reports three CPU-time samples and their median; lower is better.
"""
import sys,time,json
from pathlib import Path
if len(sys.argv) < 2:
    sys.argv.append(str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,sys.argv[1])
from terminal_ui import Settings,TerminalUI,DEFAULTS
from lyrics import parse_lyrics
from paging import Pages
from visualizer import Visualizer
raw='\n'.join(f'[{i//30:02}:{i*2%60:02}]A longer sample phrase for deterministic typewriter rendering {i}' for i in range(180))
lines=parse_lyrics(raw)
results=[]
for repeat in range(3):
 cfg=Settings('/missing');cfg.values['visualizer']['mode']='activity';ui=TerminalUI(cfg);pages=Pages();v=Visualizer()
 start=time.process_time()
 for frame in range(900):
  pos=frame/180
  body,anchor,gap=pages.render(lines,pos,cfg.values['pages'],typing_mode='words-beta')
  visual=v.frame(cfg.values['visualizer'],True,gap,pos)
  ui.compose('Artist','Benchmark',body,pos,360,True,anchor=anchor,size=(120,36),visual=visual,gap=gap)
 results.append(time.process_time()-start)
print(json.dumps({'version':sys.argv[1],'cpu_seconds':results,'median':sorted(results)[1]}))
