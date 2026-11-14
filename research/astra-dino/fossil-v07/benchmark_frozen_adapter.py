#!/usr/bin/env python3
"""ASTRA DINO: out-of-taxon fossil character benchmark on the 6 original Hendrickx NEXUS trees.
Run: python benchmark.py --nexus <authentic> --output evidence.json
No dependency beyond Biopython; the six topologies are never fitted to hidden labels here.
"""
import argparse, collections, hashlib, io, json, math, random, re
from pathlib import Path
from Bio import Phylo

STATES = tuple('0123456')

NCHAR = 457
TREE_SOURCES = (
 ("ML_unconstrained.zip", "ML_unconstrained/baron_unconstrained.treefile"),
 ("Tree_comparisons.zip","Tree_comparisons/BEA/baron_saurischia.treefile"),
 ("Tree_comparisons.zip","Tree_comparisons/BEA/baron_ornithischiformes.treefile"),
 ("Tree_comparisons.zip","Tree_comparisons/BEA/comparison.treefile"),
)
def parse_nexus(path):
    import zipfile
    text=Path(path).read_text(encoding="utf-8-sig")
    block=re.search(r"(?is)\bBEGIN\s+DATA\s*;(.*?)\bEND\s*;",text)
    if not block: raise ValueError("DATA block missing")
    mm=re.search(r"(?is)\bMATRIX\b(.*?);",block.group(1))
    if not mm: raise ValueError("MATRIX missing")
    rows={}
    for line in mm.group(1).splitlines():
        m=re.match(r"^\s*(\S+)\s+(.+)$",line)
        if not m: continue
        name,bases=m.groups()
        tok=re.findall(r"\([^)]*\)|\{[^}]*\}|[0-6?\-]", bases)
        if len(tok)!=NCHAR: raise ValueError(f"Invalid {name}: {len(tok)} != {NCHAR}")
        if name in rows: raise ValueError("Duplicate taxon")
        rows[name]=tok
    trees=[]
    for zipname,entry in TREE_SOURCES:
        with zipfile.ZipFile(Path(path).parent / zipname) as archive:
            tree=Phylo.read(io.StringIO(archive.read(entry).decode("utf8")),"newick")
        taxa=[tip.name for tip in tree.get_terminals()]
        if len(taxa)!=len(rows) or set(taxa)!=set(rows): raise ValueError("Tree taxa mismatch "+entry)
        trees.append(tree)
    if len(rows)!=74 or len(trees)!=4: raise ValueError("Unexpected source matrix")
    return rows, trees, text

def distances(tree):
    # Unit edges, since original trees are topological, without credible branch lengths.
    graph=collections.defaultdict(list)
    for parent in tree.find_clades():
        for child in parent.clades:
            graph[parent].append(child);graph[child].append(parent)
    result={}
    for tip in tree.get_terminals():
        q=collections.deque([(tip,0)]);seen={tip}; lengths={}
        while q:
            node,d=q.popleft()
            if node.is_terminal():lengths[node.name]=d
            for child in graph[node]:
                if child not in seen:seen.add(child);q.append((child,d+1))
        result[tip.name]=lengths
    return result

def predictions(rows,tree):
    # Sankoff/Fitch style unit-change-cost parsimony, using the outside-subtree
    # message for each leaf: its own state NEVER participates in its prediction.
    # Compute all 71 characters and 61 tips in a single post/pre order traversal.
    inf=10**8; tips=tree.get_terminals(); nodes=list(tree.find_clades(order='preorder'))
    post=list(tree.find_clades(order='postorder'))
    all_preds={name:[] for name in rows}
    for k in range(NCHAR):
        down={}
        for n in post:
            if n.is_terminal():
                x=rows[n.name][k]
                allowed=(set(re.findall(r'[0-6]',x)) if x not in '?-' else set(STATES))
                down[n]=[0 if s in allowed else inf for s in STATES]
            else:
                down[n]=[sum(min(down[c][j]+int(s!=STATES[j]) for j in range(len(STATES))) for c in n.clades) for s in STATES]
        out={tree.root:[0]*len(STATES)}
        for n in nodes:
            if n not in out:raise AssertionError('Tree order issue')
            for child in n.clades:
                sibs=[c for c in n.clades if c is not child]
                out[child]=[
                    min(out[n][i]+int(STATES[i]!=state)+sum(min(down[sibling][j]+int(STATES[i]!=STATES[j]) for j in range(len(STATES))) for sibling in sibs) for i in range(len(STATES)))
                    for state in STATES]
        for tip in tips:
            val=out[tip];lo=min(val);poss=[STATES[i] for i,x in enumerate(val) if x==lo]
            all_preds[tip.name].append(poss[0] if len(poss)==1 else None)
    return all_preds

def mode(values):
    ct=collections.Counter(values)
    return sorted(ct,key=lambda s:(-ct[s],s))[0] if ct else None

def trait_score(rows,dist,idx,excluded=None,permutation_seed=None):
    # If permutation_seed provided, permute training states per character only.
    taxa=list(rows);result={t:[] for t in taxa}
    for k in range(NCHAR):
        known={t:rows[t][k] for t in taxa if rows[t][k] in STATES}
        for target in taxa:
            donor_states={t:v for t,v in known.items() if t!=target}
            if permutation_seed is not None:
                sorted_taxa=sorted(donor_states)
                shuffled=[donor_states[t] for t in sorted_taxa]
                random.Random(permutation_seed+10007*k+5003*taxa.index(target)).shuffle(shuffled)
                donor_states=dict(zip(sorted_taxa,shuffled))
            scores=collections.defaultdict(float)
            for donor,state in donor_states.items():
                d=dist[target][donor]
                scores[state]+=1/(max(1,d)**2)
            result[target].append(max(STATES,key=lambda s:(scores[s],-ord(s))) if scores else None)
    return result

def nearest_predictions(rows,dist):
    taxa=list(rows); result={t:[] for t in taxa}
    for target in taxa:
        for k in range(NCHAR):
            donors=[d for d in taxa if d != target and rows[d][k] in STATES]
            if not donors:
                result[target].append(None);continue
            minimum=min(dist[target][d] for d in donors)
            result[target].append(mode(rows[d][k] for d in donors if dist[target][d] == minimum))
    return result

def assess(rows, trees, n_perm=0):
    taxa=list(rows);n=len(taxa)
    truth=[(t,k,rows[t][k]) for t in taxa for k in range(NCHAR) if rows[t][k] in STATES]
    major={}
    for t in taxa:
        for k in range(NCHAR):
            major[t,k]=mode(rows[d][k] for d in taxa if d!=t and rows[d][k] in STATES)
    per_tree=[];tree_preds=[]
    for i,tree in enumerate(trees):
        d=distances(tree)
        sank=predictions(rows,tree)
        weight=trait_score(rows,d,None)
        near=nearest_predictions(rows,d)
        tree_preds.append((sank,weight,d,near))
        per_tree.append({'tree':i+1,'fitch':evaluate(truth,lambda t,k:sank[t][k]),'weighted':evaluate(truth,lambda t,k:weight[t][k]),'nearest':evaluate(truth,lambda t,k:near[t][k]),'fitch_fallback':evaluate(truth,lambda t,k:sank[t][k] if sank[t][k] is not None else major[t,k])})
    ensemble={}
    for t in taxa:
        for k in range(NCHAR):
            ensemble[t,k]=mode([w[t][k] for _,w,_,_ in tree_preds if w[t][k] is not None])
    nearest_ensemble={(t,k):mode([n[t][k] for _,_,_,n in tree_preds if n[t][k] is not None]) for t in taxa for k in range(NCHAR)}
    fitch_ensemble={(t,k):mode([f[t][k] for f,_,_,_ in tree_preds if f[t][k] is not None]) for t in taxa for k in range(NCHAR)}
    models={'majority':lambda t,k:major[t,k],'astra_topology_ensemble':lambda t,k:ensemble[t,k],'nearest_ensemble':lambda t,k:nearest_ensemble[t,k], 'fitch_ensemble_fallback':lambda t,k:fitch_ensemble[t,k] if fitch_ensemble[t,k] is not None else major[t,k]}
    for i,(f,w,_,n) in enumerate(tree_preds):
        models[f'fitch_tree_{i+1}']=lambda t,k,p=f:p[t][k]
        models[f'fitch_tree_{i+1}_fallback']=lambda t,k,p=f:p[t][k] if p[t][k] is not None else major[t,k]
    evaluations={key:evaluate(truth,pred) for key,pred in models.items()}
    # Paired group bootstrap, macro across known-taxa not raw number of observations.
    pairs={t:[(int(models['astra_topology_ensemble'](t,k)==v),int(models['majority'](t,k)==v)) for tt,k,v in truth if tt==t] for t in taxa}
    observed=sum(sum(a-b for a,b in pairs[t])/len(pairs[t]) for t in taxa if pairs[t])/sum(bool(pairs[t]) for t in taxa)
    boot=[];rng=random.Random(20261114)
    eligible=[t for t in taxa if pairs[t]]
    for _ in range(2000):
        sample=[eligible[rng.randrange(len(eligible))] for _ in eligible]
        boot.append(sum(sum(a-b for a,b in pairs[t])/len(pairs[t]) for t in sample)/len(sample))
    boot.sort()
    permutations=[]
    if n_perm:
        for seed in range(n_perm):
            # permute donor labels in one predetermined tree, no tuning or best-tree selection.
            fake=trait_score(rows,tree_preds[0][2],None,permutation_seed=1000+seed)
            permutations.append(evaluate(truth,lambda t,k:fake[t][k])['micro_accuracy'])
    return {'matrix':{'taxa':len(taxa),'characters':NCHAR,'unambiguous_states':len(truth),'missing':sum(rows[t][k]=='?' for t in taxa for k in range(NCHAR)), 'inapplicable':sum(rows[t][k]=='-' for t in taxa for k in range(NCHAR)),'ambiguous':sum(rows[t][k] not in STATES and rows[t][k] not in '?-' for t in taxa for k in range(NCHAR)), 'class_counts':dict(collections.Counter(v for _,_,v in truth))},'per_tree':per_tree,'evaluation':evaluations,'bootstrap':{'astro_minus_majority_macro':observed,'ci95':[boot[50],boot[1949]],'n_taxa':len(eligible)},'permutation_negative_tree1':{'n':n_perm,'accuracy_list':permutations},'method':'leave-one-whole-taxon-out all 457 characters; four fixed published topologies; no tuning on hidden labels; unit-edge distance-2 weighting and majority ensemble; missing/inapplicable/ambiguous excluded from scoring'}

def evaluate(truth,pred):
    c=0;cov=0;by=collections.defaultdict(lambda:[0,0,0]);class_by=collections.defaultdict(lambda:[0,0])
    for t,k,v in truth:
        ans=pred(t,k);ok=ans==v
        c+=int(ok);cov+=int(ans is not None)
        by[t][0]+=int(ok);by[t][1]+=1;by[t][2]+=int(ans is not None)
        class_by[v][0]+=int(ok);class_by[v][1]+=1
    return {'n':len(truth),'correct':c,'covered':cov,'micro_accuracy':round(c/len(truth),6),'coverage':round(cov/len(truth),6),'accuracy_given_prediction':round(c/cov,6) if cov else None,'macro_taxon_accuracy':round(sum(x[0]/x[1] for x in by.values())/len(by),6),'classes':{s: {'correct':x[0],'n':x[1]} for s,x in class_by.items()},'per_taxon':{t:dict(correct=x[0],n=x[1],covered=x[2]) for t,x in by.items()}}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--nexus',required=True);p.add_argument('--output',required=True);p.add_argument('--permutations',type=int,default=20);a=p.parse_args()
    rows,trees,text=parse_nexus(a.nexus)
    result=assess(rows,trees,a.permutations)
    result['source_sha256']=hashlib.sha256(Path(a.nexus).read_bytes()).hexdigest()
    Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    for key,m in result['evaluation'].items():print(key,m['n'],m['correct'],m['covered'],m['micro_accuracy'],m['macro_taxon_accuracy'])
    print('bootstrap',result['bootstrap'])
    print('per_tree',[(x['tree'],x['fitch']['correct'],x['weighted']['correct']) for x in result['per_tree']])
    print('negative',result['permutation_negative_tree1'])