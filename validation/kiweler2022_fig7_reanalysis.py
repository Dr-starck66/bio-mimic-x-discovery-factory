#!/usr/bin/env python3
"""Figure 7 Kiweler et al. 2022. Never construct missing animal-level data."""
import argparse,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
from scipy import stats

DOI="10.1038/s41467-022-30363-y"
PANELS={
 "7c":{"endpoint":"primary_tumor_weight_mg","n":{"SCR":9,"MTHFD1L_KD":9},"p":0.9474},
 "7d":{"endpoint":"relative_mthfd1l_expression","n":{"SCR":7,"MTHFD1L_KD":8},"p":0.0014},
 "7e":{"endpoint":"lung_macro_metastasis_count","n":{"SCR":9,"MTHFD1L_KD":9},"p":0.0322},
 "7g":{"endpoint":"metastatic_lung_area_percent","n":{"SCR":7,"MTHFD1L_KD":9},"p":0.0189}
}
def published_binary_bounds():
    out=[]
    for free in range(5,10):
        table=[[9,0],[9-free,free]]
        out.append({"kd_without_macrometastases":free,"kd_with_macrometastases":9-free,
                    "scr_with_macrometastases":9,"scr_without_macrometastases":0,
                    "fisher_two_sided_p":float(stats.fisher_exact(table).pvalue),
                    "risk_difference_kd_minus_scr":-free/9,"table":table})
    return out

def read_animal_csv(path):
    d=defaultdict(lambda:defaultdict(list)); seen=set()
    with open(path,encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        if set(r.fieldnames or [])!={"panel","group","mouse_id","value"}:
            raise ValueError("Expected exact columns panel,group,mouse_id,value")
        for row in r:
            panel,group,mouse=row["panel"],row["group"],row["mouse_id"]
            if panel not in PANELS or group not in ("SCR","MTHFD1L_KD") or not mouse:
                raise ValueError("Invalid panel/group/mouse_id")
            key=panel,group,mouse
            if key in seen:raise ValueError("Duplicate animal")
            seen.add(key)
            value=float(row["value"])
            if not math.isfinite(value) or value<0:raise ValueError("Non-finite or negative observation")
            if panel=="7e" and not value.is_integer():raise ValueError("Count must be integer")
            if panel=="7g" and value>100:raise ValueError("Area must be <=100 percent")
            d[panel][group].append(value)
    for panel,cfg in PANELS.items():
        for group,n in cfg["n"].items():
            if len(d[panel][group])!=n:raise ValueError(f"Unexpected n: {panel} {group} {len(d[panel][group])}, expected {n}")
    if not all(v>0 for v in d["7e"]["SCR"]):raise ValueError("SCR contradiction: all 9 reported metastatic")
    if sum(v==0 for v in d["7e"]["MTHFD1L_KD"])<5:raise ValueError("KD contradiction: >50% reported metastasis-free")
    return d

def welch_from_animals(d):
    result={}
    for panel,cfg in PANELS.items():
        a=d[panel]["SCR"];b=d[panel]["MTHFD1L_KD"]
        v0=float(stats.tvar(a))/len(a);v1=float(stats.tvar(b))/len(b)
        se=math.sqrt(v0+v1)
        df=(v0+v1)**2/(v0*v0/(len(a)-1)+v1*v1/(len(b)-1)) if v0*v1>0 else None
        p=float(stats.ttest_ind(b,a,equal_var=False).pvalue)
        diff=sum(b)/len(b)-sum(a)/len(a)
        result[panel]={"endpoint":cfg["endpoint"],"n_scr":len(a),"n_kd":len(b),
          "mean_scr":sum(a)/len(a),"mean_kd":sum(b)/len(b),
          "difference_kd_minus_scr":diff,"sem_scr":float(stats.sem(a)),"sem_kd":float(stats.sem(b)),
          "welch_two_sided_p":p,"welch_df":df,
          "mean_difference_ci95":list(map(float,stats.t.interval(.95,df,loc=diff,scale=se))) if df else None,
          "published_p":cfg["p"],"four_decimal_p_match":round(p,4)==cfg["p"]}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mouse-csv",type=Path)
    p.add_argument("--source-xlsx",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if bool(a.mouse_csv)!=bool(a.source_xlsx):p.error("Both --mouse-csv and --source-xlsx required for raw-value replay")
    r={"doi":DOI,"status":"PARTIAL","mode":"published_text_bounds_only",
       "published_figure_panels":PANELS,"binary_sensitivity":published_binary_bounds(),
       "paper_welch_tests_recalculated":False,
       "negative_control":"Fig 7c p=0.9474, no significant primary tumour weight difference; not proof of equivalence",
       "warnings":["Fisher binary presence/absence is not the paper's Welch count test (Fig 7e)",
                   "All KD event-free counts 5..9 are scenarios, not claimed raw observations",
                   "Different sample n for 7b,7c,7d,7e,7g; histological exclusions need review",
                   "No clinical relevance or drug efficacy inferred"]}
    if a.mouse_csv:
        original=a.source_xlsx.read_bytes()
        if original[:4]!=b"PK\x03\x04":raise ValueError("Source is not a ZIP-based XLSX")
        d=read_animal_csv(a.mouse_csv)
        r.update({"mode":"candidate_mouse_level_replay","status":"PARTIAL",
          "source_xlsx_sha256":hashlib.sha256(original).hexdigest(),
          "mouse_csv_sha256":hashlib.sha256(a.mouse_csv.read_bytes()).hexdigest(),
          "paper_welch_tests_recalculated":True,"welch":welch_from_animals(d),
          "mapping_unverified":"Must independently match every CSV observation to author workbook cells"})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"{r['status']}: {r['mode']}")
    for row in r["binary_sensitivity"]:print(row["kd_without_macrometastases"],row["fisher_two_sided_p"])
if __name__=="__main__":main()
