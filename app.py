import os, json, gzip, base64, secrets, urllib.request, urllib.parse
from datetime import datetime
from collections import defaultdict
from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'ekart-dashboard-secret-key-2024-fixed'

OWNER_PASSWORD = os.environ.get('OWNER_PASSWORD', 'ekart2024')
GITHUB_TOKEN   = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO    = os.environ.get('GITHUB_REPO', 'ruchikapal-afk/Elixir-Dashboard')
GITHUB_FILE    = 'data/dashboard_data.b64'

def pct(n,d): return round(n/d*100,1) if d else 0

def agg(rows):
    t=r6=r24=d0=d1=0
    for r in rows:
        t+=r['total'];r6+=r['r6'];r24+=r['r24'];d0+=r['d0'];d1+=r['d1']
    return {'t':t,'r6p':pct(r6,t),'r24p':pct(r24,t),'d0p':pct(d0,t),'d1p':pct(d1,t)}

def build_agg(records):
    DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    by_date=defaultdict(list);by_week=defaultdict(list);by_month=defaultdict(list)
    by_ht_d=defaultdict(lambda:defaultdict(list));by_ht_w=defaultdict(lambda:defaultdict(list));by_ht_m=defaultdict(lambda:defaultdict(list))
    by_gm_d=defaultdict(lambda:defaultdict(list));by_gm_w=defaultdict(lambda:defaultdict(list));by_gm_m=defaultdict(lambda:defaultdict(list))
    by_rm_d=defaultdict(lambda:defaultdict(list));by_rm_w=defaultdict(lambda:defaultdict(list));by_rm_m=defaultdict(lambda:defaultdict(list))
    by_am_d=defaultdict(lambda:defaultdict(list));by_am_w=defaultdict(lambda:defaultdict(list));by_am_m=defaultdict(lambda:defaultdict(list))
    by_hub=defaultdict(list);by_hw=defaultdict(lambda:defaultdict(list));by_hm=defaultdict(lambda:defaultdict(list))
    by_dow=defaultdict(lambda:defaultdict(list));by_dg=defaultdict(lambda:defaultdict(lambda:defaultdict(list)))
    by_dr=defaultdict(lambda:defaultdict(lambda:defaultdict(list)));by_da=defaultdict(lambda:defaultdict(lambda:defaultdict(list)))
    hier={};hm={}
    for r in records:
        dt=r['date'];wk=r['week'];mo=r['month'];g=r['gm'];rm=r['rm'];am=r['am'];ht=r['hub_type'];hub=r['hub']
        dow=datetime.strptime(dt,'%Y-%m-%d').strftime('%A')
        by_date[dt].append(r);by_week[wk].append(r);by_month[mo].append(r)
        by_ht_d[ht][dt].append(r);by_ht_w[ht][wk].append(r);by_ht_m[ht][mo].append(r)
        by_gm_d[g][dt].append(r);by_gm_w[g][wk].append(r);by_gm_m[g][mo].append(r)
        by_rm_d[rm][dt].append(r);by_rm_w[rm][wk].append(r);by_rm_m[rm][mo].append(r)
        by_am_d[am][dt].append(r);by_am_w[am][wk].append(r);by_am_m[am][mo].append(r)
        by_hub[hub].append(r);by_hw[hub][wk].append(r);by_hm[hub][mo].append(r)
        by_dow[dow][dt].append(r);by_dg[g][dow][dt].append(r);by_dr[rm][dow][dt].append(r);by_da[am][dow][dt].append(r)
        if hub not in hm:hm[hub]={'gm':g,'rm':rm,'am':am,'ht':ht}
        if g not in hier:hier[g]={}
        if rm not in hier[g]:hier[g][rm]={}
        if am not in hier[g][rm]:hier[g][rm][am]=set()
        hier[g][rm][am].add(hub)
    for g in hier:
        for r in hier[g]:
            for a in hier[g][r]:hier[g][r][a]=sorted(hier[g][r][a])
    return {
        'dates':sorted(by_date),'weeks':sorted(by_week,key=lambda x:int(x.split()[-1])),
        'months':sorted(by_month),'hub_types':sorted(by_ht_d),'gms':sorted(by_gm_d),
        'rms':sorted(by_rm_d),'ams':sorted(by_am_d),'days':DAYS,'hierarchy':hier,'hub_meta':hm,
        'date_agg':{d:agg(v) for d,v in sorted(by_date.items())},
        'week_agg':{w:agg(v) for w,v in by_week.items()},
        'month_agg':{m:agg(v) for m,v in by_month.items()},
        'ht_date':{h:{d:agg(v) for d,v in dv.items()} for h,dv in by_ht_d.items()},
        'ht_week':{h:{w:agg(v) for w,v in wv.items()} for h,wv in by_ht_w.items()},
        'ht_month':{h:{m:agg(v) for m,v in mv.items()} for h,mv in by_ht_m.items()},
        'gm_date':{g:{d:agg(v) for d,v in dv.items()} for g,dv in by_gm_d.items()},
        'gm_week':{g:{w:agg(v) for w,v in wv.items()} for g,wv in by_gm_w.items()},
        'gm_month':{g:{m:agg(v) for m,v in mv.items()} for g,mv in by_gm_m.items()},
        'rm_date':{r:{d:agg(v) for d,v in dv.items()} for r,dv in by_rm_d.items()},
        'rm_week':{r:{w:agg(v) for w,v in wv.items()} for r,wv in by_rm_w.items()},
        'rm_month':{r:{m:agg(v) for m,v in mv.items()} for r,mv in by_rm_m.items()},
        'am_date':{a:{d:agg(v) for d,v in dv.items()} for a,dv in by_am_d.items()},
        'am_week':{a:{w:agg(v) for w,v in wv.items()} for a,wv in by_am_w.items()},
        'am_month':{a:{m:agg(v) for m,v in mv.items()} for a,mv in by_am_m.items()},
        'hub_agg':{h:agg(v) for h,v in by_hub.items()},
        'hub_week':{h:{w:agg(v) for w,v in wv.items()} for h,wv in by_hw.items()},
        'hub_month':{h:{m:agg(v) for m,v in mv.items()} for h,mv in by_hm.items()},
        'dow_overall':{d:{dt:agg(r) for dt,r in dv.items()} for d,dv in by_dow.items()},
        'dow_gm':{g:{d:{dt:agg(r) for dt,r in ddv.items()} for d,ddv in dv.items()} for g,dv in by_dg.items()},
        'dow_rm':{r:{d:{dt:agg(rows) for dt,rows in ddv.items()} for d,ddv in dv.items()} for r,dv in by_dr.items()},
        'dow_am':{a:{d:{dt:agg(r) for dt,r in ddv.items()} for d,ddv in dv.items()} for a,dv in by_da.items()},
    }

def gh_get():
    """Get data from GitHub"""
    try:
        url = f'https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GITHUB_FILE}?t={datetime.now().timestamp()}'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()
    except: return None

def gh_put(b64_data, updated_at):
    """Save data to GitHub via API"""
    if not GITHUB_TOKEN: return False
    try:
        # Get current file SHA
        api_url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}'
        req = urllib.request.Request(api_url, headers={
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        })
        sha = None
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                sha = json.loads(r.read())['sha']
        except: pass
        
        # Prepare content
        content = base64.b64encode(b64_data.encode()).decode()
        payload = {'message': f'Update dashboard data {updated_at}', 'content': content}
        if sha: payload['sha'] = sha
        
        req2 = urllib.request.Request(api_url, 
            data=json.dumps(payload).encode(),
            headers={'Authorization': f'token {GITHUB_TOKEN}','Content-Type':'application/json','Accept':'application/vnd.github.v3+json'},
            method='PUT')
        with urllib.request.urlopen(req2, timeout=30) as r:
            return r.status in [200,201]
    except Exception as e:
        print(f'GitHub save error: {e}')
        return False

def gWk(dt):
    d=datetime.strptime(dt,'%Y-%m-%d');j=datetime(d.year,1,1)
    return 'Week '+str(((d-j).days+j.weekday()+1)//7+1)

def gMo(dt):
    d=datetime.strptime(dt,'%Y-%m-%d')
    return d.strftime("%b'%y")

@app.route('/')
def index():
    for path in ['index.html','templates/index.html']:
        if os.path.exists(path):
            with open(path,encoding='utf-8') as f: content=f.read()
            return content, 200, {'Content-Type':'text/html; charset=utf-8'}
    return "Upload index.html to repo root", 404

@app.route('/api/data')
def api_data():
    b64 = gh_get()
    if not b64: return jsonify({'error':'No data uploaded yet'}),404
    # Parse updated_at from first line if stored
    lines = b64.strip().split('\n',1)
    updated_at = None
    if lines[0].startswith('UPDATED:'):
        updated_at = lines[0][8:]
        b64 = lines[1] if len(lines)>1 else ''
    return jsonify({'data':b64,'updated_at':updated_at})

@app.route('/api/login',methods=['POST'])
def login():
    pwd=request.json.get('password','')
    if pwd==OWNER_PASSWORD:
        session['owner']=True
        return jsonify({'ok':True})
    return jsonify({'ok':False,'error':'Wrong password'}),401

@app.route('/api/logout',methods=['POST'])
def logout():
    session.pop('owner',None)
    return jsonify({'ok':True})

@app.route('/api/upload',methods=['POST'])
def upload():
    pwd=(request.form.get('owner_pwd','') or request.headers.get('X-Owner-Key','') or
         (session.get('owner') and OWNER_PASSWORD) or '')
    if pwd!=OWNER_PASSWORD and not session.get('owner'):
        return jsonify({'error':'Unauthorized'}),403
    import openpyxl
    f=request.files.get('file')
    if not f: return jsonify({'error':'No file'}),400
    wb=openpyxl.load_workbook(f,data_only=True)
    ws=wb.active
    headers=[str(c.value or '').strip() for c in next(ws.iter_rows(min_row=1,max_row=1))]
    REQ=['Date','Hub Name','Hub Type','GM','RM','AM','Total Tickets','Response < 6 Hrs','Response < 24 hrs','Closed By D0','Closed by D1']
    missing=[c for c in REQ if c not in headers]
    if missing: return jsonify({'error':'Missing: '+', '.join(missing)}),400
    hi={h:i for i,h in enumerate(headers)}
    new_recs=[]
    for row in ws.iter_rows(min_row=2,values_only=True):
        if not row[hi['Date']]: continue
        dt=row[hi['Date']]
        if isinstance(dt,datetime): dt=dt.strftime('%Y-%m-%d')
        else: dt=str(dt).split('T')[0].split(' ')[0]
        wk=str(row[hi.get('Week',-1)] or gWk(dt))
        mo=str(row[hi.get('Month',-1)] or gMo(dt))
        new_recs.append({'date':dt,'week':wk,'month':mo,'gm':str(row[hi['GM']] or ''),
            'rm':str(row[hi['RM']] or ''),'am':str(row[hi['AM']] or ''),
            'hub_type':str(row[hi['Hub Type']] or ''),'hub':str(row[hi['Hub Name']] or ''),
            'total':int(row[hi['Total Tickets']] or 0),'r6':int(row[hi['Response < 6 Hrs']] or 0),
            'r24':int(row[hi['Response < 24 hrs']] or 0),'d0':int(row[hi['Closed By D0']] or 0),
            'd1':int(row[hi['Closed by D1']] or 0)})
    
    # Get existing data from GitHub
    existing_b64 = gh_get()
    existing_recs = []
    if existing_b64:
        lines = existing_b64.strip().split('\n',1)
        data_b64 = lines[1] if lines[0].startswith('UPDATED:') and len(lines)>1 else existing_b64
        try:
            bin_data=base64.b64decode(data_b64)
            j=gzip.decompress(bin_data).decode()
            D=json.loads(j)
            # Reconstruct records from aggregations not needed - just store new records
        except: pass
    
    # Build new aggregation
    D = build_agg(new_recs)
    j = json.dumps(D, separators=(',',':'))
    c = gzip.compress(j.encode(), compresslevel=9)
    b64 = base64.b64encode(c).decode()
    
    updated_at = datetime.now().strftime('%d %b %Y, %I:%M %p')
    storage_content = f'UPDATED:{updated_at}\n{b64}'
    
    # Save to GitHub
    saved = gh_put(storage_content, updated_at)
    
    return jsonify({
        'ok': True,
        'rows_uploaded': len(new_recs),
        'updated_at': updated_at,
        'github_saved': saved,
        'message': 'Saved to GitHub - will persist after restart!' if saved else 'Saved in memory only - add GITHUB_TOKEN env var for persistence'
    })

if __name__=='__main__':
    app.run(debug=False,host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
