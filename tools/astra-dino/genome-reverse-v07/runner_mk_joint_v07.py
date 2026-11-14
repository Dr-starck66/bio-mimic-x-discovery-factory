import pathlib,re,math,collections,hashlib,json,random,functools
D=pathlib.Path('/tmp/astra_v07')
def parse(source):
 b=(D/(source+'.nex')).read_bytes();s=b.decode('utf-8-sig')
 n=int(re.search(r'(?i)nchar\s*=\s*(\d+)',s)[1]);nt=int(re.search(r'(?i)ntax\s*=\s*(\d+)',s)[1])
 m=re.search(r'(?ims)^\s*MATRIX\s*\n(.*?);',s)[1];rows={}
 for l in m.strip().splitlines():
  l=l.strip()
  if not l:continue
  if l[0]=="'":name,_,seq=l[1:].partition("'")
  else:name,seq=re.match(r'(\S+)\s+(.+)',l).groups()
  a=re.findall(r'\([^)]*\)|\{[^}]*\}|[0-9?\-]',seq)
  assert len(a)==n,(name,len(a),n)
  rows[name]=a
 assert len(rows)==nt
 trees=[]
 if source=='hendrickx':
  for match in re.finditer(r'(?im)^\s*TREE\s+[^=]+?=\s*(\([^;]*\))\s*;',s):
   tok=re.findall(r'\(|\)|,|:[0-9.eE+\-]+|\d+',re.sub(r'\[[^\]]*\]','',match[1]));p=[0]
   def sub():
    t=tok[p[0]];p[0]+=1
    if t=='(':
     v=[sub()]
     while tok[p[0]]==',':p[0]+=1;v.append(sub())
     assert tok[p[0]]==')';p[0]+=1;z=tuple(v)
    else:z=int(t)-1
    if p[0]<len(tok) and tok[p[0]].startswith(':'):p[0]+=1
    return z
   trees.append(sub())
  assert len(trees)==6
 else:trees=[tuple(range(nt))]
 return list(rows),list(rows.values()),trees,hashlib.sha256(b).hexdigest()
@functools.lru_cache(maxsize=100)
def obs(v):
 if v in ('?','-'):return None
 a=set(re.findall('[0-9]',v));return a if a else None
def norm(x):
 s=sum(x);return [z/s for z in x] if s else [1/len(x)]*len(x)
def build(t):
 nodes=[];leaves={}
 def f(x):
  if isinstance(x,int):
   i=len(nodes);nodes.append(((),x));leaves[x]=i;return i
  ch=tuple(f(y) for y in x);i=len(nodes);nodes.append((ch,None));return i
 rt=f(t);return nodes,rt,leaves
def mk(t,A,j,states):
 nodes,root,leaves=t;k=len(states);e=math.exp(-k*.25/(k-1))
 P=[[1/k+(1-1/k)*e if x==y else (1-e)/k for y in range(k)] for x in range(k)]
 up=[None]*len(nodes);msg=[None]*len(nodes)
 for i,(ch,tip) in enumerate(nodes):
  if tip is not None:
   z=obs(A[tip][j]);up[i]=norm([float(z is None or state in z) for state in states])
  else:
   v=[1.]*k
   for c in ch:
    mc=[sum(P[a][b]*up[c][b] for b in range(k)) for a in range(k)]
    msg[c]=mc;v=[x*y for x,y in zip(v,mc)]
   up[i]=norm(v)
 down=[None]*len(nodes);down[root]=[1/k]*k
 for i in reversed(range(len(nodes))):
  ch,_=nodes[i]
  for c in ch:
   v=down[i][:]
   for other in ch:
    if c!=other:v=[x*y for x,y in zip(v,msg[other])]
   down[c]=norm([sum(v[a]*P[a][b] for a in range(k)) for b in range(k)])
 return {tip:down[i] for tip,i in leaves.items()}
_near_cache={}
def joint(A,target,j,mk0,states,negative=False):
 key=(id(A),target,negative)
 if key not in _near_cache:
  known={}
  for z in range(0,len(A[0]),5):
   row=(target+7+11*z)%len(A) if negative else target
   if negative and row==target:row=(row+1)%len(A)
   v=obs(A[row][z])
   if v and len(v)==1:known[z]=next(iter(v))
  neighbors=[]
  if len(known)>=3:
   for i,row in enumerate(A):
    if i==target:continue
    shared=[z for z in known if obs(row[z]) and len(obs(row[z]))==1]
    if len(shared)<3:continue
    errors=sum(next(iter(obs(row[z])))!=known[z] for z in shared)
    w=math.exp(-5*errors/len(shared))*math.sqrt(len(shared)/len(known))
    neighbors.append((w,i))
   neighbors.sort(key=lambda x:(-x[0],x[1]))
  _near_cache[key]=neighbors[:12]
 neighbors=_near_cache[key]
 if not neighbors:return mk0
 q=[.5]*len(states)
 for w,i in neighbors:
  v=obs(A[i][j])
  if v and len(v)==1:
   v=next(iter(v))
   if v in states:q[states.index(v)]+=w
 q=norm(q)
 return norm([.65*x+.35*y for x,y in zip(mk0,q)])

def stats(items,key):
 n=len(items);good=0;ll=0;brier=0
 for target,j,truth,base,mk0,jointp,neg in items:
  p=[base,mk0,jointp,neg][key]
  good+=int(max(range(len(p)),key=lambda c:p[c])==truth)
  ll-=math.log(max(1e-12,p[truth]))
  brier+=sum((p[c]-(c==truth))**2 for c in range(len(p)))
 return {'n':n,'correct':good,'accuracy':good/n,'log_loss':ll/n,'brier':brier/n}
def score(src):
 taxa,A,trees,sha=parse(src);states=list('0123' if src=='hendrickx' else '01234')
 targets=[i for i,row in enumerate(A) if sum(len(x)==1 and x in states for x in row)>=10]
 allstats=[];items_primary=[]
 for tidx,tree in enumerate(trees):
  tree=build(tree);items=[]
  for j in range(len(A[0])):
   if j%5==0:continue
   post=mk(tree,A,j,states)
   for i in targets:
    y=A[i][j]
    if y not in states:continue
    c=collections.Counter(next(iter(obs(A[h][j]))) for h in range(len(A)) if h!=i and obs(A[h][j]) and len(obs(A[h][j]))==1)
    base=norm([c.get(x,0)+.5 for x in states]);m=post[i]
    items.append((i,j,states.index(y),base,m,joint(A,i,j,m,states),joint(A,i,j,m,states,True)))
  methods={name:stats(items,k) for k,name in enumerate(['majority','mk','joint','shuffled_anchor'])}
  allstats.append({'tree':tidx+1,'methods':methods})
  if tidx==0:items_primary=items
 rng=random.Random(20261114);by={}
 for i in targets:
  oo=[o for o in items_primary if o[0]==i]
  if not oo:continue
  n=len(oo);gains={}
  for method in ('accuracy','log_loss','brier'):
   x=stats(oo,1);y=stats(oo,2)
   gains[method]=(y[method]-x[method]) if method=='accuracy' else (x[method]-y[method])
  by[i]=(n,gains)
 intervals={};valid=list(by)
 for method in ('accuracy','log_loss','brier'):
  diffs=[]
  for _ in range(500):
   sample=[rng.choice(valid) for _ in valid]
   denom=sum(by[i][0] for i in sample)
   diffs.append(sum(by[i][0]*by[i][1][method] for i in sample)/denom)
  diffs.sort();intervals[method]=[diffs[12],diffs[487]]
 return {'dataset':src,'sha256':sha,'taxa':len(taxa),'characters':len(A[0]),'n_holdout_taxa':len(targets),'n_outcomes':len(items_primary),
  'tree_source':'six published topologies, possible historic topology leakage' if src=='hendrickx' else 'unresolved star topology, no published tree in Gist',
  'hyperparameters':{'mk_rate':.25,'lambda':.35,'anchor_rule':'j%5=0','neighbors':12,'minimum_shared_anchors':3},
  'first_tree':allstats[0], 'all_trees':allstats,'cluster_bootstrap_95':intervals}
results={'schema':'astra.dino.joint-mk.v07','datasets':[score('hendrickx'),score('baron_josephwb_edited')]}
(D/'evidence_joint_mk_v07.json').write_text(json.dumps(results,indent=2))
for s in results['datasets']:
 print(json.dumps({k:v for k,v in s.items() if k!='all_trees'}))
 if len(s['all_trees'])>1:print('TOP',json.dumps([{'t':v['tree'],'mk':v['methods']['mk']['accuracy'],'joint':v['methods']['joint']['accuracy']} for v in s['all_trees']]))
