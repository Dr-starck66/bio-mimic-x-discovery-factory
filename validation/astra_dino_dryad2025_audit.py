#!/usr/bin/env python3
"""Read-only Dryad 2025 finch crosswalk and ALX1/HMGA2 VCF scanner.

Standard library only. No imputation, no inferred VCF calls, no biological claims.
Reference intervals must be pinned to the very same assembly as the VCF header.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ASSEMBLY = "GCA_902806625.1"  # Rubin 2022 / Lifjeld 2025 study reference
REQUIRED_TRAITS = ("Beak_length", "Beak_height", "Beak_width")
PROVENANCE = {
    "doi": "10.5061/dryad.3ffbg79w8",
    "dataset": "Weak sperm differentiation in Darwin's finches (2025)",
    "reference": ASSEMBLY,
    "morphometrics": "Morphometrics.txt",
    "pca": "pPCAeigen.txt",
    "vcf": "Prun64_3miss2mafNoZ_1.vcf.gz",
    "accession_rule": "Only new 50 sequenced samples: first 6 digits of PCA SampleID refer to Oslo museum AccNo; the remaining 14 downloaded SRA samples must not be implicitly crosswalked",
}

class EvidenceError(ValueError):
    pass

def sha256_file(path, chunk_size=2**20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(chunk_size):
            h.update(block)
    return h.hexdigest()

def rows_from_text(path):
    """Read published tab/comma delimited records; hard fail on duplicate columns."""
    text = Path(path).read_text(encoding="utf-8-sig")
    clean = [x for x in text.splitlines() if x.strip() and not x.lstrip().startswith('#')]
    if not clean:
        raise EvidenceError("EMPTY_TABLE")
    sample = '\n'.join(clean[:5])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters='\t,;')
        records = list(csv.DictReader(io.StringIO('\n'.join(clean)), dialect=dialect))
    except csv.Error as e:
        raise EvidenceError(f"TABLE_FORMAT: {e}") from e
    header = list(records[0].keys()) if records else clean[0].split('\t')
    if any(k is None for k in header) or len(set(header)) != len(header):
        raise EvidenceError("DUPLICATE_COLUMNS")
    if not records:
        raise EvidenceError("NO_TABLE_ROWS")
    if any(None in row or any(v is None for v in row.values()) for row in records):
        raise EvidenceError("MALFORMED_ROWS")
    return records

def phenotypes(path):
    rows = rows_from_text(path)
    needed = {'AccNo', *REQUIRED_TRAITS}
    if not needed.issubset(rows[0]):
        raise EvidenceError('MORPH_HEADER_MISSING:' + ','.join(sorted(needed-set(rows[0]))))
    mapping = {}
    rejected = 0
    for row in rows:
        acc = row['AccNo'].strip()
        if not re.fullmatch(r'\d{6}', acc):
            rejected += 1
            continue
        if acc in mapping:
            raise EvidenceError('DUPLICATE_MORPH_ACC:' + acc)
        vals={}
        try:
            for trait in REQUIRED_TRAITS:
                vals[trait] = float(row[trait])
                if not (0 < vals[trait] < 1000):
                    raise ValueError('implausible measurement')
        except (TypeError, ValueError):
            rejected+=1
            continue
        mapping[acc] = {'AccNo':acc, 'traits':vals, 'species':row.get('Species','').strip(), 'island':row.get('Island','').strip()}
    return mapping, {'raw_rows':len(rows),'valid_six_digit_unique':len(mapping),'rejected_rows':rejected}

def pca_samples(path):
    rows = rows_from_text(path)
    if 'SampleID' not in rows[0]:
        raise EvidenceError('PCA_SAMPLEID_MISSING')
    ids = {}
    for row in rows:
        sample = row['SampleID'].strip()
        if not sample or sample in ids:
            raise EvidenceError('DUPLICATE_OR_EMPTY_PCA_SAMPLE')
        ids[sample] = row
    return ids

def read_vcf(path, regions=None, expected_assembly=ASSEMBLY):
    """Streaming gz/plain VCF. Never call coverage zero if assembly/contig not validated."""
    open_func = gzip.open if str(path).endswith('.gz') else open
    regions = regions or []
    with open_func(path, 'rt', encoding='utf-8') as vcf:
        header = []
        samples = None
        assembly = None
        contig_names = set()
        for line in vcf:
            if line.startswith('##'):
                header.append(line.rstrip())
                if line.startswith('##reference='):
                    assembly = line.strip().split('=',1)[1]
                if line.startswith('##contig='):
                    m = re.search(r'ID=([^,>]+)',line)
                    if m: contig_names.add(m.group(1))
                continue
            if line.startswith('#CHROM\t'):
                fields=line.rstrip('\n').split('\t')
                if len(fields)<10 or fields[8] != 'FORMAT':
                    raise EvidenceError('VCF_HEADER_INVALID')
                samples=fields[9:]
                if len(set(samples)) != len(samples):
                    raise EvidenceError('DUPLICATE_VCF_SAMPLES')
                break
            raise EvidenceError('VCF_MISSING_HEADER')
        if samples is None:
            raise EvidenceError('VCF_HEADER_NOT_FOUND')
        # Actual VCF assembly provenance must be established before scanning intervals.
        verified = assembly is not None and expected_assembly in assembly
        if regions:
            if not verified:
                return {'status':'UNVERIFIED_ASSEMBLY','reported_reference':assembly,
                        'samples':samples,'number_samples':len(samples),
                        'variants_by_gene':None,'variants_by_region':None,
                        'reason':'VCF ##reference does not explicitly identify the pinned assembly; cannot infer target-locus SNP counts'}
            if not contig_names:
                return {'status':'UNVERIFIED_CONTIG_DICTIONARY','reported_reference':assembly,
                        'samples':samples,'number_samples':len(samples),
                        'variants_by_gene':None,'variants_by_region':None,
                        'reason':'VCF missing ##contig metadata; cannot verify region names'}
            for r in regions:
                if r['assembly'] != expected_assembly:
                    raise EvidenceError('INTERVAL_ASSEMBLY_MISMATCH')
                if contig_names and r['contig'] not in contig_names:
                    return {'status':'UNVERIFIED_CONTIG','reported_reference':assembly,
                            'number_samples':len(samples), 'samples':samples,
                            'variants_by_gene':None,'variants_by_region':None,
                            'reason':f"Interval contig {r['contig']} absent from declared VCF contigs"}
        totals = Counter()
        observed = 0
        called_by_gene = defaultdict(lambda: Counter())
        for line in vcf:
            if not line.strip() or line.startswith('#'):
                continue
            cols=line.rstrip('\n').split('\t')
            if len(cols)<9+len(samples):
                raise EvidenceError('TRUNCATED_VCF_RECORD')
            chrom=cols[0]
            try: pos=int(cols[1])
            except ValueError: raise EvidenceError('INVALID_VCF_POSITION')
            observed+=1
            for region in regions:
                if chrom!=region['contig'] or not region['start']<=pos<=region['end']:
                    continue
                # Only true biallelic single-nucleotide variants; report skipped separately.
                key=region['gene']
                if len(cols[3])!=1 or len(cols[4])!=1 or cols[3] not in 'ACGT' or cols[4] not in 'ACGT':
                    totals[key+'_NON_SNV']+=1
                    continue
                totals[key]+=1
                gtkeys=cols[8].split(':')
                if 'GT' not in gtkeys:
                    called_by_gene[key]['no_GT_records']+=1
                    continue
                gi=gtkeys.index('GT')
                for sample,val in zip(samples,cols[9:]):
                    components=val.split(':')
                    gt=components[gi] if len(components)>gi else '.'
                    if gt in ('.','./.','.|.') or '.' in re.split(r'[|/]',gt):
                        called_by_gene[key]['missing_genotypes']+=1
                    elif all(x in ('0','1') for x in re.split(r'[|/]',gt)):
                        called_by_gene[key]['called_genotypes']+=1
                    else:
                        called_by_gene[key]['other_genotypes']+=1
        return {'status':'SCANNED_HEADER_AND_INTERVALS_NOT_INDEPENDENTLY_REVIEWED' if regions else 'HEADER_ONLY_NO_INTERVALS',
                'reported_reference':assembly,'number_samples':len(samples),'samples':samples,
                'observed_vcf_records':observed,
                'variants_by_gene':dict(totals) if regions else None,
                'genotype_calls_by_gene':{k:dict(v) for k,v in called_by_gene.items()} if regions else None}

def read_regions(path, assembly=ASSEMBLY):
    obj=json.loads(Path(path).read_text('utf8'))
    if obj.get('assembly') != assembly or obj.get('coordinate_system') != '1-based-closed':
        raise EvidenceError('REGIONS_ASSEMBLY_OR_COORDINATES_NOT_PINNED')
    rs=obj.get('regions',[])
    if not rs or not {x.get('gene') for x in rs}.issubset({'ALX1','HMGA2'}):
        raise EvidenceError('REGIONS_MISSING_OR_UNKNOWN_GENES')
    if not {'ALX1','HMGA2'}.issubset({x['gene'] for x in rs}):
        raise EvidenceError('BOTH_TARGET_LOCI_REQUIRED')
    for r in rs:
        if not re.fullmatch(r'[\w.\-]+',r.get('contig','')):
            raise EvidenceError('INVALID_CONTIG')
        if not isinstance(r.get('start'),int) or not isinstance(r.get('end'),int) or r['start']<1 or r['end']<r['start']:
            raise EvidenceError('INVALID_INTERVAL')
        if not r.get('source') or not r.get('assembly')==assembly:
            raise EvidenceError('UNSOURCED_INTERVAL')
    return rs

def join_samples(morph, pca, vcf_samples):
    # The first six digits are only a *candidate* for the 50 newly sequenced birds,
    # never an authoritative match without explicit provenance of new sequencing.
    matches=[]; absent=[]; ambiguous=[]
    for sample in vcf_samples:
        if sample not in pca:
            absent.append(sample);continue
        idmatch = re.match(r'^(\d{6})(.*)$',sample)
        if not idmatch:
            ambiguous.append({'SampleID':sample,'reason':'not a six-digit prefix'});continue
        acc,suffix=idmatch.groups()
        if not suffix or acc not in morph:
            ambiguous.append({'SampleID':sample,'AccNo_candidate':acc,'reason':'no explicit suffix or no phenotype'});continue
        row=morph[acc]
        matches.append({'SampleID':sample, 'AccNo_candidate':acc,
                        'status':'CANDIDATE_DATASET_RULE_NOT_INDEPENDENTLY_VALIDATED',
                        'phenotype':row})
    duplicated=[acc for acc,count in Counter(x['AccNo_candidate'] for x in matches).items() if count>1]
    if duplicated:
        raise EvidenceError('NON_UNIQUE_SAMPLE_TO_BIRD:' + ','.join(duplicated))
    return {'vcf_samples':len(vcf_samples),'pca_samples':len(pca),'candidate_pairs':len(matches),
            'independently_verified_pairs':0,'samples_not_in_pca':absent,
            'ambiguous_samples':ambiguous,'candidate_records':matches,
            'reason':'PCA prefix convention is limited to the first 50 newly sequenced birds; independent SRA or repository metadata must distinguish these from 14 reused samples'}

def audit(morph, pca, vcf, intervals=None):
    measurements,mstats=phenotypes(morph)
    samples=pca_samples(pca)
    targets=read_regions(intervals) if intervals else None
    v=read_vcf(vcf, targets)
    linked=join_samples(measurements,samples,v['samples'])
    return {'status':'PARTIAL' if v['status']!='SCANNED_HEADER_AND_INTERVALS_NOT_INDEPENDENTLY_REVIEWED' or not linked['independently_verified_pairs'] else 'PASS',
            'sources':PROVENANCE,'file_hashes':{Path(p).name:sha256_file(p) for p in [morph,pca,vcf]+([intervals] if intervals else [])},
            'morphology':mstats,'pca_entries':len(samples),'crosswalk':linked,'variants':v,
            'caveat':'Any SNP count needs pinned assembly-matched target intervals, not inferred gene names; genetic association or predictive value is not established by this scan'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--morph',required=True)
    parser.add_argument('--pca',required=True)
    parser.add_argument('--vcf',required=True)
    parser.add_argument('--intervals',help='Pinned JSON with BOTH ALX1 and HMGA2 intervals on exact GCA_902806625.1 assembly')
    parser.add_argument('--output')
    args=parser.parse_args()
    try:
        report=audit(args.morph,args.pca,args.vcf,args.intervals)
    except (OSError,ValueError,gzip.BadGzipFile) as exc:
        print(json.dumps({'status':'FAIL_CLOSED','error':str(exc)}))
        raise SystemExit(2) from exc
    result=json.dumps(report,indent=2,ensure_ascii=False)
    if args.output:Path(args.output).write_text(result+'\n',encoding='utf8')
    print(result)

if __name__=='__main__':main()
