#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path


def validate(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors=[]; warnings=[]
    if data.get("type") != "excalidraw": errors.append("root type must be excalidraw")
    bg=(data.get("appState") or {}).get("viewBackgroundColor")
    if bg not in {"#fcfcfb", "#ffffff"}: warnings.append(f"unexpected canvas background: {bg}")
    elements=[e for e in data.get("elements",[]) if isinstance(e,dict) and not e.get("isDeleted")]
    saturated_area=0.0; shape_area=0.0
    texts=[]
    for e in elements:
        t=e.get("type")
        if float(e.get("roughness",0) or 0) != 0: errors.append(f"{e.get('id')}: roughness must be 0")
        if t in {"arrow","line"} and float(e.get("strokeWidth",1) or 1) > 2: warnings.append(f"{e.get('id')}: heavy edge stroke")
        if t=="text":
            text=str(e.get("text", "")); texts.append(text)
            if int(e.get("fontSize",16) or 16) < 9: errors.append(f"{e.get('id')}: text below 9px")
        if t in {"rectangle","ellipse","diamond"}:
            area=abs(float(e.get("width",0))*float(e.get("height",0))); shape_area+=area
            fill=str(e.get("backgroundColor","transparent")).lower()
            if fill not in {"transparent","#ffffff","#fcfcfb","#f7f8fa","#f9fafb","#eff6ff","#ecfdf5","#f5f3ff","#f0f9ff","#f0fdf4","#fef2f2","#fff7e6","#fff1e8","#f1f5f9"}:
                saturated_area+=area
    if shape_area and saturated_area/shape_area > .22: warnings.append("saturated fill area exceeds 22% of shape area")
    raw="\n".join(texts)
    if re.search(r"\[\[[^\]]+[/\\][^\]]+\]\]", raw): errors.append("raw Obsidian path is visible in scene text")
    if re.search(r"[\U0001F300-\U0001FAFF]", raw): warnings.append("emoji found; prefer native vector icon")
    return {"ok":not errors,"errors":errors,"warnings":warnings,"counts":{"elements":len(elements),"texts":len(texts)}}


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("input"); p.add_argument("--strict",action="store_true"); p.add_argument("--report")
    a=p.parse_args(); path=Path(a.input)
    files=sorted(path.rglob("*.excalidraw")) if path.is_dir() else [path]
    reports={str(f):validate(f) for f in files}
    ok=all(r["ok"] and (not a.strict or not r["warnings"]) for r in reports.values())
    result={"ok":ok,"files":reports}
    if a.report: Path(a.report).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
