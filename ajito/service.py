"""Local Ajito interface over the existing QOL model and Notion client.

Only the window on this Mac can call the API. Tokens never reach the page.
"""
import argparse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import secrets
import math
import statistics
import sys
import threading
from zoneinfo import ZoneInfo

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / 'For_new_users' / 'Scripts'))
from config import load_config, save_config, backup_config, config_path
from core import calculate_qol_score, validate_data
from group_setup import group_config, validate_invitation, check_connections, make_invitation, database_id
from notion_client import NotionClient
from ranking import retrieve_rankings

WEB = ROOT / 'ajito' / 'web'


class App:
    def __init__(self, config=None, client_factory=NotionClient, demo=False):
        self.config = config
        self.error = None
        self.client_factory = client_factory
        self.lock = threading.RLock()
        self.demo = demo
        self.demo_entries = []
        if config is None and not demo:
            try:
                self.config = load_config()
            except (ValueError, OSError) as exc:
                self.error = str(exc)
        if demo:
            self.config = {'user': 'Kenta', 'timezone': 'America/Los_Angeles', 'group_name': 'Doronbo crew',
                'all_users': {name: {'DATABASE_ID': f'{index:032x}', 'NOTION_TOKEN': 'demo'} for index,name in enumerate(('Kenta', 'Kazuma', 'Eoin'),1)}}

    def require_account(self):
        if self.config is None:
            raise ValueError('Join your group in Settings first.')
        return self.config

    def client(self):
        cfg = self.require_account()
        return self.client_factory(cfg['all_users'][cfg['user']], cfg['timezone'])

    def bootstrap(self):
        cfg = self.config
        zone = cfg.get('timezone', 'America/Los_Angeles') if cfg else 'America/Los_Angeles'
        today = datetime.now(ZoneInfo(zone)).date().isoformat()
        return {'configured': bool(cfg), 'user': cfg['user'] if cfg else None, 'timezone': zone,
            'participants': [name for name in cfg['all_users'] if name != 'User_Analysis_Requests_Database'] if cfg else [],
            'group_name': cfg.get('group_name', 'QOL crew') if cfg else 'Your crew',
            'today': today, 'config_error': self.error, 'demo': self.demo, 'version': '2.0.1'}

    @staticmethod
    def preview(data):
        clean = validate_data(data)
        score = round(calculate_qol_score(clean), 1)
        wake, sleep = (datetime.fromisoformat(clean[key]) for key in ('wake_time', 'sleep_time'))
        awake = (sleep-wake).total_seconds()/60
        efficiency = clean['time_focused']/awake*100
        missed = sum(clean[key] == 'No' for key in ('exercise', 'outside', 'talk'))
        healthy = max(0, 60-efficiency)+10*missed
        productive = max(0, 1.5*(70-efficiency)+3*missed)
        return {'score': score, 'efficiency': round(efficiency, 1), 'awake_minutes': awake,
            'route': 'healthy' if healthy <= productive else 'productive',
            'healthy_deduction': round(healthy, 2), 'productive_deduction': round(productive, 2),
            'wake_deduction': round(min(max((wake-wake.replace(hour=8,minute=30,second=0)).total_seconds()/60,0)*.2,15),2),
            'bed_deduction': round(min(abs((sleep-wake.replace(hour=23,minute=30,second=0)).total_seconds()/60)*.2,15),2),
            'social_deduction': round(max(clean['social_media']-45,0)*.2,2), 'offday': clean['offday_special_day']=='Yes'}

    def dispatch(self, route, data):
        if route == '/api/bootstrap':
            return self.bootstrap()
        if route == '/api/preview':
            return self.preview(data)
        if route == '/api/latest':
            if self.demo:
                return {'number': 214+len(self.demo_entries), 'score': 86.2, 'date': '2026-10-19', 'streak': 4}
            page = self.client().latest()
            props = page.get('properties', {}) if page else {}
            return {'number': (NotionClient.entry_number(page)+1) if page else 1,
                'score': props.get('QOL Score', {}).get('number'),
                'date': (props.get('Date', {}).get('date') or {}).get('start'),
                'streak': props.get('Streak', {}).get('number')}
        if route == '/api/rankings':
            if self.demo:
                return {'scores': {'Kenta': 86.2,'Kazuma':92.4,'Eoin':78.6},'dates':{n:'2026-10-19' for n in self.config['all_users']},
                    'streaks':{'Kenta':4,'Kazuma':7,'Eoin':-2},'empty':[],'unavailable':{}}
            return retrieve_rankings(self.require_account()['all_users'], self.client_factory)
        if route == '/api/history':
            if self.demo:
                return {'entries':[dict(date=f'2026-10-{i:02}',score=score,
                    efficiency=round(35+(i*7)%45,1),exercise=i%3!=0,outside=i%4!=0,talk=i%5!=0,offday=False)
                    for i,score in enumerate([64,72,68,85,81,77,90,62,84,88,91,80,75,94,89,86,82,90,86.2],1)]}
            entries=[]
            for page in self.client().query(sorts=[{'property':'Date','direction':'ascending'}]):
                props=page.get('properties',{})
                day=(props.get('Date',{}).get('date') or {}).get('start')
                score=props.get('QOL Score',{}).get('number')
                if day and isinstance(score,(int,float)) and math.isfinite(score):
                    row={'date':day,'score':score}
                    for prop,key in [('Exercise?','exercise'),('Went Outside?','outside'),('Talk to Someone?','talk'),('Offday/Special Day?','offday')]:
                        name=((props.get(prop) or {}).get('select') or {}).get('name')
                        row[key]=True if name=='Yes' else False if name=='No' else None
                    try:
                        from datetime import timedelta
                        wake=datetime.fromisoformat(props['Wake Time']['date']['start']).replace(tzinfo=None)
                        bed=datetime.fromisoformat(props['Sleep Time']['date']['start']).replace(tzinfo=None)
                        if bed<wake and bed.date()==wake.date():bed+=timedelta(days=1)
                        minutes=(bed-wake).total_seconds()/60
                        focused=props['Time Focused']['number']
                        if 0<minutes<1440 and isinstance(focused,(int,float)) and 0<=focused<=minutes:
                            row['efficiency']=round(focused/minutes*100,1)
                    except (KeyError,TypeError,ValueError):pass
                    entries.append(row)
            return {'entries':entries}
        if route == '/api/submit':
            with self.lock:
                if data.get('expected_user') != self.require_account()['user']:
                    raise ValueError('Your selected account changed. Review the entry again before saving.')
                clean=validate_data(data)
                clean['qol_score']=round(calculate_qol_score(clean),1)
                if self.demo:
                    from core import next_streak
                    clean.update(entry_number=str(214+len(self.demo_entries)),streak=next_streak(4,clean['qol_score']))
                    if any(e['todays_date']==clean['todays_date'] for e in self.demo_entries):
                        raise ValueError('An entry already exists for this date.')
                    self.demo_entries.append(clean)
                    return clean
                return self.client().save(clean)
        if route == '/api/invitation':
            return validate_invitation(data)
        if route == '/api/connect':
            if self.demo: raise ValueError('Open the normal app to connect your real crew. Demo mode never changes your settings.')
            with self.lock:
                if not data.get('accept'):
                    raise ValueError('Confirm the shared access before connecting.')
                cfg=group_config(data['invitation'],data['name'],data['token'],data['timezone'])
                failures=check_connections(cfg, self.client_factory)
                if failures:
                    raise ValueError('\n'.join(f'{name}: {error}' for name,error in failures.items()))
                if not self.demo:
                    if self.error: backup_config()
                    save_config(cfg)
                self.config=cfg
                self.error=None
                return self.bootstrap()
        if route == '/api/individual':
            if self.demo: raise ValueError('Open the normal app to connect your real account. Demo mode never changes your settings.')
            with self.lock:
                name=str(data.get('name','')).strip()
                token=str(data.get('token','')).strip()
                cfg={'user':name,'timezone':data.get('timezone','America/Los_Angeles'),
                    'all_users':{name:{'DATABASE_ID':database_id(data.get('database','')),'NOTION_TOKEN':token}}}
                from config import validate_config
                validate_config(cfg)
                failures=check_connections(cfg,self.client_factory)
                if failures: raise ValueError('\n'.join(failures.values()))
                if not self.demo:
                    if self.error: backup_config()
                    save_config(cfg)
                self.config=cfg;self.error=None
                return self.bootstrap()
        if route == '/api/export':
            return make_invitation(self.require_account(), data.get('name','QOL Friends'))
        if route == '/api/insights':
            history=self.dispatch('/api/history', {})['entries']
            grouped={}
            for e in history:
                if isinstance(e.get('score'),(int,float)) and 0<=e['score']<=100:
                    grouped.setdefault(e['date'][:10],[]).append(e['score'])
            valid=[{'date':day,'score':sum(values)/len(values)} for day,values in sorted(grouped.items())]
            recent=valid[-7:];previous=valid[-14:-7]
            avg=lambda rows:round(sum(e['score'] for e in rows)/len(rows),1) if rows else None
            from collections import defaultdict
            from datetime import date
            weekdays=defaultdict(list)
            for entry in valid:
                try: weekdays[date.fromisoformat(entry['date'][:10]).strftime('%A')].append(entry['score'])
                except ValueError: pass
            patterns=[{'day':day,'average':round(sum(scores)/len(scores),1),'count':len(scores)} for day,scores in weekdays.items()]
            patterns.sort(key=lambda p:-p['average'])
            focus_points=[{'date':row['date'][:10],'score':row['score'],'efficiency':row['efficiency'],'offday':row.get('offday')}
                for row in history if isinstance(row.get('efficiency'),(int,float)) and 0<=row['efficiency']<=100 and 0<=row['score']<=100]
            paired=[row for row in focus_points if row['offday'] is False]
            correlation=None
            if len(paired)>=5:
                xs=[row['efficiency'] for row in paired];ys=[row['score'] for row in paired]
                if statistics.pstdev(xs)>0 and statistics.pstdev(ys)>0:
                    mx=statistics.mean(xs);my=statistics.mean(ys)
                    correlation=round(sum((x-mx)*(y-my) for x,y in zip(xs,ys))/math.sqrt(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys)),2)
            habits=[]
            for key,label in [('exercise','Exercise'),('outside','Went outside'),('talk','Talked to someone')]:
                yes=[row['score'] for row in history if row.get(key) is True and row.get('offday') is False and 0<=row['score']<=100]
                no=[row['score'] for row in history if row.get(key) is False and row.get('offday') is False and 0<=row['score']<=100]
                ya=round(statistics.mean(yes),1) if yes else None;na=round(statistics.mean(no),1) if no else None
                habits.append(dict(label=label,yes_count=len(yes),no_count=len(no),yes_average=ya,no_average=na,difference=round(ya-na,1) if ya is not None and na is not None else None))
            return {'total_entries':len(valid),'recent_count':len(recent),'recent_average':avg(recent),
                'previous_count':len(previous),'previous_average':avg(previous),
                'recent_good_days':sum(e['score']>=65 for e in recent),'best_score':max((e['score'] for e in valid),default=None),
                'weekdays':patterns,'focus_points':focus_points,'correlation':correlation,'habits':habits,'scope':'Stored scores; latest seven logged entries, not necessarily seven calendar days.'}
        if route == '/api/day-lab':
            clean=validate_data(data)
            original=self.preview(clean)
            scenarios=[]
            options=[]
            for field,label in [('exercise','Exercise'),('outside','Go outside'),('talk','Talk to someone')]:
                if clean[field]=='No':options.append((label,{field:'Yes'}))
            options += [('30 more focused minutes',{'time_focused':min(int(original['awake_minutes']),clean['time_focused']+30)}),
                        ('30 fewer social-media minutes',{'social_media':max(0,clean['social_media']-30)}),
                        ('Bedtime at 11:30 PM',{'sleep_time':clean['todays_date']+'T23:30:00'}),
                        ('Wake at 8:30 AM',{'wake_time':clean['todays_date']+'T08:30:00'})]
            for label,changes in options:
                try:
                    result=self.preview(dict(clean,**changes))
                    scenarios.append({'label':label,'score':result['score'],'difference':round(result['score']-original['score'],1),'changes':changes})
                except ValueError:pass
            scenarios.sort(key=lambda s:-s['difference'])
            return {'current':original['score'],'scenarios':scenarios,'offday':original['offday']}
        raise ValueError('Unknown action.')


def make_server(app, port=0):
    token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def headers_for(self, status, content_type, size):
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(size))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
        def json_response(self, status, value):
            body=json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
            self.headers_for(status,'application/json; charset=utf-8',len(body));self.wfile.write(body)
        def do_GET(self):
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
                return self.json_response(403,{'error':'Invalid host.'})
            path=self.path.split('?',1)[0]
            if path=='/': path='/index.html'
            target=(WEB/path.lstrip('/')).resolve()
            if not target.is_relative_to(WEB.resolve()) or not target.is_file():
                return self.json_response(404,{'error':'Not found.'})
            body=target.read_bytes()
            kind=mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
            self.headers_for(200,kind,len(body));self.wfile.write(body)
        def do_POST(self):
            expected=f'http://127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host')!=expected[7:] or self.headers.get('Origin') not in (None,expected) or not secrets.compare_digest(self.headers.get('X-QOL-Token',''),token):
                return self.json_response(403,{'error':'This action must come from your QOL window.'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=256*1024:raise ValueError('Request too large or empty.')
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict):raise ValueError('Expected an object.')
                result=app.dispatch(self.path,data)
                self.json_response(200,result)
            except Exception as exc:
                message=str(exc)
                for connection in (app.config or {}).get('all_users',{}).values():
                    secret=connection.get('NOTION_TOKEN','')
                    if secret:message=message.replace(secret,'[token hidden]')
                if data_token:=(data.get('token') if isinstance(locals().get('data'),dict) else None):
                    message=message.replace(str(data_token),'[token hidden]')
                self.json_response(400,{'error':message})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads=True
    return server, token


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--demo',action='store_true')
    parser.add_argument('--parent',type=int)
    parser.add_argument('--port',type=int,default=0)
    args=parser.parse_args()
    if getattr(sys,'frozen',False):
        import zoneinfo
        zoneinfo.reset_tzpath(())
    server,token=make_server(App(demo=args.demo),args.port)
    url=f'http://127.0.0.1:{server.server_port}/#{token}'
    print(json.dumps({'url':url}),flush=True)
    if args.parent:
        def watch():
            import time
            while True:
                time.sleep(2)
                if os.getppid()!=args.parent:
                    server.shutdown();return
        threading.Thread(target=watch,daemon=True).start()
    server.serve_forever(poll_interval=.2)


if __name__=='__main__':main()
