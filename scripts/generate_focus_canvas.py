#!/usr/bin/env python3
"""Generate a compact JSON Canvas that guides a reader from question to Focus to Atlas."""
from __future__ import annotations
import argparse
from pathlib import Path
from im_code_map_common import read_json, stable_id, write_json


def node(nid:str,file:str,x:int,y:int,w:int=420,h:int=220)->dict:
    return {"id":nid,"type":"file","file":file,"x":x,"y":y,"width":w,"height":h}

def group(nid:str,label:str,x:int,y:int,w:int,h:int)->dict:
    return {"id":nid,"type":"group","label":label,"x":x,"y":y,"width":w,"height":h}

def edge(eid:str,a:str,b:str,label:str)->dict:
    return {"id":eid,"fromNode":a,"fromSide":"right","toNode":b,"toSide":"left","label":label}

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("session",type=Path); ap.add_argument("output",type=Path); ap.add_argument("--architecture-prefix",default="architecture")
    a=ap.parse_args(); s=read_json(a.session); pre=a.architecture_prefix.rstrip('/'); sid=s['session_id']; stream=s['selected_stream_id']
    nodes=[
      group("g-question","1. 질문과 범위",0,0,500,360),node("n-session",f"{pre}/understanding/{sid}.md",40,80),
      group("g-focus","2. 사람이 먼저 읽는 흐름",600,0,520,620),node("n-focus",f"{pre}/flows/{stream}-focus.md",650,80),node("n-unknown",f"{pre}/unknowns.md",650,340),
      group("g-atlas","3. 필요할 때만 상세 확장",1220,0,520,620),node("n-atlas",f"{pre}/atlas/index.md",1270,80),node("n-atlas-flow",f"{pre}/atlas/flows/{stream}.md",1270,340),
    ]
    edges=[edge("e1","n-session","n-focus","질문을 한 흐름으로 좁힘"),edge("e2","n-focus","n-unknown","모름과 범위 확인"),edge("e3","n-unknown","n-atlas","위험·변경·추가 질문이면 확장"),edge("e4","n-atlas","n-atlas-flow","전체 단계와 근거")]
    a.output.parent.mkdir(parents=True,exist_ok=True); write_json(a.output,{"nodes":nodes,"edges":edges}); print(f"WROTE: {a.output}"); return 0
if __name__=='__main__': raise SystemExit(main())
