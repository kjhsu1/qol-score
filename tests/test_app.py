import copy
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'For_new_users' / 'Scripts'))
from core import calculate_qol_score, validate_data, top_three, next_streak
from notion_client import NotionClient, NotionError, SCHEMA
from config import load_config, save_config
import requests


def sample(**overrides):
    data = dict(wake_time='2026-10-19T08:30:00', sleep_time='2026-10-19T23:30:00',
                todays_date='2026-10-19', exercise='Yes', outside='Yes', talk='Yes',
                social_media='0', time_focused='700', offday_special_day='No', diary='')
    return dict(data, **overrides)


def page(number, score=80, date='2026-10-18', streak=2):
    return {'properties': {'Name': {'title': [{'plain_text': str(number)}]},
                           'QOL Score': {'number': score}, 'Streak': {'number': streak},
                           'Date': {'date': {'start': date}}}}


def response(data, status=200):
    result = Mock(ok=status < 400, status_code=status)
    result.json.return_value = data
    return result


class ScoringTests(unittest.TestCase):
    def test_perfect_day(self):
        self.assertEqual(calculate_qol_score(sample()), 100)

    def test_healthy_route_wins_with_all_habits(self):
        self.assertAlmostEqual(calculate_qol_score(sample(time_focused='495')), 95)
        self.assertEqual(calculate_qol_score(sample(time_focused='540')), 100)

    def test_midnight_uses_waking_day_bedtime(self):
        self.assertAlmostEqual(calculate_qol_score(sample(sleep_time='2026-10-20T00:01:00')), 93.8)
        self.assertAlmostEqual(calculate_qol_score(sample(sleep_time='2026-10-19T00:01:00')), 93.8)

    def test_rejects_equal_times(self):
        with self.assertRaises(ValueError):
            calculate_qol_score(sample(sleep_time='2026-10-19T08:30:00'))

    def test_invalid_inputs(self):
        for overrides in [dict(social_media='-1'), dict(time_focused='99999'),
                          dict(social_media='1.5'), dict(time_focused=''), dict(exercise='Maybe'),
                          dict(todays_date='2026-02-30'), dict(wake_time='bad'),
                          dict(todays_date='2026-10-18'), dict(sleep_time='2026-10-21T00:00:00'),
                          dict(sleep_time='2026-10-18T23:00:00'), dict(diary='x'*20001)]:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError): validate_data(sample(**overrides))

    def test_offday_and_floor(self):
        self.assertEqual(calculate_qol_score(sample(offday_special_day='Yes',time_focused='0')), 100)
        self.assertEqual(calculate_qol_score(sample(time_focused='0',social_media='900')), 0)

    def test_streak_switches(self):
        for old, score, expected in [(0,65,1),(3,80,4),(-2,80,1),(2,64,-1),(-2,0,-3),(None,10,-1)]:
            self.assertEqual(next_streak(old,score),expected)

    def test_ranking_handles_zero_and_third(self):
        self.assertEqual(top_three({'A':90,'B':80,'C':70,'D':0}), [('A',90),('B',80),('C',70)])
        self.assertEqual(top_three({'B':0,'A':0}), [('A',0),('B',0)])
        self.assertEqual(top_three({}), [])
        self.assertEqual(top_three({'A':None,'B':float('nan')}), [])

    def test_both_versions_share_model(self):
        path=ROOT/'For_Kenta/Scripts/QOL_LIB.py'
        spec=importlib.util.spec_from_file_location('kenta_model',path)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        example=sample(time_focused='630',exercise='No',outside='No')
        self.assertEqual(module.calculate_qol_score(example),94)
        self.assertEqual(module.calculate_qol_score(example),calculate_qol_score(example))

    def test_ui_import_has_no_window_or_requests(self):
        import UI
        self.assertFalse(hasattr(UI, 'root'))


class NotionTests(unittest.TestCase):
    def client(self, responses=()):
        session=Mock()
        session.request.side_effect=list(responses)
        client=NotionClient({'NOTION_TOKEN':'test-token','DATABASE_ID':'db'},session=session)
        client.source_id='source'
        client.properties={k:{'type':v} for k,v in SCHEMA.items()}
        return client,session

    def test_numeric_latest_and_pagination(self):
        client,session=self.client([response({'results':[page(9)],'has_more':True,'next_cursor':'next'}),
                                    response({'results':[page(100)],'has_more':False})])
        self.assertEqual(client.entry_number(client.latest()),100)
        self.assertEqual(session.request.call_args.kwargs['json']['start_cursor'],'next')
        self.assertEqual(session.request.call_args.kwargs['timeout'],(5,20))

    def test_empty_and_non_numeric_titles(self):
        client,_=self.client([response({'results':[]})])
        self.assertEqual(client.highest(),0)
        self.assertEqual(client.entry_number(page('Welcome')),0)
        self.assertEqual(client.entry_number({'properties':{}}),0)

    def test_invalid_cursor(self):
        client,_=self.client([response({'results':[],'has_more':True,'next_cursor':None})])
        with self.assertRaises(NotionError): list(client.query())

    def test_http_error(self):
        for code in [401,403,404,429,500]:
            client,_=self.client([response({'message':'Rejected'},code)])
            with self.assertRaises(NotionError): list(client.query())

    def test_timeout_no_write_retry(self):
        client,session=self.client()
        session.request.side_effect=requests.Timeout('no connection')
        with self.assertRaises(NotionError): client.request('POST','pages',json={})
        self.assertEqual(session.request.call_count,1)

    def test_bad_json(self):
        result=response({}); result.json.side_effect=ValueError()
        client,_=self.client([result])
        with self.assertRaises(NotionError): list(client.query())

    def test_duplicate_prevents_write(self):
        client,session=self.client([response({'results':[page(1)]})])
        data=validate_data(sample()); data['qol_score']=100
        with self.assertRaises(ValueError): client.save(data)
        self.assertEqual(session.request.call_count,1)

    def test_save_normalizes_payload_and_chunks_diary(self):
        client,session=self.client([response({'results':[]}),response({'results':[page(9)]}),response({'id':'created'})])
        data=validate_data(sample(diary='あ'*4200, time_focused='630', exercise='No', outside='No'))
        data['qol_score']=round(calculate_qol_score(data),1)
        saved=client.save(data)
        payload=session.request.call_args.kwargs['json']
        self.assertEqual(saved['entry_number'],'10')
        self.assertEqual(saved['streak'],3)
        self.assertEqual(payload['parent'],{'data_source_id':'source'})
        self.assertEqual(payload['properties']['QOL Score']['number'],94)
        self.assertEqual(len(payload['properties']['Diary']['rich_text']),3)
        self.assertEqual(payload['properties']['Date']['date']['start'],'2026-10-19')
        self.assertTrue(payload['properties']['Wake Time']['date']['start'].endswith('-07:00'))

    def test_backdated_entry_prevents_write(self):
        client,session=self.client([response({'results':[]}),response({'results':[page(9,date='2026-10-20')]})])
        data=validate_data(sample()); data['qol_score']=100
        with self.assertRaises(ValueError): client.save(data)
        self.assertEqual(session.request.call_count,2)

    def test_missing_schema(self):
        client,_=self.client(); del client.properties['Date']
        with self.assertRaisesRegex(NotionError,'Date'): client.check_schema()

    def test_source_discovery(self):
        client,session=self.client([response({'data_sources':[{'id':'new'}]}),response({'properties':{k:{'type':v} for k,v in SCHEMA.items()}})])
        client.source_id=None; client.check_schema()
        self.assertEqual(client.source_id,'new')

    def test_multiple_sources_rejected(self):
        client,_=self.client([response({'data_sources':[{'id':'a'},{'id':'b'}]})]); client.source_id=None
        with self.assertRaises(NotionError): client.resolve()

    def test_daylight_saving_and_timezone(self):
        client,_=self.client()
        with self.assertRaises(ValueError): client.iso('2026-03-08T02:30:00')
        with self.assertRaises(ValueError): client.iso('2026-11-01T01:30:00')
        self.assertTrue(client.iso('2026-01-01T08:00:00').endswith('-08:00'))
        self.assertTrue(client.iso('2026-07-01T08:00:00').endswith('-07:00'))


class ConfigTests(unittest.TestCase):
    def test_private_roundtrip(self):
        data={'user':'A','timezone':'Europe/London','all_users':{'A':{'NOTION_TOKEN':'test','DATABASE_ID':'test'}}}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'config.json'
            self.assertIsNone(load_config(path))
            save_config(data,path)
            self.assertEqual(load_config(path),data)
            self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def test_first_run_creates_private_account(self):
        import UI
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'account.json'
            with patch.dict(os.environ, {'QOL_CONFIG':str(path)}), \
                 patch('tkinter.simpledialog.askstring', side_effect=['Alice','test-token','database','Europe/London']):
                result=UI.individual_setup(None)
            self.assertEqual(result['user'],'Alice')
            self.assertEqual(load_config(path)['timezone'],'Europe/London')
            self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def test_canceled_setup_creates_no_config(self):
        import UI
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'account.json'
            with patch.dict(os.environ, {'QOL_CONFIG':str(path)}), \
                 patch('tkinter.simpledialog.askstring', return_value=None):
                self.assertIsNone(UI.individual_setup(None))
            self.assertFalse(path.exists())

    def test_invalid_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'config.json'; path.write_text('{bad')
            with self.assertRaises(ValueError): load_config(path)
            with self.assertRaises(ValueError): save_config({'user':'missing'},path)


if __name__=='__main__':
    unittest.main()
