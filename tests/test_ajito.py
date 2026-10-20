"""Ajito keeps the established scoring, writes, and multi-user routing."""
import importlib.util
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock, patch
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'For_new_users/Scripts'))
spec=importlib.util.spec_from_file_location('ajito_service',ROOT/'ajito/service.py')
service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)
from core import calculate_qol_score, validate_data


def data(**changes):
    return dict(dict(wake_time='2026-10-20T08:30:00',sleep_time='2026-10-20T23:30:00',todays_date='2026-10-20',exercise='Yes',outside='Yes',talk='Yes',social_media='0',time_focused='495',offday_special_day='No',diary='Test 日本語',expected_user='Alice'),**changes)


def config():
    return {'user':'Alice','timezone':'Europe/London','all_users':{'Alice':{'NOTION_TOKEN':'secret-alice-test','DATABASE_ID':'a'*32},'Bob':{'NOTION_TOKEN':'secret-bob-test','DATABASE_ID':'b'*32}}}


class AjitoTests(unittest.TestCase):
    def test_preview_uses_the_existing_model_for_varying_days(self):
        for focused in (0,200,450,495,540,630,666,800):
            for habit in ('Yes','No'):
                values=data(time_focused=str(focused),exercise=habit)
                self.assertEqual(service.App.preview(values)['score'],round(calculate_qol_score(values),1))
        self.assertEqual(service.App.preview(data(time_focused='630',exercise='No'))['score'],97)
        self.assertEqual(service.App.preview(data(sleep_time='2026-10-20T01:30:00',exercise='No',time_focused='510'))['score'],65)

    def test_submit_routes_to_selected_database_with_shared_client(self):
        client=Mock();client.save.side_effect=lambda d:d
        factory=Mock(return_value=client)
        app=service.App(config(),factory)
        saved=app.dispatch('/api/submit',data())
        factory.assert_called_once_with(config()['all_users']['Alice'],'Europe/London')
        self.assertEqual(saved['qol_score'],95)
        self.assertEqual(saved['sleep_time'],'2026-10-20T23:30:00')
        self.assertEqual(client.save.call_args.args[0]['diary'],'Test 日本語')

    def test_changed_identity_and_invalid_entries_never_write(self):
        client=Mock();app=service.App(config(),Mock(return_value=client))
        for bad in (data(expected_user='Bob'),data(time_focused='9000'),data(social_media='-1')):
            with self.assertRaises(ValueError):app.dispatch('/api/submit',bad)
        client.save.assert_not_called()

    def test_bootstrap_does_not_expose_tokens_or_database_ids(self):
        app=service.App(config());encoded=json.dumps(app.bootstrap())
        self.assertNotIn('secret-alice-test',encoded);self.assertNotIn('a'*32,encoded)
        self.assertEqual(app.bootstrap()['participants'],['Alice','Bob'])

    def test_rankings_use_entire_existing_roster(self):
        app=service.App(config(),Mock())
        with patch.object(service,'retrieve_rankings',return_value={'ok':True}) as read:
            self.assertEqual(app.dispatch('/api/rankings',{}),{'ok':True})
            self.assertEqual(read.call_args.args[0],config()['all_users'])

    def test_failed_group_check_preserves_current_account(self):
        app=service.App(config(),Mock())
        invitation={'format':'qol-group','version':1,'group_name':'Friends','timezone':'Europe/London','participants':[{'name':'Bob','database_id':'b'*32}]}
        with patch.object(service,'check_connections',return_value={'Bob':'No access'}),patch.object(service,'save_config') as save:
            with self.assertRaises(ValueError):app.dispatch('/api/connect',{'invitation':invitation,'name':'Bob','token':'new-token','timezone':'Europe/London','accept':True})
            save.assert_not_called();self.assertEqual(app.config,config())

    def test_demo_cannot_write_to_notion(self):
        factory=Mock();app=service.App(demo=True,client_factory=factory)
        result=app.dispatch('/api/submit',data(expected_user='Kenta'))
        self.assertEqual(result['qol_score'],95);factory.assert_not_called()
        with self.assertRaises(ValueError):app.dispatch('/api/submit',data(expected_user='Kenta'))

    def test_debrief_uses_stored_scores_without_modifying_history(self):
        app=service.App(demo=True)
        result=app.dispatch('/api/insights',{})
        self.assertEqual(result['total_entries'],19)
        self.assertEqual(result['recent_count'],7)
        self.assertEqual(result['previous_count'],7)
        self.assertTrue(result['weekdays'])
        self.assertEqual(len(app.demo_entries),0)

    def test_day_lab_uses_exact_same_engine_without_mutating_form(self):
        app=service.App(demo=True)
        candidate=data(exercise='No',time_focused='450')
        original=dict(candidate)
        result=app.dispatch('/api/day-lab',candidate)
        self.assertEqual(candidate,original)
        for row in result['scenarios']:
            expected=round(calculate_qol_score(dict(candidate,**row['changes'])),1)
            self.assertEqual(row['score'],expected)
            self.assertEqual(row['difference'],round(expected-result['current'],1))
        self.assertEqual(app.demo_entries,[])

    def test_analysis_is_descriptive_excludes_offdays_and_reports_counts(self):
        rows=[{'date':f'2026-10-{i:02}','score':i*10,'efficiency':i*10,
               'exercise':i%2==0,'outside':True,'talk':False,'offday':False} for i in range(1,7)]
        rows.append({'date':'2026-10-07','score':100,'efficiency':0,'exercise':True,'outside':True,'talk':True,'offday':True})
        class HistoryApp(service.App):
            def dispatch(self,route,data):
                if route=='/api/history':return {'entries':rows}
                return super().dispatch(route,data)
        report=HistoryApp(demo=True).dispatch('/api/insights',{})
        self.assertEqual(report['correlation'],1.0)
        self.assertEqual(report['habits'][0]['yes_count'],3)
        self.assertEqual(report['habits'][0]['no_count'],3)
        self.assertEqual(report['habits'][0]['difference'],10)
        self.assertEqual(len(report['focus_points']),7)

    def test_analysis_rejects_false_precision_for_small_or_constant_samples(self):
        class HistoryApp(service.App):
            def dispatch(self,route,data):
                if route=='/api/history':return {'entries':[{'date':f'2026-10-{i:02}','score':50,'efficiency':50} for i in range(1,7)]}
                return super().dispatch(route,data)
        result=HistoryApp(demo=True).dispatch('/api/insights',{})
        self.assertIsNone(result['correlation'])
        self.assertIsNone(result['habits'][0]['difference'])
        self.assertEqual(result['habits'][0]['yes_count'],0)

    def test_local_server_guards_and_unicode_json(self):
        app=service.App(demo=True);server,token=service.make_server(app)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            self.assertEqual(requests.post(base+'/api/bootstrap',json={}).status_code,403)
            headers={'X-QOL-Token':token}
            self.assertEqual(requests.post(base+'/api/bootstrap',json={},headers=dict(headers,Origin='https://evil.test')).status_code,403)
            self.assertEqual(requests.get(base+'/',headers={'Host':'evil.test'}).status_code,403)
            result=requests.post(base+'/api/bootstrap',json={},headers=headers)
            self.assertEqual(result.status_code,200);self.assertNotIn('NOTION_TOKEN',result.text)
            self.assertEqual(requests.post(base+'/api/preview',json=data(),headers=headers).json()['score'],95)
            self.assertEqual(requests.post(base+'/api/preview',json=[],headers=headers).status_code,400)
            self.assertEqual(requests.get(base+'/').status_code,200)
            self.assertIn("frame-ancestors 'none'",requests.get(base+'/').headers['Content-Security-Policy'])
            self.assertEqual(requests.get(base+'/../service.py').status_code,404)
        finally:server.shutdown();server.server_close();thread.join(2)


if __name__=='__main__':unittest.main()
