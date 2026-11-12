#!/usr/bin/env python3
"""Trace original Kiweler 2022 Fig 7 cell values; stdlib ZIP/XML, pinned SHA-256."""
import argparse,csv,hashlib,json,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
SOURCE_SHA256="ac6f8f8d08055d82838601a1cdef66b5e464c9e392d3b09b85acbfbbcb762a81"
MAIN="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG="{http://schemas.openxmlformats.org/package/2006/relationships}"
SHEETS={"7c":("Figure 7C",3,11,9,9),"7d":("Figure 7D",4,12,7,8),
        "7e":("Figure 7E",4,12,9,9),"7g":("Figure 7G",4,12,7,9)}

def extract(path):
    sha=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if sha!=SOURCE_SHA256:raise ValueError(f"Different source version; fail closed: {sha}")
    data=[];trace=[]
    with zipfile.ZipFile(path) as z:
        rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid_to_target={x.get("Id"):x.get("Target").lstrip("/") for x in rels.findall(PKG+"Relationship")}
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        name_to_target={s.get("name"):rid_to_target[s.get(REL+"id")]
            for s in wb.findall(".//"+MAIN+"sheet")}
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            strings=ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared=["".join(t.text or "" for t in si.iter(MAIN+"t")) for si in strings.findall(MAIN+"si")]
        for panel,(name,first,last,scr_n,kd_n) in SHEETS.items():
            target=name_to_target.get(name)
            if not target:raise ValueError(f"Missing sheet {name}")
            if not target.startswith("xl/"):target="xl/"+target
            root=ET.fromstring(z.read(target));cells={}
            for c in root.iter(MAIN+"c"):
                v=c.find(MAIN+"v")
                if v is None:continue
                raw=v.text or ""
                if c.get("t")=="s":raw=shared[int(raw)]
                cells[c.get("r")]=raw
            for row in range(first,last+1):
                mid=str(row-first+1)
                for group,col in [("SCR","C"),("MTHFD1L_KD","D")]:
                    addr=f"{col}{row}"
                    if addr not in cells:raise ValueError(f"Missing cell {name}!{addr}")
                    raw=cells[addr];excluded="*" in raw
                    reason=("Supplement Fig 7D exclusion" if panel=="7d" else
                            "Collapsed lung excluded") if excluded else ""
                    if excluded:val=None
                    else:
                        val=float(raw)
                        if val<0:raise ValueError(f"Negative observation {name}!{addr}")
                        data.append({"panel":panel,"group":group,"mouse_id":mid,"value":val})
                    trace.append({"panel":panel,"group":group,"mouse_id":mid,
                        "source_cell":f"'{name}'!{addr}","source_raw":raw,
                        "status":"EXCLUDED" if excluded else "INCLUDED",
                        "value":val,"exclusion_reason":reason})
            for group,expected in [("SCR",scr_n),("MTHFD1L_KD",kd_n)]:
                actual=sum(x["panel"]==panel and x["group"]==group for x in data)
                if actual!=expected:raise ValueError(f"Wrong n {panel} {group}: {actual}/{expected}")
    if not any(x["panel"]=="7e" and x["value"]%1 for x in data):
        raise ValueError("No fractional 7E values: source mapping suspicious")
    return data,trace,sha

def write_csv(path,rows,fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-xlsx",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    data,trace,sha=extract(a.source_xlsx)
    write_csv(a.out_dir/"fig7_mouse_level.csv",data,["panel","group","mouse_id","value"])
    write_csv(a.out_dir/"fig7_cell_lineage.csv",trace,
              ["panel","group","mouse_id","source_cell","source_raw","status","value","exclusion_reason"])
    print(json.dumps({"status":"PASS","source_sha256":sha,"n_included":len(data),
        "n_excluded":sum(x["status"]=="EXCLUDED" for x in trace),
        "fractional_counts":sum(x["panel"]=="7e" and x["value"]%1 for x in data)}))
if __name__=="__main__":main()
