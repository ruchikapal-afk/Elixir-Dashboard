import os, json, gzip, base64, hashlib, secrets
from datetime import datetime
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, abort, session

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ── CONFIG ──────────────────────────────────────────────────────────────────
OWNER_PASSWORD = os.environ.get('OWNER_PASSWORD', 'ekart2024')  # set in Render env vars
DATA_FILE      = 'data/hub_data.json'
AGG_FILE       = 'data/agg_data.json.gz'

# ── HELPERS ─────────────────────────────────────────────────────────────────
def pct(n, d): return round(n/d*100, 1) if d else 0

def agg(rows):
    t=r6=r24=d0=d1=0
    for r in rows:
        t+=r['total']; r6+=r['r6']; r24+=r['r24']; d0+=r['d0']; d1+=r['d1']
    return {'t':t,'r6p':pct(r6,t),'r24p':pct(r24,t),'d0p':pct(d0,t),'d1p':pct(d1,t),
            '_r6':r6,'_r24':r24,'_d0':d0,'_d1':d1}

def build_agg(records):
    DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    by_date=defaultdict(list); by_week=defaultdict(list); by_month=defaultdict(list)
    by_ht_date=defaultdict(lambda:defaultdict(list))
    by_ht_week=defaultdict(lambda:defaultdict(list))
    by_ht_month=defaultdict(lambda:defaultdict(list))
    by_gm_date=defaultdict(lambda:defaultdict(list))
    by_gm_week=defaultdict(lambda:defaultdict(list))
    by_gm_month=defaultdict(lambda:defaultdict(list))
    by_rm_date=defaultdict(lambda:defaultdict(list))
    by_rm_week=defaultdict(lambda:defaultdict(list))
    by_rm_month=defaultdict(lambda:defaultdict(list))
    by_am_date=defaultdict(lambda:defaultdict(list))
    by_am_week=defaultdict(lambda:defaultdict(list))
    by_am_month=defaultdict(lambda:defaultdict(list))
    by_hub=defaultdict(list)
    by_hub_week=defaultdict(lambda:defaultdict(list))
    by_hub_month=defaultdict(lambda:defaultdict(list))
    by_dow_overall=defaultdict(lambda:defaultdict(list))
    by_dow_gm=defaultdict(lambda:defaultdict(lambda:defaultdict(list)))
    by_dow_rm=defaultdict(lambda:defaultdict(lambda:defaultdict(list)))
    by_dow_am=defaultdict(lambda:defaultdict(lambda:defaultdict(list)))
    hierarchy={}; hub_meta={}

    for r in records:
        dt=r['date']; wk=r['week']; mo=r['month']
        g=r['gm']; rm2=r['rm']; am2=r['am']; ht=r['hub_type']; hub=r['hub']
        dow=datetime.strptime(dt,'%Y-%m-%d').strftime('%A')
        by_date[dt].append(r); by_week[wk].append(r); by_month[mo].append(r)
        by_ht_date[ht][dt].append(r); by_ht_week[ht][wk].append(r); by_ht_month[ht][mo].append(r)
        by_gm_date[g][dt].append(r); by_gm_week[g][wk].append(r); by_gm_month[g][mo].append(r)
        by_rm_date[rm2][dt].append(r); by_rm_week[rm2][wk].append(r); by_rm_month[rm2][mo].append(r)
        by_am_date[am2][dt].append(r); by_am_week[am2][wk].append(r); by_am_month[am2][mo].append(r)
        by_hub[hub].append(r); by_hub_week[hub][wk].append(r); by_hub_month[hub][mo].append(r)
        by_dow_overall[dow][dt].append(r)
        by_dow_gm[g][dow][dt].append(r)
        by_dow_rm[rm2][dow][dt].append(r)
        by_dow_am[am2][dow][dt].append(r)
        if hub not in hub_meta: hub_meta[hub]={'gm':g,'rm':rm2,'am':am2,'ht':ht}
        if g not in hierarchy: hierarchy[g]={}
        if rm2 not in hierarchy[g]: hierarchy[g][rm2]={}
        if am2 not in hierarchy[g][rm2]: hierarchy[g][rm2][am2]=set()
        hierarchy[g][rm2][am2].add(hub)

    for g in hierarchy:
        for r in hierarchy[g]:
            for a in hierarchy[g][r]:
                hierarchy[g][r][a]=sorted(hierarchy[g][r][a])

    all_dates=sorted(by_date)
    all_weeks=sorted(by_week,key=lambda x:int(x.split()[-1]))
    all_months=sorted(by_month)

    return {
        'dates':all_dates,'weeks':all_weeks,'months':all_months,
        'hub_types':sorted(by_ht_date),'gms':sorted(by_gm_date),
        'rms':sorted(by_rm_date),'ams':sorted(by_am_date),'days':DAYS,
        'hierarchy':hierarchy,'hub_meta':hub_meta,
        'date_agg':{d:agg(v) for d,v in sorted(by_date.items())},
        'week_agg':{w:agg(v) for w,v in by_week.items()},
        'month_agg':{m:agg(v) for m,v in by_month.items()},
        'ht_date':{h:{d:agg(v) for d,v in dv.items()} for h,dv in by_ht_date.items()},
        'ht_week':{h:{w:agg(v) for w,v in wv.items()} for h,wv in by_ht_week.items()},
        'ht_month':{h:{m:agg(v) for m,v in mv.items()} for h,mv in by_ht_month.items()},
        'gm_date':{g:{d:agg(v) for d,v in dv.items()} for g,dv in by_gm_date.items()},
        'gm_week':{g:{w:agg(v) for w,v in wv.items()} for g,wv in by_gm_week.items()},
        'gm_month':{g:{m:agg(v) for m,v in mv.items()} for g,mv in by_gm_month.items()},
        'rm_date':{r:{d:agg(v) for d,v in dv.items()} for r,dv in by_rm_date.items()},
        'rm_week':{r:{w:agg(v) for w,v in wv.items()} for r,wv in by_rm_week.items()},
        'rm_month':{r:{m:agg(v) for m,v in mv.items()} for r,mv in by_rm_month.items()},
        'am_date':{a:{d:agg(v) for d,v in dv.items()} for a,dv in by_am_date.items()},
        'am_week':{a:{w:agg(v) for w,v in wv.items()} for a,wv in by_am_week.items()},
        'am_month':{a:{m:agg(v) for m,v in mv.items()} for a,mv in by_am_month.items()},
        'hub_agg':{h:agg(v) for h,v in by_hub.items()},
        'hub_week':{h:{w:agg(v) for w,v in wv.items()} for h,wv in by_hub_week.items()},
        'hub_month':{h:{m:agg(v) for m,v in mv.items()} for h,mv in by_hub_month.items()},
        'dow_overall':{dow:{dt:agg(rows) for dt,rows in dv.items()} for dow,dv in by_dow_overall.items()},
        'dow_gm':{g:{dow:{dt:agg(rows) for dt,rows in ddv.items()} for dow,ddv in dv.items()} for g,dv in by_dow_gm.items()},
        'dow_rm':{r:{dow:{dt:agg(rows) for dt,rows in ddv.items()} for dow,ddv in dv.items()} for r,dv in by_dow_rm.items()},
        'dow_am':{a:{dow:{dt:agg(rows) for dt,rows in ddv.items()} for dow,ddv in dv.items()} for a,dv in by_dow_am.items()},
    }

def load_records():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE) as f: return json.load(f)

def save_records(records):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE,'w') as f: json.dump(records,f)
    D = build_agg(records)
    j = json.dumps(D, separators=(',',':'))
    c = gzip.compress(j.encode(), compresslevel=9)
    b = base64.b64encode(c).decode()
    with open(AGG_FILE,'w') as f: f.write(b)
    return b

def get_agg_b64():
    if os.path.exists(AGG_FILE):
        with open(AGG_FILE) as f: return f.read().strip()
    return None

def gWk(dt):
    d=datetime.strptime(dt,'%Y-%m-%d'); j=datetime(d.year,1,1)
    return 'Week '+str(((d-j).days+j.weekday()+1)//7+1)

def gMo(dt):
    d=datetime.strptime(dt,'%Y-%m-%d')
    return d.strftime("%b'%y")

# ── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('templates','index.html')

@app.route('/api/data')
def api_data():
    b64 = get_agg_b64()
    if not b64:
        return jsonify({'error':'No data uploaded yet. Please ask the owner to upload data.'}), 404
    return jsonify({'data': b64, 'updated_at': get_updated_at()})

@app.route('/api/updated_at')
def api_updated():
    return jsonify({'updated_at': get_updated_at()})

def get_updated_at():
    if os.path.exists(AGG_FILE):
        ts = os.path.getmtime(AGG_FILE)
        return datetime.fromtimestamp(ts).strftime('%d %b %Y, %I:%M %p')
    return None

@app.route('/api/login', methods=['POST'])
def login():
    pwd = request.json.get('password','')
    if pwd == OWNER_PASSWORD:
        session['owner'] = True
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Wrong password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('owner', None)
    return jsonify({'ok': True})

@app.route('/api/upload', methods=['POST'])
def upload():
    if not session.get('owner'):
        return jsonify({'error': 'Unauthorized. Please login as owner first.'}), 403

    import openpyxl
    f = request.files.get('file')
    if not f: return jsonify({'error': 'No file'}), 400

    wb = openpyxl.load_workbook(f, data_only=True)
    ws = wb.active
    headers = [str(c.value or '').strip() for c in next(ws.iter_rows(min_row=1,max_row=1))]

    REQ = ['Date','Hub Name','Hub Type','GM','RM','AM','Total Tickets',
           'Response < 6 Hrs','Response < 24 hrs','Closed By D0','Closed by D1']
    missing = [c for c in REQ if c not in headers]
    if missing: return jsonify({'error': f'Missing columns: {", ".join(missing)}'}), 400

    hi = {h:i for i,h in enumerate(headers)}
    new_recs = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[hi['Date']]: continue
        dt = row[hi['Date']]
        if isinstance(dt, datetime): dt = dt.strftime('%Y-%m-%d')
        else: dt = str(dt).split('T')[0].split(' ')[0]
        wk  = str(row[hi.get('Week',  -1)] or gWk(dt))
        mo  = str(row[hi.get('Month', -1)] or gMo(dt))
        new_recs.append({
            'date':dt,'week':wk,'month':mo,
            'gm':  str(row[hi['GM']] or ''),
            'rm':  str(row[hi['RM']] or ''),
            'am':  str(row[hi['AM']] or ''),
            'hub_type': str(row[hi['Hub Type']] or ''),
            'hub':      str(row[hi['Hub Name']] or ''),
            'total': int(row[hi['Total Tickets']] or 0),
            'r6':   int(row[hi['Response < 6 Hrs']] or 0),
            'r24':  int(row[hi['Response < 24 hrs']] or 0),
            'd0':   int(row[hi['Closed By D0']] or 0),
            'd1':   int(row[hi['Closed by D1']] or 0),
        })

    # Merge: new rows replace existing rows for same date+hub
    existing = load_records()
    key_set = {(r['date'],r['hub']) for r in new_recs}
    merged = [r for r in existing if (r['date'],r['hub']) not in key_set] + new_recs
    merged.sort(key=lambda r: r['date'])

    save_records(merged)
    return jsonify({
        'ok': True,
        'rows_uploaded': len(new_recs),
        'total_rows': len(merged),
        'updated_at': get_updated_at()
    })

@app.route('/api/clear', methods=['POST'])
def clear_data():
    if not session.get('owner'):
        return jsonify({'error': 'Unauthorized'}), 403
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    if os.path.exists(AGG_FILE):  os.remove(AGG_FILE)
    return jsonify({'ok': True})

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
