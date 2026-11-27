#!/usr/bin/env python3
"""BIO-MIMIC X: fail-closed alpha-synuclein 7-140 sequence and source audit."""
from __future__ import annotations
import argparse,csv,hashlib,itertools,json,math,sys,zipfile
from pathlib import Path

DOI="10.1038/s41467-026-78990-z"
PRIDE="PXD083225"
UNIPROT="P37840"
SEQ=("MDVFMKGLSKAKEGVVAAAEKTKQGVAEAAGKTKEGVLYVGSKTKEGVVH"
     "GVATVAEKTKEQVTNVGGAVVTGVTAVAQKTVEGAGSIAAATGFVKKDQL"
     "GKNEEGAPQEGILEDMPVDPDNEAYEMPSEEGYQDYEPEA")
RESIDUE_MASS={"A":71.037113805,"R":156.10111105,"N":114.04292747,
"D":115.026943065,"C":103.009184505,"E":129.042593135,"Q":128.05857754,
"G":57.021463735,"H":137.058911875,"I":113.08406398,"L":113.08406398,
"K":128.09496305,"M":131.040484645,"F":147.068413945,"P":97.052763875,
"S":87.032028435,"T":101.047678505,"W":186.07931298,"Y":163.063328575,
"V":99.068413945}
FIELDS={"experiment_id","assay","sample_id","condition","value","unit"}
CONDITIONS={"intact_1_140","truncated_7_140"}

def sequence_audit():
    assert len(SEQ)==140 and SEQ[5:7]=="KG"
    mass=lambda s:round(sum(RESIDUE_MASS[a] for a in s)+18.010564684,6)
    full,fragment=mass(SEQ),mass(SEQ[6:])
    return {"status":"PASS_SEQUENCE_CHECK_ONLY",
            "sequence_sha256":hashlib.sha256(SEQ.encode("ascii")).hexdigest(),
            "uniprot":UNIPROT,"length_full":len(SEQ),"length_fragment":len(SEQ[6:]),
            "cleavage":"Lys6|Gly7","removed":SEQ[:6],
            "mass_theoretical_unmodified_Da":{"full":full,"fragment":fragment,
                                              "difference":round(full-fragment,6)},
            "warning":"Theoretical free-termini unmodified protein; not experimental MS or a treatment"}

def receipt(path,role):
    p=Path(path)
    if not p.is_file() or p.stat().st_size==0: raise ValueError("Missing or empty "+role)
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return {"role":role,"filename":p.name,"bytes":p.stat().st_size,
            "sha256":h.hexdigest(),"external_hash_verified":"UNVERIFIED"}

def paired_sign_flip(delta):
    n=len(delta)
    if n<3 or n>16:raise ValueError("Paired sample count must be 3..16")
    obs=abs(sum(delta))
    return sum(abs(sum(s*d for s,d in zip(signs,delta)))>=obs-1e-10
               for signs in itertools.product((-1,1),repeat=n))/(2**n)

def parse_paired_csv(path):
    groups={}
    with Path(path).open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not FIELDS.issubset(reader.fieldnames):
            raise ValueError("Missing required CSV columns")
        for line,row in enumerate(reader,2):
            if any(not row.get(k) or not row[k].strip() for k in FIELDS):
                raise ValueError("Missing input field line "+str(line))
            if row["condition"] not in CONDITIONS:raise ValueError("Unapproved condition")
            try:value=float(row["value"])
            except ValueError as ex:raise ValueError("Non numeric measure") from ex
            if not math.isfinite(value):raise ValueError("Nonfinite measure")
            group=(row["experiment_id"],row["assay"],row["unit"])
            sample=(row["sample_id"],row["condition"])
            b=groups.setdefault(group,{})
            if sample in b:raise ValueError("Duplicate biological sample")
            b[sample]=value
    if not groups:raise ValueError("Empty experiment")
    result=[]
    for (experiment,assay,unit),samples in sorted(groups.items()):
        ids=sorted({i for i,_ in samples})
        if any((i,c) not in samples for i in ids for c in CONDITIONS):
            raise ValueError("Unmatched sample pairing")
        delta=[samples[(i,"truncated_7_140")]-samples[(i,"intact_1_140")] for i in ids]
        result.append({"experiment":experiment,"assay":assay,"unit":unit,
                       "pairs":len(ids),"mean_delta":sum(delta)/len(delta),
                       "p_two_sided_exact_sign_flip":paired_sign_flip(delta),
                       "status":"PARTIAL_EXPLORATORY_ONLY",
                       "pairing_validation":"UNVERIFIED",
                       "multiple_testing_correction":"UNVERIFIED"})
    return result

def run(source_data=None,pride_files=(),measurements=None):
    out={"doi":DOI,"dataset":PRIDE,"sequence":sequence_audit(),"files":[],
         "exploratory_stats":[],"published_curve_reproduced":"UNVERIFIED",
         "pride_raw_spectra_reanalysed":"UNVERIFIED",
         "clinical_effect":"UNVERIFIED","status":"PARTIAL"}
    if source_data:
        p=Path(source_data)
        if p.suffix.lower()!=".xlsx" or not zipfile.is_zipfile(p):
            raise ValueError("Invalid source XLSX")
        with zipfile.ZipFile(p) as z:
            if "xl/workbook.xml" not in z.namelist():
                raise ValueError("Not a spreadsheet workbook")
        out["files"].append(receipt(source_data,"nature_source_data"))
    for p in pride_files:out["files"].append(receipt(p,"pride_file"))
    if measurements:
        out["files"].append(receipt(measurements,"explicitly_mapped_csv"))
        out["exploratory_stats"]=parse_paired_csv(measurements)
    out["missing"]=[key for present,key in
                    ((source_data,"original_nature_xlsx"),
                     (pride_files,"real_pride_spectra"),
                     (measurements,"author_measurement_mapping")) if not present]
    return out

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-data-xlsx")
    p.add_argument("--pride-file",action="append",default=[])
    p.add_argument("--mapped-csv")
    p.add_argument("--output")
    p.add_argument("--require-experimental-data",action="store_true")
    a=p.parse_args(argv)
    try:result=run(a.source_data_xlsx,a.pride_file,a.mapped_csv)
    except (ValueError,OSError,zipfile.BadZipFile) as ex:
        print(json.dumps({"status":"FAIL_INVALID_INPUT","error":str(ex)}),file=sys.stderr)
        return 2
    result_json=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    if a.output:
        path=Path(a.output);path.parent.mkdir(exist_ok=True,parents=True)
        path.write_text(result_json,encoding="utf-8")
    print(result_json)
    return 2 if a.require_experimental_data else 0

if __name__=="__main__":raise SystemExit(main())
