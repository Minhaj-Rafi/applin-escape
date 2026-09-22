import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from model import Store
from save_recovery import backup_store, restore_backup
from main import App

class WindowsBackup(unittest.TestCase):
    def test_connections_closed_before_file_replacement_and_after_restore(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(d); opened=[]; connect=sqlite3.connect; replace=os.replace
            def tracked(*args,**kwargs):
                db=connect(*args,**kwargs); opened.append(db); return db
            def assert_closed():
                for db in opened:
                    with self.assertRaises(sqlite3.ProgrammingError): db.execute('SELECT 1')
            def guarded_replace(*args):
                assert_closed();return replace(*args)
            try:
                with patch('save_recovery.sqlite3.connect',side_effect=tracked),patch('save_recovery.os.replace',side_effect=guarded_replace):
                    for i in range(4):store.set('marker',i);backup_store(store)
                    store.db.close()
                    restore_backup(d)
                    assert_closed()
                with __import__('contextlib').closing(connect(store.directory/'progress.sqlite3')) as db:
                    self.assertEqual(db.execute("SELECT value FROM settings WHERE name='marker'").fetchone()[0],'3')
            finally: store.db.close()

class HomePresentation(unittest.TestCase):
    def test_project_zero_requirements_and_sanctuary_navigation(self):
        with tempfile.TemporaryDirectory() as d:
            a=App(d)
            try:
                a.action('sanctuary');a.draw()
                self.assertNotIn('adventure',[action for _,action in a.buttons])
                a.project_index=0
                with patch.object(a,'text',wraps=a.text) as draw:
                    a.draw_projects({'rescued':43},{'friends':{},'projects46':{'0':1}})
                labels=[c.args[0] for c in draw.call_args_list]
                self.assertIn('Rescued residents: not required',labels)
                self.assertIn('Happy residents: not required',labels)
                self.assertIn('Deliveries completed: 1',labels)
            finally:a.close()
