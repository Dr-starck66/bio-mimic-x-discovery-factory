import json,tempfile,pathlib
import statsmodels.api as sm
from external_challenge import *
d=sm.datasets.grunfeld.load_pandas().data
# Fixed by dataset ordering before scores; entire firm held out.
groups=list(d.firm.unique());task={};labels=[]
for name,gs in [('train',groups[:7]),('validation',groups[7:9]),('test',groups[9:])]:
    z=d[d.firm.isin(gs)];task[name]={'X':z[['value','capital']].to_numpy().tolist(),'groups':z.firm.tolist()}
    if name=='test':labels=z.invest.tolist()
    else:task[name]['y']=z.invest.tolist()
with tempfile.TemporaryDirectory() as t:
    root=pathlib.Path(t);pub=root/'public';priv=root/'private';auth=prepare(task,labels,priv,pub);pre=read(pub/'prereg.json');s=submit(task,pre,auth['pin'],auth['prereg_sha256']);r=judge(task,pre,s,auth['pin'],auth['prereg_sha256'],priv);result=verify_receipt(r,pre,s,auth['pin'],auth['prereg_sha256']);write('demo_public.json',{'task':task,'prereg':pre,'submission':s,'receipt':r,'authentication':auth});print(json.dumps({'result':result,'groups':{k:sorted(set(v['groups'])) for k,v in task.items()},'methods':{k:v['method'] for k,v in s['predictions'].items()}},indent=2))
