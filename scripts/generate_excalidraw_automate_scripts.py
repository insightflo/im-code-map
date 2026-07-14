#!/usr/bin/env python3
"""Generate Obsidian ExcalidrawAutomate scripts from visual-model v5.

The raw `.excalidraw` generator is deterministic and canonical. These scripts
provide an editable, in-vault regeneration path and a live-embeddable master map.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from im_code_map_common import clamp_text, slugify, wrap_text

SEMANTIC_COLORS = {
    "actor": ("#175CD3", "#EFF8FF"), "start": ("#4F46E5", "#EEF2FF"),
    "process": ("#4F46E5", "#FFFFFF"), "decision": ("#D97706", "#FFFAEB"),
    "state-change": ("#7F56D9", "#F4F3FF"), "event": ("#0E7490", "#ECFDFF"),
    "wait": ("#7F56D9", "#F4F3FF"), "data": ("#175CD3", "#EFF8FF"),
    "storage": ("#175CD3", "#EFF8FF"), "external": ("#C11574", "#FDF2FA"),
    "error": ("#D92D20", "#FEF3F2"), "risk": ("#D92D20", "#FEF3F2"),
    "compensation": ("#C11574", "#FDF2FA"), "end": ("#15803D", "#ECFDF3"),
    "domain": ("#4F46E5", "#EEF2FF"), "codebase": ("#101828", "#F2F4F7"),
    "note": ("#15803D", "#ECFDF3"), "test": ("#15803D", "#ECFDF3"),
}

LANE_BADGE = {"actor":"ACT", "system":"SYS", "domain":"DOM", "state-machine":"STATE", "context":"RULE"}


def js(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def layout(diagram: dict[str, Any]) -> dict[str, dict[str, float]]:
    cfg = diagram["layout"]
    w = float(cfg.get("node_width", 250)); h = float(cfg.get("node_height", 120))
    hgap = float(cfg.get("horizontal_gap", 90)); vgap = float(cfg.get("vertical_gap", 80))
    lane_h = max(h + vgap, 210); lane_header = 230
    lanes = sorted(diagram.get("lanes", []), key=lambda x: (x.get("order", 0), x["id"]))
    lane_idx = {lane["id"]: i for i, lane in enumerate(lanes)}
    frames = sorted(diagram.get("frames", []), key=lambda x: (x.get("order", 0), x["id"]))
    nodes_by_frame: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for n in diagram.get("nodes", []): nodes_by_frame[n["frame"]].append(n)
    pos: dict[str, dict[str, float]] = {}
    y_cursor = 200
    for frame in frames:
        nodes = nodes_by_frame[frame["id"]]
        orders = {v:i for i,v in enumerate(sorted({float(n.get("order",0)) for n in nodes}))}
        used_lanes = [l["id"] for l in lanes if any(n.get("lane")==l["id"] for n in nodes)]
        local_lane = {lid:i for i,lid in enumerate(used_lanes)}
        for n in nodes:
            x = 300 + orders[float(n.get("order",0))]*(w+hgap)
            y = y_cursor + 100 + local_lane.get(n.get("lane"), lane_idx.get(n.get("lane"),0))*lane_h
            pos[n["id"]] = {"x":x,"y":y,"w":float(n.get("width",w)),"h":float(n.get("height",h)),"frameY":y_cursor}
        y_cursor += 170 + max(1,len(used_lanes))*lane_h + 120
    return pos


def diagram_script(diagram: dict[str, Any], output_folder: str) -> str:
    positions = layout(diagram)
    node_data = []
    for n in diagram.get("nodes", []):
        stroke, bg = SEMANTIC_COLORS.get(n["kind"], ("#495057","#f8f9fa"))
        shape = n.get("shape") or ("diamond" if n["kind"]=="decision" else "ellipse" if n["kind"] in {"start","end"} else "rectangle")
        label_parts=[n.get("label",n["id"])]
        if n.get("state_before") or n.get("state_after"): label_parts.append(f"{n.get('state_before','?')} → {n.get('state_after','?')}")
        if n.get("summary"): label_parts.append(clamp_text(n["summary"],28,180))
        if n.get("confidence")!="VERIFIED": label_parts.append(n.get("confidence","UNVERIFIED"))
        node_data.append({**n,"stroke":stroke,"background":bg,"shape":shape,"text":wrap_text("\n".join(label_parts),28,7),**positions[n["id"]]})
    edge_data=[]
    edge_colors={"happy-path":"#2b8a3e","conditional":"#e67700","async-event":"#0b7285","retry":"#5f3dc4","error":"#c92a2a","timeout":"#c92a2a","compensation":"#a61e4d","cancel":"#c92a2a","data":"#1864ab","reference":"#868e96","dependency":"#495057","ownership":"#364fc7"}
    for e in diagram.get("edges",[]):
        parts=[e.get("label","")]
        if e.get("condition") and e.get("condition")!=e.get("label"): parts.append(e["condition"])
        if e.get("confidence")!="VERIFIED": parts.append(e.get("confidence","UNVERIFIED"))
        edge_data.append({**e,"color":edge_colors.get(e.get("kind"),"#495057"),"text":"\n".join(p for p in parts if p)})
    lanes=[{**lane, "badge": LANE_BADGE.get(lane.get("kind"), "LANE")} for lane in sorted(diagram.get("lanes",[]),key=lambda x:(x.get("order",0),x["id"]))]
    frames=sorted(diagram.get("frames",[]),key=lambda x:(x.get("order",0),x["id"]))
    icon_helper = 'function addSemanticIcon(kind,x,y,stroke) {\n  const ids = [];\n  ea.style.strokeColor = stroke;\n  ea.style.backgroundColor = "transparent";\n  ea.style.strokeWidth = 2;\n  const line = pts => { ids.push(ea.addLine(pts)); };\n  const rect = (ix,iy,w,h) => { ids.push(ea.addRect(ix,iy,w,h)); };\n  const ellipse = (ix,iy,w,h) => { ids.push(ea.addEllipse(ix,iy,w,h)); };\n  const bx=x, by=y, cx=x+12, cy=y+13;\n  if (kind === "start") line([[bx+3,by+1],[bx+3,by+25],[bx+23,by+13],[bx+3,by+1]]);\n  else if (kind === "end") line([[bx+1,by+14],[bx+9,by+23],[bx+24,by+3]]);\n  else if (kind === "decision") line([[cx,by+1],[bx+23,cy],[cx,by+25],[bx+1,cy],[cx,by+1]]);\n  else if (kind === "state-change") { line([[bx+1,by+7],[bx+22,by+7]]); line([[bx+23,by+20],[bx+2,by+20]]); }\n  else if (kind === "event") line([[bx+14,by],[bx+5,by+14],[bx+13,by+14],[bx+8,by+27],[bx+22,by+10],[bx+14,by+10]]);\n  else if (kind === "external") { ellipse(bx+1,by+1,24,24); line([[bx+2,cy],[bx+24,cy]]); line([[cx,by+2],[cx-5,cy],[cx,by+24],[cx+5,cy],[cx,by+2]]); }\n  else if (kind === "storage") { ellipse(bx+1,by+1,23,7); rect(bx+1,by+4,23,18); ellipse(bx+1,by+18,23,7); }\n  else if (kind === "data") { rect(bx+1,by+2,23,5); rect(bx+1,by+10,23,5); rect(bx+1,by+18,23,5); }\n  else if (kind === "domain") { rect(bx+1,by+1,9,9); rect(bx+15,by+1,9,9); rect(bx+1,by+15,9,9); rect(bx+15,by+15,9,9); }\n  else if (kind === "error" || kind === "risk") { line([[cx,by+1],[bx+24,by+25],[bx,by+25],[cx,by+1]]); line([[cx,by+8],[cx,by+17]]); ellipse(cx-1.5,by+20,3,3); }\n  else if (kind === "compensation") line([[bx+23,by+6],[bx+8,by+6],[bx+3,by+12],[bx+8,by+18],[bx+19,by+18]]);\n  else { ellipse(cx-5,cy-5,10,10); line([[bx+1,cy],[bx+23,cy]]); line([[cx,by+1],[cx,by+25]]); }\n  return ids;\n}'
    code=f'''/* Generated by im-code-map v5.1. Source: {diagram['id']} */
const DIAGRAM = {js(diagram['id'])};
const OUTPUT_FOLDER = {js(output_folder)};
const nodes = {js(node_data)};
const edges = {js(edge_data)};
const lanes = {js(lanes)};
const frames = {js(frames)};

ea.reset();
ea.setTheme(0);
ea.setFontFamily(2);
ea.canvas.viewBackgroundColor = "#F7F8FC";
ea.style.fillStyle = "solid";
ea.style.roughness = 0;
ea.style.strokeWidth = 2;

ea.style.strokeColor = "#101828";
ea.style.fontSize = 30;
ea.addText(40, 30, {js(diagram['title'])}, {{width: 1500, height: 60, textAlign: "left", textVerticalAlign: "middle"}});
ea.style.fontSize = 16;
ea.style.strokeColor = "#667085";
ea.addText(40, 95, {js(diagram.get('purpose',''))}, {{wrapAt: 95, width: 1500, height: 70, textAlign: "left", textVerticalAlign: "top"}});

// Lane guides. They are routing context, not a replacement for the stream itself.
for (const node of nodes) {{
  // create one lane band per frame/lane combination at first occurrence
  const key = `${{node.frame}}::${{node.lane}}`;
  if (!globalThis.__imCodeMapLanes) globalThis.__imCodeMapLanes = new Set();
  if (globalThis.__imCodeMapLanes.has(key)) continue;
  globalThis.__imCodeMapLanes.add(key);
  const siblings = nodes.filter(n => n.frame === node.frame && n.lane === node.lane);
  const minX = 40;
  const maxX = Math.max(...siblings.map(n => n.x+n.w), 1200) + 70;
  const y = Math.min(...siblings.map(n => n.y)) - 40;
  ea.style.strokeColor = "#D0D5DD";
  ea.style.backgroundColor = "#F2F4F7";
  ea.style.opacity = 70;
  ea.style.strokeWidth = 1;
  ea.addRect(minX, y, maxX-minX, Math.max(...siblings.map(n=>n.h))+80);
  ea.style.opacity = 100;
  ea.style.strokeColor = "#667085";
  ea.style.fontSize = 16;
  const lane = lanes.find(l => l.id === node.lane);
  ea.addText(55, y+20, lane ? `[${{lane.badge}}] ${{lane.label}}` : node.lane, {{width: 210, height: 60, textAlign:"left", textVerticalAlign:"middle"}});
}}

{icon_helper}

const nodeIds = {{}};
for (const node of nodes) {{
  ea.style.strokeColor = node.stroke;
  ea.style.backgroundColor = node.background;
  ea.style.strokeWidth = ["decision","error","compensation"].includes(node.kind) ? 3 : 2;
  let id;
  if (node.shape === "diamond") id = ea.addDiamond(node.x,node.y,node.w,node.h);
  else if (node.shape === "ellipse") id = ea.addEllipse(node.x,node.y,node.w,node.h);
  else id = ea.addRect(node.x,node.y,node.w,node.h);
  nodeIds[node.id] = id;
  if (node.details_link) ea.getElement(id).link = node.details_link;
  const iconIds = addSemanticIcon(node.kind,node.x+13,node.y+11,node.stroke);
  ea.style.strokeColor = "#1e1e1e";
  ea.style.fontSize = 16;
  const tid = ea.addText(node.x+18,node.y+12,node.text,{{wrapAt:28,width:node.w-36,height:node.h-24,textAlign:"center",textVerticalAlign:"middle"}});
  if (node.details_link) ea.getElement(tid).link = node.details_link;
  ea.addToGroup([id,...iconIds,tid]);
}}

for (const edge of edges) {{
  if (!nodeIds[edge.from] || !nodeIds[edge.to]) continue;
  ea.style.strokeColor = edge.color;
  ea.style.strokeWidth = ["error","compensation"].includes(edge.kind) ? 3 : 2;
  ea.style.strokeStyle = ["async-event","retry","reference"].includes(edge.kind) ? "dashed" : "solid";
  const aid = ea.connectObjects(nodeIds[edge.from],null,nodeIds[edge.to],null,{{numberOfPoints:0,startArrowHead:null,endArrowHead:"arrow",padding:6}});
  if (edge.text) ea.addLabelToLine(aid,edge.text);
}}

delete globalThis.__imCodeMapLanes;
await ea.create({{filename: DIAGRAM, foldername: OUTPUT_FOLDER, onNewPane: true}});
'''
    return code


def embeddable_script(composition: dict[str, Any], vault_folder: str) -> str:
    placements=[]
    for p in composition.get("placements",[]):
        placements.append({**p,"path":f"{vault_folder.rstrip('/')}/{p['diagram_id']}.excalidraw"})
    return f'''/* Generated by im-code-map v5.1. Live child-file composition. */
const OUTPUT_FOLDER = {js(vault_folder)};
const placements = {js(placements)};
ea.reset();
ea.setTheme(0);
ea.setFontFamily(2);
ea.canvas.viewBackgroundColor = "#F7F8FC";
ea.style.strokeColor = "#101828";
ea.style.fontSize = 32;
ea.addText(40,30,{js(composition['title'])},{{width:1800,height:70,textAlign:"left",textVerticalAlign:"middle"}});
for (const p of placements) {{
  const file = app.vault.getAbstractFileByPath(p.path);
  if (!file) throw new Error(`Missing child Excalidraw file: ${{p.path}}`);
  const width = Math.max(900, 1800*p.scale);
  const height = Math.max(600, 1100*p.scale);
  ea.style.strokeColor = "#343a40";
  ea.style.fontSize = 22;
  ea.addText(p.x+40,p.y+105,p.title,{{width:width,height:42,textAlign:"left",textVerticalAlign:"middle"}});
  ea.addEmbeddable(p.x+40,p.y+160,width,height,undefined,file);
}}
await ea.create({{filename:{js(composition['id'])},foldername:OUTPUT_FOLDER,onNewPane:true}});
'''


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_model",type=Path)
    parser.add_argument("output_dir",type=Path,nargs="?",default=None)
    parser.add_argument("--vault-folder",default="architecture/excalidraw")
    args=parser.parse_args()
    model=json.loads(args.visual_model.read_text(encoding="utf-8"))
    out=args.output_dir or args.visual_model.parent/"excalidraw-automate"
    out.mkdir(parents=True,exist_ok=True)
    for diagram in model.get("diagrams",[]):
        if "excalidraw-automate" not in diagram.get("format_targets",[]): continue
        path=out/f"generate-{slugify(diagram['id'])}.js"
        path.write_text(diagram_script(diagram,args.vault_folder),encoding="utf-8")
        print(f"WROTE {path}")
    for composition in model.get("compositions",[]):
        if composition.get("mode")!="obsidian-embeddable": continue
        path=out/f"generate-{slugify(composition['id'])}.js"
        path.write_text(embeddable_script(composition,args.vault_folder),encoding="utf-8")
        print(f"WROTE {path}")
    return 0

if __name__=="__main__": raise SystemExit(main())
