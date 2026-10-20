import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'For_new_users' / 'Scripts'))
from group_setup import database_id, validate_invitation, read_invitation, make_invitation, group_config, connect_and_save, check_connections
from config import load_config
from ranking import retrieve_rankings


def invitation():
    return {'format':'qol-group','version':1,'group_name':'Friends','timezone':'Europe/London',
            'participants':[{'name':'Alice','database_id':'a'*32},{'name':'Bob','database_id':'b'*32}]}


def configuration():
    return group_config(invitation(),'Bob','test-group-token','Europe/London')


class InvitationTests(unittest.TestCase):
    def test_import_gives_everyone_same_roster_but_own_submission_target(self):
        alice=group_config(invitation(),'Alice','token','America/Los_Angeles')
        bob=configuration()
        self.assertEqual(set(alice['all_users']),set(bob['all_users']))
        self.assertEqual(alice['all_users'][alice['user']]['DATABASE_ID'],'a'*32)
        self.assertEqual(bob['all_users'][bob['user']]['DATABASE_ID'],'b'*32)
        self.assertEqual(bob['all_users']['Alice']['NOTION_TOKEN'],'test-group-token')

    def test_export_never_copies_credentials_or_analysis_account(self):
        config=configuration()
        config['all_users']['User_Analysis_Requests_Database']={'DATABASE_ID':'c'*32,'NOTION_TOKEN':'analysis-secret'}
        exported=make_invitation(config,'Friends')
        self.assertEqual(len(exported['participants']),2)
        self.assertNotIn('test-group-token',json.dumps(exported))
        self.assertNotIn('analysis-secret',json.dumps(exported))
        self.assertNotIn('NOTION_TOKEN',json.dumps(exported))

    def test_database_url_uses_database_id_not_view(self):
        self.assertEqual(database_id('https://www.notion.so/workspace/My-Database-'+ 'a'*32+'?v='+'b'*32), 'a'*32)
        self.assertEqual(database_id('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),'a'*32)
        for bad in ['bad','https://evil.example/'+'a'*32,5]:
            with self.assertRaises(ValueError): database_id(bad)

    def test_duplicate_name_or_database_rejected(self):
        for update in [{'name':'alice'},{'database_id':'a'*32}]:
            data=invitation(); data['participants'][1].update(update)
            with self.assertRaises(ValueError): validate_invitation(data)

    def test_malformed_or_secret_containing_invitation_rejected(self):
        cases=[[],{},dict(invitation(),version=2),dict(invitation(),timezone='Invalid/Zone'),
               dict(invitation(),participants=[]),dict(invitation(),NOTION_TOKEN='private')]
        secret=invitation(); secret['participants'][0]['NOTION_TOKEN']='private'; cases.append(secret)
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(ValueError): validate_invitation(data)

    def test_unknown_identity_and_empty_token_rejected(self):
        for name,token in [('Mallory','token'),('Alice',' ')]:
            with self.assertRaises(ValueError): group_config(invitation(),name,token,'Europe/London')

    def test_file_import(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invite.json'; path.write_text(json.dumps(invitation()))
            self.assertEqual(read_invitation(path),invitation())
            path.write_text('{bad')
            with self.assertRaises(ValueError): read_invitation(path)
            path.write_text('x'*131073)
            with self.assertRaises(ValueError): read_invitation(path)


class GroupConnectionTests(unittest.TestCase):
    def factory(self, failure=None):
        clients=[]
        def create(connection, timezone):
            client=Mock(source_id=connection['DATABASE_ID'])
            if connection['DATABASE_ID']==failure:
                client.check_schema.side_effect=RuntimeError('Notion refused test-group-token')
            clients.append(client)
            return client
        return create,clients

    def test_reads_all_connections_before_saving(self):
        factory,clients=self.factory()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'config.json'
            result=connect_and_save(configuration(),path,factory)
            self.assertEqual(load_config(path),result)
            self.assertEqual(len(clients),2)
            for client in clients:
                client.check_schema.assert_called_once()
                args=client.request.call_args
                self.assertEqual(args.args,('POST','data_sources/'+client.source_id+'/query'))
                self.assertEqual(args.kwargs['json'],{'page_size':1})
            self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def test_one_failed_connection_prevents_save_and_preserves_old_config(self):
        factory,clients=self.factory('b'*32)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'config.json'; path.write_text('original')
            with self.assertRaisesRegex(ValueError,'Bob') as error:
                connect_and_save(configuration(),path,factory)
            self.assertNotIn('test-group-token',str(error.exception))
            self.assertEqual(path.read_text(),'original')
            self.assertEqual(len(clients),2)

    def test_failed_query_also_prevents_setup(self):
        client=Mock(source_id='a'); client.request.side_effect=RuntimeError('timeout')
        self.assertEqual(set(check_connections(configuration(),lambda *args:client)),{'Alice','Bob'})


class GroupRankingTests(unittest.TestCase):
    def test_failed_user_does_not_hide_others_and_empty_user_is_visible(self):
        connections={name:{'NOTION_TOKEN':'token-'+name,'DATABASE_ID':name} for name in ['Alice','Bob','Cathy','Dan']}
        def create(connection):
            client=Mock()
            name=connection['DATABASE_ID']
            if name=='Bob': client.latest.side_effect=RuntimeError('invalid token-Bob')
            elif name=='Cathy': client.latest.return_value=None
            else: client.latest.return_value={'properties':{'QOL Score':{'number':0 if name=='Alice' else 90},'Date':{'date':{'start':'2026-10-19'}}}}
            return client
        result=retrieve_rankings(connections,create)
        self.assertEqual(result['scores'],{'Alice':0,'Dan':90})
        self.assertEqual(result['empty'],['Cathy'])
        self.assertEqual(list(result['unavailable']),['Bob'])
        self.assertNotIn('token-Bob',result['unavailable']['Bob'])
        self.assertEqual(result['dates']['Dan'],'2026-10-19')

    def test_analysis_connection_is_not_a_competitor(self):
        result=retrieve_rankings({'User_Analysis_Requests_Database':{}},lambda connection: self.fail('Should not connect'))
        self.assertEqual(result['scores'],{})

    def test_all_failed_is_explicit(self):
        def create(connection):
            raise RuntimeError('offline')
        result=retrieve_rankings(configuration()['all_users'],create)
        self.assertEqual(result['scores'],{})
        self.assertEqual(set(result['unavailable']),{'Alice','Bob'})
