"""Offline regression tests using disposable SQLite projections only."""

import argparse
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 't3_threads.py'
SPEC = importlib.util.spec_from_file_location('t3_threads', SCRIPT)
t3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(t3)

SCHEMA = '''
CREATE TABLE projection_projects (project_id TEXT, title TEXT, workspace_root TEXT);
CREATE TABLE projection_threads (
    thread_id TEXT PRIMARY KEY, project_id TEXT, title TEXT, branch TEXT,
    worktree_path TEXT, latest_turn_id TEXT, created_at TEXT, updated_at TEXT,
    deleted_at TEXT, archived_at TEXT, pending_approval_count INTEGER DEFAULT 0,
    pending_user_input_count INTEGER DEFAULT 0, private_field TEXT
);
CREATE TABLE projection_thread_sessions (
    thread_id TEXT, status TEXT, provider_name TEXT, provider_thread_id TEXT,
    active_turn_id TEXT, last_error TEXT, updated_at TEXT
);
CREATE TABLE projection_turns (
    row_id TEXT, thread_id TEXT, turn_id TEXT, state TEXT, requested_at TEXT,
    started_at TEXT, completed_at TEXT, checkpoint_ref TEXT,
    checkpoint_status TEXT, checkpoint_files_json TEXT
);
CREATE TABLE projection_thread_messages (
    message_id TEXT PRIMARY KEY, thread_id TEXT, turn_id TEXT, role TEXT,
    text TEXT, is_streaming INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT
);
CREATE TABLE projection_thread_activities (
    activity_id TEXT, thread_id TEXT, turn_id TEXT, kind TEXT, summary TEXT, created_at TEXT
);
CREATE TABLE projection_thread_proposed_plans (
    plan_id TEXT, thread_id TEXT, turn_id TEXT, plan_markdown TEXT,
    updated_at TEXT, implemented_at TEXT
);
CREATE TABLE projection_thread_pull_requests (
    thread_id TEXT, host TEXT, repository TEXT, number INTEGER, url TEXT,
    source TEXT, linked_at TEXT, snapshot_json TEXT
);
CREATE TABLE provider_credentials (secret TEXT);
INSERT INTO provider_credentials VALUES ('fixture-only secret');
'''


class ReaderTests(unittest.TestCase):
    """Exercise public behavior and access restrictions against fixture data."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'state.sqlite'
        self.writer = sqlite3.connect(self.db)
        self.addCleanup(self.writer.close)
        self.writer.executescript(SCHEMA)
        self.add_thread('aaaaaaaa-0000-0000-0000-000000000001', 'First')
        self.tid = 'aaaaaaaa-0000-0000-0000-000000000001'

    def add_thread(self, tid, title, **fields):
        values = dict(thread_id=tid, project_id='project', title=title,
                      updated_at='2026-01-01', **fields)
        self.writer.execute(
            f'INSERT INTO projection_threads ({", ".join(values)}) '
            f'VALUES ({", ".join("?" for _ in values)})', tuple(values.values()))
        self.writer.commit()

    def message(self, mid, text, role='user', tid=None, streaming=0):
        self.writer.execute(
            'INSERT INTO projection_thread_messages '
            '(message_id, thread_id, role, text, is_streaming, created_at) VALUES (?,?,?,?,?,?)',
            (mid, tid or self.tid, role, text, streaming, '2026-01-01'))
        self.writer.commit()

    def reader(self):
        self.writer.commit()
        reader = t3.Reader(self.db)
        self.addCleanup(reader.conn.close)
        return reader

    def collect(self, command='list', **options):
        args = dict(command=command, search='', messages=False, archived=False,
                    offset=0, limit=20, thread=self.tid, before=None, text_limit=100)
        args.update(options)
        reader = self.reader()
        try:
            return t3.collect(reader, argparse.Namespace(**args))
        finally:
            reader.conn.close()

    def test_unicode_message_search_matches_metadata_casefold(self):
        self.message('m1', 'CAFÉ issue on Straße')
        for query in ('café issue', 'STRASSE'):
            with self.subTest(query=query):
                rows = self.collect(search=query, messages=True)['threads']
                self.assertEqual([r['thread']['thread_id'] for r in rows], [self.tid])
                self.assertTrue(rows[0]['message_match'])
        self.assertEqual(self.collect(search='café issue')['threads'], [])
        self.writer.execute('UPDATE projection_threads SET title=?', ('CAFÉ issue',))
        self.assertFalse(self.collect(search='café issue')['threads'][0]['message_match'])

    def test_search_metacharacters_are_literal(self):
        self.message('m1', r'100% path_name C:\cache')
        self.add_thread('bbbbbbbb', 'Other')
        self.message('m2', '1000 pathXname', tid='bbbbbbbb')
        for query in ('100%', 'path_name', r'C:\cache'):
            with self.subTest(query=query):
                rows = self.collect(search=query, messages=True)['threads']
                self.assertEqual([r['thread']['thread_id'] for r in rows], [self.tid])

    def test_search_and_show_exclude_reasoning_and_system_messages(self):
        self.message('m1', 'hidden reasoning', role='reasoning')
        self.message('m2', 'hidden system', role='system')
        self.message('m3', None)
        self.message('m4', 'visible answer', role='assistant')
        self.assertEqual(self.collect(search='hidden', messages=True)['threads'], [])
        self.assertEqual([m['message_id'] for m in self.collect('show')['messages']], ['m3', 'm4'])

    def test_list_pagination_and_archived_deleted_filters(self):
        self.add_thread('bbbbbbbb', 'Second')
        self.add_thread('cccccccc', 'Archived', archived_at='2026-01-02')
        self.add_thread('dddddddd', 'Deleted', deleted_at='2026-01-02')
        first = self.collect(limit=1)
        second = self.collect(limit=1, offset=1)
        self.assertTrue(first['has_more'])
        self.assertFalse(second['has_more'])
        self.assertEqual(second['threads'][0]['thread']['thread_id'], 'bbbbbbbb')
        self.assertEqual(len(self.collect(archived=True)['threads']), 3)
        self.assertEqual(self.collect(offset=20)['threads'], [])

    def test_history_pagination_breaks_timestamp_ties(self):
        for number in range(1, 6):
            self.message(f'm{number}', str(number))
        page = self.collect('show', limit=2)
        self.assertEqual([m['message_id'] for m in page['messages']], ['m4', 'm5'])
        self.assertTrue(page['has_older_messages'])
        page = self.collect('show', limit=2, before='m4')
        self.assertEqual([m['message_id'] for m in page['messages']], ['m2', 'm3'])
        page = self.collect('show', limit=2, before='m2')
        self.assertEqual([m['message_id'] for m in page['messages']], ['m1'])
        self.assertFalse(page['has_older_messages'])

    def test_history_rejects_foreign_or_missing_anchor(self):
        self.message('foreign', 'other', tid='other-thread')
        for anchor in ('foreign', 'missing'):
            with self.subTest(anchor=anchor), self.assertRaisesRegex(ValueError, 'does not belong'):
                self.collect('show', before=anchor)

    def test_resolves_ids_prefixes_provider_aliases_and_urls(self):
        self.writer.execute(
            'INSERT INTO projection_thread_sessions (thread_id,provider_thread_id,provider_name) VALUES (?,?,?)',
            (self.tid, 'provider-alias', 'codex'))
        reader = self.reader()
        for ref in (self.tid, self.tid[:8], 'provider-alias',
                    f'https://t3.example/threads/{self.tid}',
                    f'https://t3.example/?threadId={self.tid}'):
            with self.subTest(ref=ref):
                self.assertEqual(reader.resolve(ref)['thread_id'], self.tid)
        self.assertIn('First · aaaaaaaa · codex', reader.state(reader.resolve(self.tid))['thread_label'])

    def test_resolve_rejects_ambiguous_missing_deleted_and_wildcard_refs(self):
        self.add_thread('aaaaaaaa-0000-0000-0000-000000000002', 'Duplicate prefix')
        self.add_thread('deleted1', 'Deleted', deleted_at='2026-01-02')
        reader = self.reader()
        for ref in ('aaaaaaaa', 'missing1', 'aaaaaaa%', 'deleted1', 'https://t3.example/no-id'):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                reader.resolve(ref)

    def test_status_precedence(self):
        cases = [
            ({}, {}, {}, 'idle'),
            ({'latest_turn_id': 'turn'}, {}, {}, 'unknown'),
            ({'latest_turn_id': 'turn'}, {'state': 'completed'}, {}, 'completed'),
            ({'latest_turn_id': 'turn'}, {'state': 'completed'}, {'status': 'running'}, 'running'),
            ({}, {}, {'active_turn_id': 'turn'}, 'running'),
            ({'latest_turn_id': 'turn'}, {'state': 'running'}, {}, 'running'),
            ({'latest_turn_id': 'turn'}, {'state': 'interrupted'}, {'status': 'running'}, 'interrupted'),
            ({'latest_turn_id': 'turn'}, {'state': 'error'}, {'status': 'running'}, 'error'),
            ({}, {}, {'last_error': 'failed'}, 'error'),
            ({'pending_user_input_count': 1}, {}, {'status': 'running'}, 'awaiting_input'),
            ({'pending_approval_count': 1, 'pending_user_input_count': 1}, {}, {}, 'awaiting_approval'),
        ]
        for i, (thread, turn, session, expected) in enumerate(cases):
            tid = f'case-{i:03}'
            self.add_thread(tid, 'State', **thread)
            if turn:
                self.writer.execute('INSERT INTO projection_turns (thread_id,turn_id,state) VALUES (?,?,?)',
                                    (tid, 'turn', turn['state']))
            if session:
                values = dict(thread_id=tid, **session)
                self.writer.execute(
                    f'INSERT INTO projection_thread_sessions ({", ".join(values)}) '
                    f'VALUES ({", ".join("?" for _ in values)})', tuple(values.values()))
            with self.subTest(expected=expected, case=i):
                self.assertEqual(self.collect('status', thread=tid)['observed_state'], expected)

    def test_streaming_assistant_marks_running(self):
        self.message('m1', 'partial', role='assistant', streaming=1)
        self.assertEqual(self.collect('status')['observed_state'], 'running')

    def test_read_only_and_table_access_restrictions(self):
        reader = self.reader()
        for sql in ("UPDATE projection_threads SET title='changed'",
                    'CREATE TABLE new_table (value TEXT)',
                    'SELECT secret FROM provider_credentials'):
            with self.subTest(sql=sql), self.assertRaises(sqlite3.DatabaseError):
                reader.conn.execute(sql).fetchall()
        self.assertEqual(reader.resolve(self.tid)['title'], 'First')
        self.assertNotIn('private_field', reader.resolve(self.tid))

    def test_missing_optional_tables_are_tolerated(self):
        for table in ('projection_projects', 'projection_thread_sessions', 'projection_turns',
                      'projection_thread_activities', 'projection_thread_proposed_plans',
                      'projection_thread_pull_requests'):
            self.writer.execute(f'DROP TABLE {table}')
        result = self.collect('show')
        self.assertIsNone(result['project'])
        self.assertEqual(result['activities'], [])
        self.assertEqual(result['proposed_plans'], [])
        self.assertEqual(result['pull_requests'], [])

    def test_missing_required_schema_fails_explicitly(self):
        self.writer.execute('DROP TABLE projection_thread_messages')
        self.writer.commit()
        with self.assertRaisesRegex(ValueError, 'Incompatible T3 schema'):
            self.reader()

    def test_missing_database_is_not_created(self):
        absent = Path(self.temp.name) / 'absent.sqlite'
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            t3.Reader(absent)
        self.assertFalse(absent.exists())

    def test_context_clipping_and_status_omits_checkpoint_files(self):
        self.message('m1', 'x' * 150)
        self.writer.execute('UPDATE projection_threads SET latest_turn_id=?', ('turn',))
        self.writer.execute(
            'INSERT INTO projection_turns (thread_id,turn_id,state,checkpoint_files_json) VALUES (?,?,?,?)',
            (self.tid, 'turn', 'completed', 'x' * 150))
        result = self.collect('show')
        self.assertEqual(result['messages'][0]['text'], 'x' * 100)
        self.assertTrue(result['messages'][0]['text_truncated'])
        self.assertEqual(result['messages'][0]['text_original_length'], 150)
        self.assertTrue(result['latest_turn']['checkpoint_files_json_truncated'])
        self.assertNotIn('checkpoint_files_json', self.collect('status')['latest_turn'])

    def test_reader_sees_committed_wal_and_keeps_consistent_snapshot(self):
        self.writer.execute('PRAGMA journal_mode=WAL')
        self.message('m1', 'before')
        reader = self.reader()
        self.message('m2', 'after')
        self.assertEqual(len(reader.rows('projection_thread_messages')), 1)
        self.assertEqual(len(self.reader().rows('projection_thread_messages')), 2)

    def test_cli_works_outside_skill_directory_and_reports_errors(self):
        command = [sys.executable, str(SCRIPT), '--db', str(self.db)]
        result = subprocess.run(command + ['status', self.tid], cwd=self.temp.name,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['observed_state'], 'idle')
        result = subprocess.run(command + ['show', 'missing1'], cwd=self.temp.name,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Thread not found', json.loads(result.stderr)['error'])
        for option, value in (('--limit', '0'), ('--limit', '101'), ('--offset', '-1')):
            result = subprocess.run(command + ['list', option, value], cwd=self.temp.name,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
