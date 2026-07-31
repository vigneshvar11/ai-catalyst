"""
AI CatalyESt — Engineering Systems · Siemens
Backend server using Flask + Flask-SocketIO
"""
import os
import json
import uuid
import random
import string
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_socketio import SocketIO, emit, join_room
from PIL import Image
import io

# ─── App Setup ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder='public', static_url_path='')
app.config['SECRET_KEY'] = 'ai-catalyst-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

DB_PATH = os.path.join(BASE_DIR, 'data', 'db.json')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads', 'avatars')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─── MongoDB Setup (lazy init — deferred until first use) ───
MONGODB_URI = os.environ.get('MONGODB_URI')
COLLECTIONS = ['members', 'events', 'points', 'quizzes', 'surveys', 'teams', 'knowledgeBoard']
_mongo_db = None
_mongo_initialized = False


def _get_mongo():
    """Lazy-init MongoDB connection. Called on first DB access after gevent monkey-patches."""
    global _mongo_db, _mongo_initialized
    if _mongo_initialized:
        return _mongo_db
    _mongo_initialized = True
    if not MONGODB_URI:
        return None
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        client = MongoClient(
            MONGODB_URI,
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        client.admin.command('ping')
        _mongo_db = client['aicatalyst']
        print("[MongoDB] Connected to MongoDB Atlas")

        # Auto-seed: if members collection is empty, load from db.json
        if _mongo_db['members'].count_documents({}) == 0:
            print("[MongoDB] Seeding from db.json...")
            with open(DB_PATH, 'r', encoding='utf-8-sig') as f:
                seed = json.load(f)
            for col in COLLECTIONS:
                docs = seed.get(col, [])
                if docs:
                    to_insert = []
                    for d in docs:
                        doc = dict(d)
                        doc['_id'] = doc.get('id', uuid.uuid4().hex[:8])
                        to_insert.append(doc)
                    _mongo_db[col].insert_many(to_insert)
                    print(f"   {col}: {len(to_insert)} docs")
            cfg = dict(seed.get('config', {}))
            cfg['_id'] = 'app_config'
            _mongo_db['config'].replace_one({'_id': 'app_config'}, cfg, upsert=True)
            print("   config: seeded")
            print("[MongoDB] Seeding complete")
    except Exception as e:
        print(f"[MongoDB] Failed, using db.json fallback: {e}")
        _mongo_db = None
    return _mongo_db


# ─── Database Helpers ───
def _mongo_list(db, collection):
    """Get all docs from a collection, stripping _id."""
    docs = list(db[collection].find())
    for d in docs:
        d.pop('_id', None)
    return docs

def read_db():
    db = _get_mongo()
    if db is not None:
        try:
            data = {}
            for col in COLLECTIONS:
                data[col] = _mongo_list(db, col)
            cfg = db['config'].find_one({'_id': 'app_config'}) or {}
            cfg.pop('_id', None)
            data['config'] = cfg
            return data
        except Exception as e:
            print(f"[MongoDB] read_db error, falling back to db.json: {e}")
    with open(DB_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def write_db(data):
    db = _get_mongo()
    if db is not None:
        try:
            for col in COLLECTIONS:
                db[col].delete_many({})
                docs = data.get(col, [])
                if docs:
                    to_insert = []
                    for d in docs:
                        doc = dict(d)
                        doc['_id'] = doc.get('id', uuid.uuid4().hex[:8])
                        to_insert.append(doc)
                    db[col].insert_many(to_insert)
            cfg = dict(data.get('config', {}))
            cfg['_id'] = 'app_config'
            db['config'].replace_one({'_id': 'app_config'}, cfg, upsert=True)
            return
        except Exception as e:
            print(f"[MongoDB] write_db error, falling back to db.json: {e}")
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def short_id():
    return uuid.uuid4().hex[:8]


# ─── Sides (EngSys / DTS) ───
SIDES = ['engsys', 'dts']

def normalize_side(side):
    return side if side in SIDES else 'engsys'

def filter_by_side(items, side):
    s = normalize_side(side)
    return [it for it in (items or []) if it.get('side', 'engsys') == s]

def _maybe_side(data):
    return normalize_side((data or {}).get('side'))

def migrate_db():
    """Idempotent: tag legacy records as EngSys, ensure knowledgeBoard + DTS config."""
    db = read_db()
    changed = False
    for col in ['members', 'events', 'points', 'quizzes', 'surveys']:
        if not isinstance(db.get(col), list):
            db[col] = []
            changed = True
        for item in db[col]:
            if not item.get('side'):
                item['side'] = 'engsys'
                changed = True
    if not isinstance(db.get('knowledgeBoard'), list):
        db['knowledgeBoard'] = []
        changed = True
    if not isinstance(db.get('teams'), list):
        db['teams'] = []
        changed = True
    cfg = db.setdefault('config', {})
    if not cfg.get('dtsTeamName'):
        cfg['dtsTeamName'] = 'SI EP NA DTS'
        changed = True
    if not cfg.get('engsysTeamName'):
        cfg['engsysTeamName'] = cfg.get('teamName', 'Engineering Systems')
        changed = True
    if changed:
        write_db(db)

# IMPORTANT: do NOT run migrate_db() at import time. Under gunicorn's gevent
# worker, importing the app happens BEFORE monkey.patch_all(); touching the DB
# here would connect PyMongo (spawning real threads/locks) pre-patch and crash
# gevent's _patch_existing_locks. Instead we migrate lazily on the first request,
# which runs after patching is complete.
_migrated = False

@app.before_request
def _run_migration_once():
    global _migrated
    if _migrated:
        return
    _migrated = True
    try:
        migrate_db()
    except Exception as _e:
        print(f"[migrate_db] skipped: {_e}")


# ─── Health Check ───
@app.route('/api/health')
def health():
    db = _get_mongo()
    info = {
        'status': 'ok',
        'mongo': db is not None,
        'mongo_uri_set': MONGODB_URI is not None,
        'initialized': _mongo_initialized,
    }
    if db is not None:
        try:
            for col in COLLECTIONS:
                info[f'count_{col}'] = db[col].count_documents({})
            info['count_config'] = db['config'].count_documents({})
        except Exception as e:
            info['count_error'] = str(e)
    return jsonify(info)

# ─── Static Files ───
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('public/css', path)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('public/js', path)

@app.route('/uploads/avatars/<path:path>')
def send_avatar(path):
    return send_from_directory(UPLOAD_DIR, path)


# ─── AUTH ───
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    db = read_db()
    cfg = db.get('config', {}).get('admin', {})
    # Admin login
    if data.get('username') == cfg.get('username') and data.get('password') == cfg.get('password'):
        return jsonify(success=True, token='ai-catalyst-admin-token', role='admin')
    # EngSys login
    engsys = db.get('config', {}).get('engsys', {'username': 'engsys', 'password': 'engsys'})
    if data.get('username') == engsys.get('username') and data.get('password') == engsys.get('password'):
        return jsonify(success=True, token='ai-catalyst-engsys-token', role='engsys')
    return jsonify(success=False, message='Invalid credentials'), 401


# ─── MEMBERS CRUD ───
@app.route('/api/members', methods=['GET'])
def get_members():
    members = read_db()['members']
    side = request.args.get('side')
    return jsonify(filter_by_side(members, side) if side else members)

@app.route('/api/members', methods=['POST'])
def add_member():
    db = read_db()
    data = request.get_json()
    name = data.get('name', 'New Member')
    member = {
        'id': name.lower().replace(' ', '-').replace('.', ''),
        'name': name,
        'email': data.get('email', ''),
        'role': data.get('role', ''),
        'domain': data.get('domain', 'Cross-Functional'),
        'side': _maybe_side(data),
        'avatar': None,
        'joinedDate': datetime.now().strftime('%Y-%m-%d'),
    }
    # Avoid duplicate IDs
    existing_ids = {m['id'] for m in db['members']}
    if member['id'] in existing_ids:
        member['id'] = member['id'] + '-' + short_id()[:4]
    db['members'].append(member)
    write_db(db)
    return jsonify(member)

@app.route('/api/members/<member_id>', methods=['PUT'])
def update_member(member_id):
    db = read_db()
    data = request.get_json()
    for i, m in enumerate(db['members']):
        if m['id'] == member_id:
            db['members'][i] = {**m, **{k: v for k, v in data.items() if k != 'id'}}
            write_db(db)
            return jsonify(db['members'][i])
    return jsonify(error='Member not found'), 404

@app.route('/api/members/<member_id>', methods=['DELETE'])
def delete_member(member_id):
    db = read_db()
    db['members'] = [m for m in db['members'] if m['id'] != member_id]
    write_db(db)
    return jsonify(success=True)

@app.route('/api/members/<member_id>/avatar', methods=['POST'])
def upload_avatar(member_id):
    if 'avatar' not in request.files:
        return jsonify(error='No file uploaded'), 400
    file = request.files['avatar']
    # Compress image before saving
    try:
        img = Image.open(file.stream)
        img = img.convert('RGB')
        # Resize if larger than 400px on any side
        max_dim = 400
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.LANCZOS)
        filename = f"{member_id}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        img.save(filepath, 'JPEG', quality=80, optimize=True)
    except Exception as e:
        # Fallback: save raw file
        ext = os.path.splitext(file.filename)[1] or '.png'
        filename = f"{member_id}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        file.seek(0)
        file.save(filepath)

    db = read_db()
    for i, m in enumerate(db['members']):
        if m['id'] == member_id:
            db['members'][i]['avatar'] = f"/uploads/avatars/{filename}"
            write_db(db)
            return jsonify(avatar=db['members'][i]['avatar'])
    return jsonify(error='Member not found'), 404


# ─── EVENTS CRUD ───
@app.route('/api/events', methods=['GET'])
def get_events():
    events = read_db()['events']
    side = request.args.get('side')
    return jsonify(filter_by_side(events, side) if side else events)

@app.route('/api/events', methods=['POST'])
def add_event():
    db = read_db()
    data = request.get_json()
    event = {'id': f"event-{short_id()}", **data, 'side': _maybe_side(data)}
    db['events'].append(event)
    write_db(db)
    return jsonify(event)

@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    db = read_db()
    data = request.get_json()
    for i, e in enumerate(db['events']):
        if e['id'] == event_id:
            db['events'][i] = {**e, **{k: v for k, v in data.items() if k != 'id'}}
            write_db(db)
            return jsonify(db['events'][i])
    return jsonify(error='Event not found'), 404

@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    db = read_db()
    db['events'] = [e for e in db['events'] if e['id'] != event_id]
    write_db(db)
    return jsonify(success=True)


# ─── POINTS CRUD ───
@app.route('/api/points', methods=['GET'])
def get_points():
    points = read_db()['points']
    side = request.args.get('side')
    return jsonify(filter_by_side(points, side) if side else points)

@app.route('/api/points', methods=['POST'])
def add_points():
    db = read_db()
    data = request.get_json()
    entry = {'id': f"pts-{short_id()}", **data, 'side': _maybe_side(data), 'date': datetime.now().isoformat()}
    db['points'].append(entry)
    write_db(db)
    return jsonify(entry)

@app.route('/api/points/<point_id>', methods=['PUT'])
def update_points(point_id):
    db = read_db()
    data = request.get_json()
    for i, p in enumerate(db['points']):
        if p['id'] == point_id:
            db['points'][i] = {**p, **{k: v for k, v in data.items() if k != 'id'}}
            write_db(db)
            return jsonify(db['points'][i])
    return jsonify(error='Points entry not found'), 404

@app.route('/api/points/<point_id>', methods=['DELETE'])
def delete_points(point_id):
    db = read_db()
    db['points'] = [p for p in db['points'] if p['id'] != point_id]
    write_db(db)
    return jsonify(success=True)

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    db = read_db()
    side = request.args.get('side')
    members = filter_by_side(db['members'], side) if side else db['members']
    points = filter_by_side(db['points'], side) if side else db['points']
    board = []
    for m in members:
        member_points = [p for p in points if p.get('memberId') == m['id']]
        monthly = {}
        for p in member_points:
            mo = p.get('month', 0)
            monthly[mo] = monthly.get(mo, 0) + p.get('points', 0)
        total = sum(p.get('points', 0) for p in member_points)
        board.append({**m, 'monthlyBreakdown': monthly, 'total': total, 'pointEntries': member_points})
    board.sort(key=lambda x: x['total'], reverse=True)
    return jsonify(board)


# ─── QUIZZES ───
@app.route('/api/quizzes', methods=['GET'])
def get_quizzes():
    quizzes = read_db().get('quizzes', [])
    side = request.args.get('side')
    return jsonify(filter_by_side(quizzes, side) if side else quizzes)

@app.route('/api/quizzes', methods=['POST'])
def create_quiz():
    db = read_db()
    data = request.get_json()
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    qtype = data.get('type') if data.get('type') in ['live', 'self-paced', 'ms-forms'] else 'live'
    quiz = {
        'id': f"quiz-{short_id()}",
        'title': data.get('title', 'Quiz'),
        'month': data.get('month', 1),
        'side': _maybe_side(data),
        'type': qtype,
        'questions': data.get('questions', []),
        'roomCode': room_code,
        'opensAt': data.get('opensAt'),
        'closesAt': data.get('closesAt'),
        'formsUrl': data.get('formsUrl', ''),
        'status': 'waiting',
        'participants': [],
        'responses': [],
        'results': [],
        'createdAt': datetime.now().isoformat(),
    }
    if 'quizzes' not in db:
        db['quizzes'] = []
    db['quizzes'].append(quiz)
    write_db(db)
    return jsonify(quiz)

@app.route('/api/quizzes/<quiz_id>', methods=['PUT'])
def update_quiz(quiz_id):
    db = read_db()
    data = request.get_json()
    for i, q in enumerate(db.get('quizzes', [])):
        if q['id'] == quiz_id:
            db['quizzes'][i] = {**q, **data}
            write_db(db)
            return jsonify(db['quizzes'][i])
    return jsonify(error='Quiz not found'), 404

@app.route('/api/quizzes/<quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    db = read_db()
    db['quizzes'] = [q for q in db.get('quizzes', []) if q['id'] != quiz_id]
    write_db(db)
    return jsonify(success=True)

@app.route('/api/quizzes/<quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    db = read_db()
    data = request.get_json() or {}
    quiz = next((q for q in db.get('quizzes', []) if q['id'] == quiz_id), None)
    if not quiz:
        return jsonify(error='Quiz not found'), 404
    now = datetime.now()
    if quiz.get('opensAt'):
        try:
            if now < datetime.fromisoformat(quiz['opensAt'].replace('Z', '+00:00')).replace(tzinfo=None):
                return jsonify(error='This quiz has not opened yet.'), 403
        except Exception:
            pass
    if quiz.get('closesAt'):
        try:
            if now > datetime.fromisoformat(quiz['closesAt'].replace('Z', '+00:00')).replace(tzinfo=None):
                return jsonify(error='This quiz has closed.'), 403
        except Exception:
            pass
    name = (data.get('name') or '').strip() or 'Anonymous'
    answers = data.get('answers', {})
    score = 0
    review = []
    for q in quiz.get('questions', []):
        given = answers.get(q['id'])
        is_correct = given == q.get('correctAnswer')
        if is_correct:
            score += 1
        review.append({
            'id': q['id'],
            'question': q.get('question', ''),
            'options': q.get('options', {}),
            'yourAnswer': given,
            'correctAnswer': q.get('correctAnswer'),
            'explanation': q.get('explanation', ''),
            'isCorrect': is_correct,
        })
    total = len(quiz.get('questions', []))
    for i, q in enumerate(db['quizzes']):
        if q['id'] == quiz_id:
            db['quizzes'][i].setdefault('responses', []).append({
                'name': name, 'answers': answers, 'score': score,
                'total': total, 'submittedAt': now.isoformat(),
            })
            break
    write_db(db)
    return jsonify(name=name, score=score, total=total, review=review)

@app.route('/api/quizzes/<quiz_id>/answers', methods=['GET'])
def quiz_answers(quiz_id):
    db = read_db()
    quiz = next((q for q in db.get('quizzes', []) if q['id'] == quiz_id), None)
    if not quiz:
        return jsonify(error='Quiz not found'), 404
    review = [{
        'id': q['id'],
        'question': q.get('question', ''),
        'options': q.get('options', {}),
        'correctAnswer': q.get('correctAnswer'),
        'explanation': q.get('explanation', ''),
    } for q in quiz.get('questions', [])]
    return jsonify(title=quiz.get('title', ''), review=review)


# ─── KNOWLEDGE BOARD (shared) ───
@app.route('/api/knowledge', methods=['GET'])
def get_knowledge():
    items = read_db().get('knowledgeBoard', [])
    return jsonify(sorted(items, key=lambda x: x.get('order', 0)))

@app.route('/api/knowledge', methods=['POST'])
def add_knowledge():
    db = read_db()
    data = request.get_json() or {}
    if 'knowledgeBoard' not in db:
        db['knowledgeBoard'] = []
    item = {
        'id': f"kb-{short_id()}",
        'label': data.get('label', 'Untitled'),
        'url': data.get('url', '#'),
        'icon': data.get('icon', 'ri-links-line'),
        'category': data.get('category', 'Resources'),
        'order': data.get('order', len(db['knowledgeBoard'])),
    }
    db['knowledgeBoard'].append(item)
    write_db(db)
    return jsonify(item)

@app.route('/api/knowledge/<item_id>', methods=['PUT'])
def update_knowledge(item_id):
    db = read_db()
    data = request.get_json() or {}
    for i, k in enumerate(db.get('knowledgeBoard', [])):
        if k['id'] == item_id:
            db['knowledgeBoard'][i] = {**k, **{kk: vv for kk, vv in data.items() if kk != 'id'}}
            write_db(db)
            return jsonify(db['knowledgeBoard'][i])
    return jsonify(error='Item not found'), 404

@app.route('/api/knowledge/<item_id>', methods=['DELETE'])
def delete_knowledge(item_id):
    db = read_db()
    db['knowledgeBoard'] = [k for k in db.get('knowledgeBoard', []) if k['id'] != item_id]
    write_db(db)
    return jsonify(success=True)


# ─── SURVEYS ───
@app.route('/api/surveys', methods=['GET'])
def get_surveys():
    surveys = read_db().get('surveys', [])
    side = request.args.get('side')
    return jsonify(filter_by_side(surveys, side) if side else surveys)

@app.route('/api/surveys', methods=['POST'])
def create_survey():
    db = read_db()
    data = request.get_json()
    survey = {
        'id': f"survey-{short_id()}",
        'presenterId': data.get('presenterId', ''),
        'month': data.get('month', 1),
        'side': _maybe_side(data),
        'topic': data.get('topic', ''),
        'status': 'active',
        'votes': [],
        'createdAt': datetime.now().isoformat(),
    }
    if 'surveys' not in db:
        db['surveys'] = []
    db['surveys'].append(survey)
    write_db(db)
    socketio.emit('survey:started', survey)
    return jsonify(survey)

@app.route('/api/surveys/<survey_id>/vote', methods=['POST'])
def vote_survey(survey_id):
    db = read_db()
    data = request.get_json()
    for i, s in enumerate(db.get('surveys', [])):
        if s['id'] == survey_id:
            s['votes'].append({'rating': data.get('rating', 3), 'timestamp': datetime.now().isoformat()})
            write_db(db)
            avg = sum(v['rating'] for v in s['votes']) / len(s['votes'])
            socketio.emit('survey:voteReceived', {
                'surveyId': survey_id,
                'totalVotes': len(s['votes']),
                'average': round(avg, 1),
            })
            return jsonify(success=True)
    return jsonify(error='Survey not found'), 404

@app.route('/api/surveys/<survey_id>/close', methods=['PUT'])
def close_survey(survey_id):
    db = read_db()
    for i, s in enumerate(db.get('surveys', [])):
        if s['id'] == survey_id:
            db['surveys'][i]['status'] = 'closed'
            write_db(db)
            socketio.emit('survey:ended', {'surveyId': survey_id})
            return jsonify(db['surveys'][i])
    return jsonify(error='Survey not found'), 404


# ─── TEAMS ───
@app.route('/api/teams', methods=['GET'])
def get_teams():
    return jsonify(read_db().get('teams', []))

@app.route('/api/teams', methods=['POST'])
def create_team():
    db = read_db()
    data = request.get_json()
    if 'teams' not in db:
        db['teams'] = []
    team = {'id': f"team-{short_id()}", **data}
    db['teams'].append(team)
    write_db(db)
    return jsonify(team)

@app.route('/api/teams/<team_id>', methods=['DELETE'])
def delete_team(team_id):
    db = read_db()
    db['teams'] = [t for t in db.get('teams', []) if t['id'] != team_id]
    write_db(db)
    return jsonify(success=True)


# ═══════════════════════════════════════════════════════════
# SOCKET.IO — Real-time Quiz & Survey
# ═══════════════════════════════════════════════════════════
active_quiz_rooms = {}  # roomCode -> room state


@socketio.on('connect')
def on_connect():
    print(f"⚡ Client connected: {request.sid}")


@socketio.on('quiz:create')
def on_quiz_create(data):
    quiz_id = data.get('quizId')
    room_code = data.get('roomCode')
    active_quiz_rooms[room_code] = {
        'quizId': quiz_id,
        'roomCode': room_code,
        'adminSid': request.sid,
        'participants': {},
        'started': False,
    }
    join_room(room_code)
    emit('quiz:roomCreated', {'roomCode': room_code})


@socketio.on('quiz:join')
def on_quiz_join(data):
    room_code = data.get('roomCode')
    member_id = data.get('memberId')
    member_name = data.get('memberName')
    room = active_quiz_rooms.get(room_code)
    if not room:
        emit('quiz:error', {'message': 'Room not found'})
        return
    if room['started']:
        emit('quiz:error', {'message': 'Quiz already started'})
        return

    room['participants'][request.sid] = {
        'memberId': member_id,
        'memberName': member_name,
        'socketId': request.sid,
        'answers': [],
        'tabSwitches': 0,
        'score': 0,
        'finished': False,
    }
    join_room(room_code)
    participants_list = [{'memberId': p['memberId'], 'memberName': p['memberName']}
                         for p in room['participants'].values()]
    socketio.emit('quiz:participantJoined', {'participants': participants_list}, room=room_code)


@socketio.on('quiz:start')
def on_quiz_start(data):
    room_code = data.get('roomCode')
    room = active_quiz_rooms.get(room_code)
    if not room:
        return
    room['started'] = True

    db = read_db()
    quiz = next((q for q in db.get('quizzes', []) if q['id'] == room['quizId']), None)
    if not quiz:
        return

    for sid, p in room['participants'].items():
        shuffled = list(quiz['questions'])
        random.shuffle(shuffled)
        questions_for_client = [{
            'index': i,
            'id': q['id'],
            'question': q['question'],
            'options': q['options'],
            'timeLimit': q.get('timeLimit', 30),
        } for i, q in enumerate(shuffled)]
        socketio.emit('quiz:started', {
            'questions': questions_for_client,
            'totalQuestions': len(shuffled),
        }, room=sid)

    emit('quiz:adminStarted', {'participantCount': len(room['participants'])})


@socketio.on('quiz:answer')
def on_quiz_answer(data):
    room_code = data.get('roomCode')
    question_id = data.get('questionId')
    answer = data.get('answer')
    room = active_quiz_rooms.get(room_code)
    if not room or request.sid not in room['participants']:
        return

    db = read_db()
    quiz = next((q for q in db.get('quizzes', []) if q['id'] == room['quizId']), None)
    if not quiz:
        return

    question = next((q for q in quiz['questions'] if q['id'] == question_id), None)
    is_correct = question and question.get('correctAnswer') == answer

    p = room['participants'][request.sid]
    p['answers'].append({'questionId': question_id, 'answer': answer, 'isCorrect': is_correct})
    if is_correct:
        p['score'] += 1

    emit('quiz:answerResult', {
        'questionId': question_id,
        'isCorrect': is_correct,
        'correctAnswer': question.get('correctAnswer') if question else None,
    })


@socketio.on('quiz:tabSwitch')
def on_quiz_tab_switch(data):
    room_code = data.get('roomCode')
    room = active_quiz_rooms.get(room_code)
    if not room or request.sid not in room['participants']:
        return

    p = room['participants'][request.sid]
    p['tabSwitches'] += 1
    emit('quiz:tabSwitchPenalty', {'totalSwitches': p['tabSwitches']})
    socketio.emit('quiz:participantTabSwitch', {
        'memberName': p['memberName'],
        'totalSwitches': p['tabSwitches'],
    }, room=room.get('adminSid'))


@socketio.on('quiz:finished')
def on_quiz_finished(data):
    room_code = data.get('roomCode')
    room = active_quiz_rooms.get(room_code)
    if not room or request.sid not in room['participants']:
        return

    p = room['participants'][request.sid]
    p['finished'] = True
    final_score = max(0, p['score'] - p['tabSwitches'])

    emit('quiz:yourResult', {
        'score': p['score'],
        'tabSwitches': p['tabSwitches'],
        'penalty': p['tabSwitches'],
        'finalScore': final_score,
    })

    all_results = [{
        'memberId': pt['memberId'],
        'memberName': pt['memberName'],
        'score': pt['score'],
        'tabSwitches': pt['tabSwitches'],
        'finalScore': max(0, pt['score'] - pt['tabSwitches']),
        'finished': pt['finished'],
    } for pt in room['participants'].values()]

    socketio.emit('quiz:liveResults', {'results': all_results}, room=room.get('adminSid'))


@socketio.on('quiz:end')
def on_quiz_end(data):
    room_code = data.get('roomCode')
    room = active_quiz_rooms.get(room_code)
    if not room:
        return

    final_results = [{
        'memberId': p['memberId'],
        'memberName': p['memberName'],
        'score': p['score'],
        'tabSwitches': p['tabSwitches'],
        'finalScore': max(0, p['score'] - p['tabSwitches']),
        'answers': p['answers'],
    } for p in room['participants'].values()]

    socketio.emit('quiz:ended', {'results': final_results}, room=room_code)

    # Save results
    db = read_db()
    for i, q in enumerate(db.get('quizzes', [])):
        if q['id'] == room['quizId']:
            db['quizzes'][i]['status'] = 'completed'
            db['quizzes'][i]['results'] = final_results
            write_db(db)
            break

    del active_quiz_rooms[room_code]


@socketio.on('disconnect')
def on_disconnect():
    for room_code, room in list(active_quiz_rooms.items()):
        if request.sid in room['participants']:
            p = room['participants'][request.sid]
            socketio.emit('quiz:participantLeft', {'memberName': p['memberName']},
                          room=room.get('adminSid'))
            del room['participants'][request.sid]


# ─── Fallback to SPA ───
@app.route('/<path:path>')
def catch_all(path):
    # Try static file first
    static_path = os.path.join(app.static_folder, path)
    if os.path.isfile(static_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory('public', 'index.html')


# ─── Start ───
if __name__ == '__main__':
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║                                          ║")
    print("  ║   🚀 AI CatalyESt Dashboard                ║")
    print("  ║   Engineering Systems · Siemens           ║")
    print("  ║                                          ║")
    print("  ║   → http://localhost:3000                ║")
    print("  ║                                          ║")
    print("  ╚══════════════════════════════════════════╝")
    print()
    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('RENDER') is None  # disable debug in production
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
