"""Audit reproducible des XML NCBI BLAST HAND2. Python 3, bibliothèque standard uniquement.
Usage: python validation/hand2_blast_xml_audit.py hand2-remote-blast-evidence.zip
"""
import hashlib,json,sys,zipfile,xml.etree.ElementTree as ET

def sha(b): return hashlib.sha256(b).hexdigest()
def analyze(z,label,receipt):
    fasta=z.read(label+'.fasta')
    seq=''.join(fasta.decode().splitlines()[1:]).upper()
    assert sha(seq.encode())==receipt['sequence_sha256']
    raw=z.read(label+'.xml')
    assert sha(raw)==receipt['xml_sha256']
    root=ET.fromstring(raw)
    assert root.findtext('BlastOutput_program')=='blastn'
    it=root.find('.//Iteration')
    n=int(it.findtext('Iteration_query-len'))
    assert len(seq)==n
    hits=[]
    for h in it.findall('./Iteration_hits/Hit'):
        hsps=[{'start':int(s.findtext('Hsp_query-from')),'end':int(s.findtext('Hsp_query-to')),
               'identical':int(s.findtext('Hsp_identity')),'aligned':int(s.findtext('Hsp_align-len')),
               'bit_score':float(s.findtext('Hsp_bit-score'))}
              for s in h.findall('./Hit_hsps/Hsp')]
        hits.append({'accession':h.findtext('Hit_accession'),'hsps':hsps})
    hand2=next(h for h in hits if h['accession']=='XM_069631422')
    hand1=next(h for h in hits if h['accession']=='XM_069653976')
    ranges=sorted((min(s['start'],s['end']),max(s['start'],s['end'])) for s in hand2['hsps'])
    merged=[]
    for a,b in ranges:
        if merged and a<=merged[-1][1]+1: merged[-1][1]=max(b,merged[-1][1])
        else: merged.append([a,b])
    covered=sum(b-a+1 for a,b in merged)
    return {'database':root.findtext('BlastOutput_db'),'query_length':n,'hits':len(hits),
            'hand2_identity':sum(s['identical'] for s in hand2['hsps']),
            'hand2_aligned_columns':sum(s['aligned'] for s in hand2['hsps']),
            'hand2_covered_query_bases':covered,
            'hand2_query_coverage':covered/n,
            'hand1_top_hsp':max(hand1['hsps'],key=lambda s:s['bit_score']),
            'hit_accessions':[h['accession'] for h in hits]}
def main(path):
    with zipfile.ZipFile(path) as z:
        manifest=json.loads(z.read('manifest.json'))
        assert manifest['schema']=='BIO-MIMIC-X/HAND2-REMOTE-BLAST/1'
        out={k:analyze(z,k,v) for k,v in manifest['receipts'].items()}
    print(json.dumps({'source_zip_sha256':sha(open(path,'rb').read()),'results':out,
                      'whole_genome_uniqueness':'UNVERIFIED','curator_confirmation':'UNVERIFIED'},
                     indent=2))
if __name__=='__main__': main(sys.argv[1])
