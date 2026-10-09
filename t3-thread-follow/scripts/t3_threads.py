#!/usr/bin/env python3
"""Read selected T3 Code projections; no provider stores, credentials, or writes."""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


FIELDS = {
    'projection_projects': 'project_id title workspace_root',
    'projection_threads': (
        'thread_id project_id title branch worktree_path latest_turn_id created_at '
        'updated_at deleted_at archived_at pending_approval_count pending_user_input_count'
    ),
    'projection_thread_sessions': (
        'thread_id status provider_name provider_thread_id active_turn_id last_error updated_at'
    ),
    'projection_turns': (
        'row_id thread_id turn_id state requested_at started_at completed_at checkpoint_ref '
        'checkpoint_status checkpoint_files_json'
    ),
    'projection_thread_messages': 'message_id thread_id turn_id role text is_streaming created_at updated_at',
    'projection_thread_activities': 'activity_id thread_id turn_id kind summary created_at',
    'projection_thread_pull_requests': 'host repository number url source linked_at snapshot_json',
    'projection_thread_proposed_plans': 'plan_id turn_id plan_markdown updated_at implemented_at',
}
TABLES = set(FIELDS)


class Reader:
    """Read an allowlisted projection snapshot without modifying T3 state."""

    def __init__(self, path):
        """Open an existing database read-only and check the minimum schema."""
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f'T3 state database unavailable: {path}. Supply --db with an accessible T3 state.sqlite.')
        self.path = str(path)
        self.conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5)
        self.conn.row_factory = sqlite3.Row
        self.conn.create_function('T3_CASEFOLD', 1, casefold_text)
        self.conn.execute('PRAGMA query_only=ON')
        self.conn.set_authorizer(self.authorize)
        self.conn.execute('BEGIN')  # Consistent snapshot per invocation, including the live WAL.
        names = [r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        self.columns = {}
        for table in TABLES.intersection(names):
            self.columns[table] = {r[1] for r in self.conn.execute(f'PRAGMA table_info({table})')}
        required = {
            'projection_threads': {'thread_id', 'project_id', 'title', 'deleted_at', 'updated_at', 'latest_turn_id'},
            'projection_thread_messages': {'message_id', 'thread_id', 'role', 'text', 'created_at', 'is_streaming'},
        }
        for table, columns in required.items():
            if not columns.issubset(self.columns.get(table, set())):
                self.conn.close()
                raise ValueError(f'Incompatible T3 schema: missing required columns in {table}.')

    @staticmethod
    def authorize(action, table, column, database, source):
        """Deny reads outside the selected projections and schema metadata."""
        if action == sqlite3.SQLITE_READ and table not in TABLES | {'sqlite_master'}:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def rows(self, table, where='', params=(), order='', limit=None):
        """Select available public fields, tolerating absent optional tables."""
        if table not in self.columns:
            return []
        fields = [f for f in FIELDS[table].split() if f in self.columns[table]]
        sql = f'SELECT {", ".join(fields)} FROM {table}'
        if where:
            sql += ' WHERE ' + where
        if order:
            sql += ' ORDER BY ' + order
        if limit is not None:
            sql += ' LIMIT ?'
            params = (*params, limit)
        return [dict(r) for r in self.conn.execute(sql, params)]

    def resolve(self, reference):
        """Resolve a T3 ID, unique prefix, provider alias, or thread URL."""
        reference = reference.strip()
        if '://' in reference:
            url = urlsplit(reference)
            query = parse_qs(url.query)
            candidate = (query.get('threadId') or query.get('thread_id') or [None])[0]
            ids = re.findall(r'[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}', unquote(url.path + '/' + url.fragment))
            if not candidate and not ids:
                raise ValueError('No recognizable thread ID in URL. Supply the T3 thread ID or search its title.')
            reference = candidate or ids[-1]
        matches = self.rows('projection_threads', 'thread_id=? AND deleted_at IS NULL', (reference,))
        if not matches and 'provider_thread_id' in self.columns.get('projection_thread_sessions', set()):
            aliases = self.rows('projection_thread_sessions', 'provider_thread_id=?', (reference,))
            for alias in aliases:
                matches.extend(self.rows('projection_threads', 'thread_id=? AND deleted_at IS NULL', (alias['thread_id'],)))
        if not matches and len(reference) >= 8:
            matches = self.rows('projection_threads', "thread_id LIKE ? ESCAPE '\\' AND deleted_at IS NULL", (escape_like(reference) + '%',), limit=6)
        if not matches:
            raise ValueError('Thread not found. Use list --search to discover its T3 ID in this installation.')
        if len(matches) != 1:
            raise ValueError('Ambiguous thread reference; use a full T3 ID. Candidates: ' + json.dumps(matches))
        return matches[0]

    def state(self, thread):
        """Combine turn, session, streaming, and blocker signals into status."""
        tid = thread['thread_id']
        sessions = self.rows('projection_thread_sessions', 'thread_id=?', (tid,), limit=1)
        session = sessions[0] if sessions else None
        latest_id = thread.get('latest_turn_id')
        turns = self.rows('projection_turns', 'thread_id=? AND turn_id=?', (tid, latest_id), limit=1) if latest_id else []
        turn = turns[0] if turns else None
        streaming = bool(self.conn.execute(
            "SELECT 1 FROM projection_thread_messages WHERE thread_id=? AND role='assistant' AND is_streaming=1 LIMIT 1", (tid,)
        ).fetchone())
        state = (turn or {}).get('state')
        if thread.get('pending_approval_count', 0):
            observed = 'awaiting_approval'
        elif thread.get('pending_user_input_count', 0):
            observed = 'awaiting_input'
        elif state in ('error', 'interrupted'):
            observed = state
        elif (session or {}).get('last_error'):
            observed = 'error'
        elif state == 'running' or (session or {}).get('status') == 'running' or (session or {}).get('active_turn_id') or streaming:
            observed = 'running'
        elif state == 'completed':
            observed = 'completed'
        elif latest_id is None and not streaming and not (session or {}).get('last_error'):
            observed = 'idle'
        else:
            observed = 'unknown'
        label = f"{thread['title']} · {tid[:8]} · {(session or {}).get('provider_name') or 'unknown provider'}"
        return {'thread_label': label, 'observed_state': observed, 'session': session, 'latest_turn': turn, 'has_streaming_assistant_message': streaming}


def casefold_text(value):
    """Provide Unicode case folding to SQLite, treating NULL as empty text."""
    return value.casefold() if isinstance(value, str) else ''


def escape_like(value):
    """Escape SQL LIKE metacharacters for literal thread-prefix matching."""
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def clip(row, field, limit):
    """Bound a text field and expose truncation metadata when needed."""
    value = row.get(field)
    if isinstance(value, str) and len(value) > limit:
        row[field] = value[:limit]
        row[field + '_truncated'] = True
        row[field + '_original_length'] = len(value)


def collect(reader, args):
    """Build a filtered thread page, status snapshot, or context page."""
    if args.command == 'list':
        where = 'deleted_at IS NULL'
        if not args.archived and 'archived_at' in reader.columns['projection_threads']:
            where += ' AND archived_at IS NULL'
        threads = reader.rows('projection_threads', where, order='updated_at DESC, thread_id ASC')
        projects = {p['project_id']: p for p in reader.rows('projection_projects')}
        sessions = {s['thread_id']: s for s in reader.rows('projection_thread_sessions')}
        result = []
        for thread in threads:
            project = projects.get(thread['project_id'])
            session = sessions.get(thread['thread_id'])
            searchable = ' '.join(str(x or '') for x in [thread.get('title'), thread.get('branch'), thread.get('worktree_path'), (project or {}).get('title')])
            message_match = False
            if args.search and args.search.casefold() not in searchable.casefold():
                if not args.messages:
                    continue
                message_match = bool(reader.conn.execute(
                    "SELECT 1 FROM projection_thread_messages WHERE thread_id=? AND role IN ('user','assistant') AND instr(T3_CASEFOLD(text), ?) > 0 LIMIT 1",
                    (thread['thread_id'], args.search.casefold()),
                ).fetchone())
                if not message_match:
                    continue
            result.append({'thread': thread, 'project': project, 'provider': (session or {}).get('provider_name'), 'message_match': message_match})
        page = result[args.offset:args.offset + args.limit]
        for item in page:
            state = reader.state(item['thread'])
            item.update({key: state[key] for key in ('thread_label', 'observed_state')})
        return {'threads': page, 'offset': args.offset, 'has_more': args.offset + args.limit < len(result)}

    thread = reader.resolve(args.thread)
    result = {'thread': thread, **reader.state(thread)}
    project = reader.rows('projection_projects', 'project_id=?', (thread['project_id'],), limit=1)
    result['project'] = project[0] if project else None
    if args.command == 'status':
        if result['latest_turn']:
            result['latest_turn'].pop('checkpoint_files_json', None)
        return result
    tid = thread['thread_id']
    where = "thread_id=? AND role IN ('user','assistant')"
    params = (tid,)
    if args.before:
        anchor = reader.rows('projection_thread_messages', 'thread_id=? AND message_id=?', (tid, args.before), limit=1)
        if not anchor:
            raise ValueError('--before message ID does not belong to this thread.')
        where += ' AND (created_at < ? OR (created_at = ? AND message_id < ?))'
        params += (anchor[0]['created_at'], anchor[0]['created_at'], args.before)
    messages = reader.rows('projection_thread_messages', where, params, order='created_at DESC, message_id DESC', limit=args.limit + 1)
    result['has_older_messages'] = len(messages) > args.limit
    result['messages'] = list(reversed(messages[:args.limit]))
    for message in result['messages']:
        clip(message, 'text', args.text_limit)
    result['activities'] = list(reversed(reader.rows('projection_thread_activities', 'thread_id=?', (tid,), order='created_at DESC, activity_id DESC', limit=8)))
    for activity in result['activities']:
        clip(activity, 'summary', args.text_limit)
    result['proposed_plans'] = reader.rows('projection_thread_proposed_plans', 'thread_id=?', (tid,), order='updated_at DESC', limit=1)
    for plan in result['proposed_plans']:
        clip(plan, 'plan_markdown', args.text_limit)
    result['pull_requests'] = reader.rows('projection_thread_pull_requests', 'thread_id=?', (tid,))
    for pr in result['pull_requests']:
        clip(pr, 'snapshot_json', args.text_limit)
    if result['latest_turn']:
        clip(result['latest_turn'], 'checkpoint_files_json', args.text_limit)
    return result


def bounded(low, high):
    """Create an argparse integer validator with inclusive limits."""
    def parse(value):
        """Parse an integer or reject an out-of-range CLI argument."""
        number = int(value)
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f'must be between {low} and {high}')
        return number
    return parse


def main():
    """Parse CLI options and emit JSON results or a structured error."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=str(Path.home() / '.t3/userdata/state.sqlite'))
    commands = parser.add_subparsers(dest='command', required=True)
    listing = commands.add_parser('list', help='Search thread metadata; optionally search message text.')
    listing.add_argument('--search', default='')
    listing.add_argument('--messages', action='store_true')
    listing.add_argument('--archived', action='store_true')
    listing.add_argument('--limit', type=bounded(1, 100), default=20)
    listing.add_argument('--offset', type=bounded(0, 1000000), default=0)
    for name in ('show', 'status'):
        command = commands.add_parser(name)
        command.add_argument('thread', help='T3 thread ID, unique prefix, provider thread ID, or URL containing a thread ID.')
        if name == 'show':
            command.add_argument('--limit', type=bounded(1, 100), default=20)
            command.add_argument('--text-limit', type=bounded(100, 50000), default=6000)
            command.add_argument('--before', help='Retrieve messages older than this message ID.')
    args = parser.parse_args()
    reader = None
    try:
        reader = Reader(args.db)
        result = collect(reader, args)
        result['database'] = reader.path
        result['observed_at'] = datetime.now(timezone.utc).isoformat()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (sqlite3.Error, ValueError, OSError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        if reader is not None:
            reader.conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
