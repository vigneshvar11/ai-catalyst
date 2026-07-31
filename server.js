const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

const app = express();
const server = http.createServer(app);
const io = new Server(server);
const PORT = process.env.PORT || 3000;

// ─── Middleware ───
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// ─── Database helper ───
const DB_PATH = path.join(__dirname, 'data', 'db.json');

function readDB() {
  // Be tolerant of UTF-8 BOM so manual/scripted file writes never break parsing.
  const raw = fs.readFileSync(DB_PATH, 'utf-8').replace(/^\uFEFF/, '');
  return JSON.parse(raw);
}

function writeDB(data) {
  fs.writeFileSync(DB_PATH, JSON.stringify(data, null, 2));
}

// ─── Sides (EngSys / DTS) ───
const SIDES = ['engsys', 'dts'];
function normalizeSide(side) {
  return SIDES.includes(side) ? side : 'engsys';
}

// Return only records belonging to the requested side. Records without a `side`
// field are treated as EngSys (the original single-team data).
function filterBySide(list, side) {
  const s = normalizeSide(side);
  return (list || []).filter(item => (item.side || 'engsys') === s);
}

// One-time, idempotent migration: tag legacy records as EngSys, ensure the
// shared knowledge board exists, and add DTS metadata to config.
function migrateDB() {
  const db = readDB();
  let changed = false;

  ['members', 'events', 'points', 'quizzes', 'surveys'].forEach(col => {
    if (!Array.isArray(db[col])) { db[col] = []; changed = true; }
    db[col].forEach(item => {
      if (!item.side) { item.side = 'engsys'; changed = true; }
    });
  });

  if (!Array.isArray(db.knowledgeBoard)) { db.knowledgeBoard = []; changed = true; }
  if (!Array.isArray(db.teams)) { db.teams = []; changed = true; }

  db.config = db.config || {};
  if (!db.config.dtsTeamName) { db.config.dtsTeamName = 'SI EP NA DTS'; changed = true; }
  if (!db.config.engsysTeamName) { db.config.engsysTeamName = db.config.teamName || 'Engineering Systems'; changed = true; }

  if (changed) writeDB(db);
}
migrateDB();

// Ensure upload directories exist
const uploadDir = path.join(__dirname, 'uploads', 'avatars');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// ─── Multer config for avatar uploads ───
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    const memberId = req.params.id;
    cb(null, `${memberId}${ext}`);
  }
});
const upload = multer({ storage, limits: { fileSize: 5 * 1024 * 1024 } });

// ─── AUTH ───
app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;
  const db = readDB();
  // Admin login
  if (username === db.config.admin.username && password === db.config.admin.password) {
    return res.json({ success: true, token: 'ai-catalyst-admin-token', role: 'admin' });
  }
  // EngSys login
  const engsys = db.config.engsys || { username: 'engsys', password: 'engsys' };
  if (username === engsys.username && password === engsys.password) {
    return res.json({ success: true, token: 'ai-catalyst-engsys-token', role: 'engsys' });
  }
  res.status(401).json({ success: false, message: 'Invalid credentials' });
});

// ─── MEMBERS CRUD ───
app.get('/api/members', (req, res) => {
  const db = readDB();
  res.json(req.query.side ? filterBySide(db.members, req.query.side) : db.members);
});

app.post('/api/members', (req, res) => {
  const db = readDB();
  const member = {
    id: req.body.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+$/, ''),
    name: req.body.name,
    email: req.body.email || '',
    role: req.body.role || '',
    domain: req.body.domain || 'Cross-Functional',
    side: normalizeSide(req.body.side),
    avatar: null,
    joinedDate: new Date().toISOString().split('T')[0]
  };
  db.members.push(member);
  writeDB(db);
  res.json(member);
});

app.put('/api/members/:id', (req, res) => {
  const db = readDB();
  const idx = db.members.findIndex(m => m.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Member not found' });
  db.members[idx] = { ...db.members[idx], ...req.body };
  writeDB(db);
  res.json(db.members[idx]);
});

app.delete('/api/members/:id', (req, res) => {
  const db = readDB();
  db.members = db.members.filter(m => m.id !== req.params.id);
  writeDB(db);
  res.json({ success: true });
});

app.post('/api/members/:id/avatar', upload.single('avatar'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });
  const db = readDB();
  const idx = db.members.findIndex(m => m.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Member not found' });
  db.members[idx].avatar = `/uploads/avatars/${req.file.filename}`;
  writeDB(db);
  res.json({ avatar: db.members[idx].avatar });
});

// ─── EVENTS CRUD ───
app.get('/api/events', (req, res) => {
  const db = readDB();
  res.json(req.query.side ? filterBySide(db.events, req.query.side) : db.events);
});

app.post('/api/events', (req, res) => {
  const db = readDB();
  const event = { id: `event-${uuidv4().slice(0, 8)}`, ...req.body, side: normalizeSide(req.body.side) };
  db.events.push(event);
  writeDB(db);
  res.json(event);
});

app.put('/api/events/:id', (req, res) => {
  const db = readDB();
  const idx = db.events.findIndex(e => e.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Event not found' });
  db.events[idx] = { ...db.events[idx], ...req.body };
  writeDB(db);
  res.json(db.events[idx]);
});

app.delete('/api/events/:id', (req, res) => {
  const db = readDB();
  db.events = db.events.filter(e => e.id !== req.params.id);
  writeDB(db);
  res.json({ success: true });
});

// ─── POINTS CRUD ───
app.get('/api/points', (req, res) => {
  const db = readDB();
  res.json(req.query.side ? filterBySide(db.points, req.query.side) : db.points);
});

app.post('/api/points', (req, res) => {
  const db = readDB();
  const entry = { id: `pts-${uuidv4().slice(0, 8)}`, ...req.body, side: normalizeSide(req.body.side), date: new Date().toISOString() };
  db.points.push(entry);
  writeDB(db);
  res.json(entry);
});

app.put('/api/points/:id', (req, res) => {
  const db = readDB();
  const idx = db.points.findIndex(p => p.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Points entry not found' });
  db.points[idx] = { ...db.points[idx], ...req.body };
  writeDB(db);
  res.json(db.points[idx]);
});

app.delete('/api/points/:id', (req, res) => {
  const db = readDB();
  db.points = db.points.filter(p => p.id !== req.params.id);
  writeDB(db);
  res.json({ success: true });
});

app.get('/api/leaderboard', (req, res) => {
  const db = readDB();
  const members = req.query.side ? filterBySide(db.members, req.query.side) : db.members;
  const points = req.query.side ? filterBySide(db.points, req.query.side) : db.points;
  const board = members.map(m => {
    const memberPoints = points.filter(p => p.memberId === m.id);
    const monthlyBreakdown = {};
    memberPoints.forEach(p => {
      if (!monthlyBreakdown[p.month]) monthlyBreakdown[p.month] = 0;
      monthlyBreakdown[p.month] += p.points;
    });
    const total = memberPoints.reduce((sum, p) => sum + p.points, 0);
    return { ...m, monthlyBreakdown, total, pointEntries: memberPoints };
  });
  board.sort((a, b) => b.total - a.total);
  res.json(board);
});

// ─── QUIZZES ───
app.get('/api/quizzes', (req, res) => {
  const db = readDB();
  res.json(req.query.side ? filterBySide(db.quizzes, req.query.side) : db.quizzes);
});

app.post('/api/quizzes', (req, res) => {
  const db = readDB();
  const type = ['live', 'self-paced', 'ms-forms'].includes(req.body.type) ? req.body.type : 'live';
  const quiz = {
    id: `quiz-${uuidv4().slice(0, 8)}`,
    title: req.body.title,
    month: req.body.month,
    side: normalizeSide(req.body.side),
    type,
    questions: req.body.questions || [],
    // Live only
    roomCode: Math.random().toString(36).substring(2, 8).toUpperCase(),
    // Self-paced scheduling window (ISO strings, optional)
    opensAt: req.body.opensAt || null,
    closesAt: req.body.closesAt || null,
    // MS Forms link (ms-forms type only)
    formsUrl: req.body.formsUrl || '',
    status: 'waiting',
    participants: [],
    responses: [],
    results: [],
    createdAt: new Date().toISOString()
  };
  db.quizzes.push(quiz);
  writeDB(db);
  res.json(quiz);
});

app.put('/api/quizzes/:id', (req, res) => {
  const db = readDB();
  const idx = db.quizzes.findIndex(q => q.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Quiz not found' });
  db.quizzes[idx] = { ...db.quizzes[idx], ...req.body };
  writeDB(db);
  res.json(db.quizzes[idx]);
});

app.delete('/api/quizzes/:id', (req, res) => {
  const db = readDB();
  db.quizzes = db.quizzes.filter(q => q.id !== req.params.id);
  writeDB(db);
  res.json({ success: true });
});

// Self-paced quiz submission — grades answers and returns a Udemy-style review.
app.post('/api/quizzes/:id/submit', (req, res) => {
  const db = readDB();
  const quiz = db.quizzes.find(q => q.id === req.params.id);
  if (!quiz) return res.status(404).json({ error: 'Quiz not found' });

  // Enforce open window if scheduled.
  const now = Date.now();
  if (quiz.opensAt && now < new Date(quiz.opensAt).getTime()) {
    return res.status(403).json({ error: 'This quiz has not opened yet.' });
  }
  if (quiz.closesAt && now > new Date(quiz.closesAt).getTime()) {
    return res.status(403).json({ error: 'This quiz has closed.' });
  }

  const name = (req.body.name || '').trim() || 'Anonymous';
  const answers = req.body.answers || {}; // { [questionId]: answer }

  let score = 0;
  const review = quiz.questions.map(q => {
    const given = answers[q.id];
    const isCorrect = given === q.correctAnswer;
    if (isCorrect) score++;
    return {
      id: q.id,
      question: q.question,
      options: q.options,
      yourAnswer: given ?? null,
      correctAnswer: q.correctAnswer,
      explanation: q.explanation || '',
      isCorrect
    };
  });

  const total = quiz.questions.length;
  const response = { name, answers, score, total, submittedAt: new Date().toISOString() };
  const qIdx = db.quizzes.findIndex(q => q.id === req.params.id);
  if (!Array.isArray(db.quizzes[qIdx].responses)) db.quizzes[qIdx].responses = [];
  db.quizzes[qIdx].responses.push(response);
  writeDB(db);

  res.json({ name, score, total, review });
});

// Reveal answers for an MS-Forms quiz (called after "Mark as complete").
app.get('/api/quizzes/:id/answers', (req, res) => {
  const db = readDB();
  const quiz = db.quizzes.find(q => q.id === req.params.id);
  if (!quiz) return res.status(404).json({ error: 'Quiz not found' });
  const review = quiz.questions.map(q => ({
    id: q.id,
    question: q.question,
    options: q.options,
    correctAnswer: q.correctAnswer,
    explanation: q.explanation || ''
  }));
  res.json({ title: quiz.title, review });
});

// ─── KNOWLEDGE BOARD (shared across both sides) ───
app.get('/api/knowledge', (req, res) => {
  const db = readDB();
  const list = [...(db.knowledgeBoard || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
  res.json(list);
});

app.post('/api/knowledge', (req, res) => {
  const db = readDB();
  if (!Array.isArray(db.knowledgeBoard)) db.knowledgeBoard = [];
  const item = {
    id: `kb-${uuidv4().slice(0, 8)}`,
    label: req.body.label || 'Untitled',
    url: req.body.url || '#',
    icon: req.body.icon || 'ri-links-line',
    category: req.body.category || 'Resources',
    order: typeof req.body.order === 'number' ? req.body.order : db.knowledgeBoard.length
  };
  db.knowledgeBoard.push(item);
  writeDB(db);
  res.json(item);
});

app.put('/api/knowledge/:id', (req, res) => {
  const db = readDB();
  const idx = (db.knowledgeBoard || []).findIndex(k => k.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Item not found' });
  db.knowledgeBoard[idx] = { ...db.knowledgeBoard[idx], ...req.body };
  writeDB(db);
  res.json(db.knowledgeBoard[idx]);
});

app.delete('/api/knowledge/:id', (req, res) => {
  const db = readDB();
  db.knowledgeBoard = (db.knowledgeBoard || []).filter(k => k.id !== req.params.id);
  writeDB(db);
  res.json({ success: true });
});

// ─── SURVEYS ───
app.get('/api/surveys', (req, res) => {
  const db = readDB();
  res.json(req.query.side ? filterBySide(db.surveys, req.query.side) : db.surveys);
});

app.post('/api/surveys', (req, res) => {
  const db = readDB();
  const survey = {
    id: `survey-${uuidv4().slice(0, 8)}`,
    presenterId: req.body.presenterId,
    month: req.body.month,
    side: normalizeSide(req.body.side),
    topic: req.body.topic || '',
    status: 'active',
    votes: [],
    createdAt: new Date().toISOString()
  };
  db.surveys.push(survey);
  writeDB(db);
  io.emit('survey:started', survey);
  res.json(survey);
});

app.post('/api/surveys/:id/vote', (req, res) => {
  const db = readDB();
  const idx = db.surveys.findIndex(s => s.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Survey not found' });
  db.surveys[idx].votes.push({
    rating: req.body.rating,
    timestamp: new Date().toISOString()
  });
  writeDB(db);
  io.emit('survey:voteReceived', {
    surveyId: req.params.id,
    totalVotes: db.surveys[idx].votes.length,
    average: (db.surveys[idx].votes.reduce((s, v) => s + v.rating, 0) / db.surveys[idx].votes.length).toFixed(1)
  });
  res.json({ success: true });
});

app.put('/api/surveys/:id/close', (req, res) => {
  const db = readDB();
  const idx = db.surveys.findIndex(s => s.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Survey not found' });
  db.surveys[idx].status = 'closed';
  writeDB(db);
  io.emit('survey:ended', { surveyId: req.params.id });
  res.json(db.surveys[idx]);
});

// ─── TEAMS ───
app.get('/api/teams', (req, res) => {
  const db = readDB();
  res.json(db.teams || []);
});

app.post('/api/teams', (req, res) => {
  const db = readDB();
  if (!db.teams) db.teams = [];
  const team = { id: `team-${uuidv4().slice(0, 8)}`, ...req.body };
  db.teams.push(team);
  writeDB(db);
  res.json(team);
});

app.delete('/api/teams/:id', (req, res) => {
  const db = readDB();
  db.teams = (db.teams || []).filter(t => t.id !== req.params.id);
  writeDB(db);
  res.json({ success: true });
});

// ─── SOCKET.IO — Real-time Quiz & Survey ───
const activeQuizRooms = {};

io.on('connection', (socket) => {
  console.log(`⚡ Client connected: ${socket.id}`);

  // ── Quiz: Admin creates a room ──
  socket.on('quiz:create', (data) => {
    const { quizId, roomCode } = data;
    activeQuizRooms[roomCode] = {
      quizId,
      roomCode,
      adminSocket: socket.id,
      participants: {},
      started: false
    };
    socket.join(roomCode);
    socket.emit('quiz:roomCreated', { roomCode });
  });

  // ── Quiz: Participant joins ──
  socket.on('quiz:join', (data) => {
    const { roomCode, memberId, memberName } = data;
    const room = activeQuizRooms[roomCode];
    if (!room) return socket.emit('quiz:error', { message: 'Room not found' });
    if (room.started) return socket.emit('quiz:error', { message: 'Quiz already started' });

    room.participants[socket.id] = {
      memberId, memberName, socketId: socket.id,
      answers: [], tabSwitches: 0, score: 0, finished: false
    };
    socket.join(roomCode);
    io.to(roomCode).emit('quiz:participantJoined', {
      participants: Object.values(room.participants).map(p => ({
        memberId: p.memberId, memberName: p.memberName
      }))
    });
  });

  // ── Quiz: Admin starts ──
  socket.on('quiz:start', (data) => {
    const { roomCode } = data;
    const room = activeQuizRooms[roomCode];
    if (!room) return;
    room.started = true;

    const db = readDB();
    const quiz = db.quizzes.find(q => q.id === room.quizId);
    if (!quiz) return;

    // Send shuffled questions to each participant
    Object.values(room.participants).forEach(p => {
      const shuffled = [...quiz.questions].sort(() => Math.random() - 0.5);
      io.to(p.socketId).emit('quiz:started', {
        questions: shuffled.map((q, i) => ({
          index: i,
          id: q.id,
          question: q.question,
          options: q.options,
          timeLimit: q.timeLimit || 30
        })),
        totalQuestions: shuffled.length
      });
    });

    // Notify admin
    socket.emit('quiz:adminStarted', { participantCount: Object.keys(room.participants).length });
  });

  // ── Quiz: Participant answers ──
  socket.on('quiz:answer', (data) => {
    const { roomCode, questionId, answer, timeTaken } = data;
    const room = activeQuizRooms[roomCode];
    if (!room || !room.participants[socket.id]) return;

    const db = readDB();
    const quiz = db.quizzes.find(q => q.id === room.quizId);
    if (!quiz) return;

    const question = quiz.questions.find(q => q.id === questionId);
    const isCorrect = question && question.correctAnswer === answer;

    room.participants[socket.id].answers.push({
      questionId, answer, isCorrect, timeTaken
    });

    if (isCorrect) room.participants[socket.id].score++;

    socket.emit('quiz:answerResult', { questionId, isCorrect, correctAnswer: question?.correctAnswer });
  });

  // ── Quiz: Tab switch detected ──
  socket.on('quiz:tabSwitch', (data) => {
    const { roomCode } = data;
    const room = activeQuizRooms[roomCode];
    if (!room || !room.participants[socket.id]) return;

    room.participants[socket.id].tabSwitches++;
    socket.emit('quiz:tabSwitchPenalty', {
      totalSwitches: room.participants[socket.id].tabSwitches
    });

    // Notify admin
    io.to(room.adminSocket).emit('quiz:participantTabSwitch', {
      memberName: room.participants[socket.id].memberName,
      totalSwitches: room.participants[socket.id].tabSwitches
    });
  });

  // ── Quiz: Participant finished ──
  socket.on('quiz:finished', (data) => {
    const { roomCode } = data;
    const room = activeQuizRooms[roomCode];
    if (!room || !room.participants[socket.id]) return;

    const p = room.participants[socket.id];
    p.finished = true;
    const finalScore = Math.max(0, p.score - p.tabSwitches);

    socket.emit('quiz:yourResult', {
      score: p.score,
      tabSwitches: p.tabSwitches,
      penalty: p.tabSwitches,
      finalScore
    });

    // Send results to admin
    const allResults = Object.values(room.participants).map(pt => ({
      memberId: pt.memberId,
      memberName: pt.memberName,
      score: pt.score,
      tabSwitches: pt.tabSwitches,
      finalScore: Math.max(0, pt.score - pt.tabSwitches),
      finished: pt.finished
    }));

    io.to(room.adminSocket).emit('quiz:liveResults', { results: allResults });
  });

  // ── Quiz: Admin ends ──
  socket.on('quiz:end', (data) => {
    const { roomCode } = data;
    const room = activeQuizRooms[roomCode];
    if (!room) return;

    const finalResults = Object.values(room.participants).map(p => ({
      memberId: p.memberId,
      memberName: p.memberName,
      score: p.score,
      tabSwitches: p.tabSwitches,
      finalScore: Math.max(0, p.score - p.tabSwitches),
      answers: p.answers
    }));

    io.to(roomCode).emit('quiz:ended', { results: finalResults });

    // Save results to DB
    const db = readDB();
    const qIdx = db.quizzes.findIndex(q => q.id === room.quizId);
    if (qIdx !== -1) {
      db.quizzes[qIdx].status = 'completed';
      db.quizzes[qIdx].results = finalResults;
      writeDB(db);
    }

    delete activeQuizRooms[roomCode];
  });

  socket.on('disconnect', () => {
    // Clean up participant from quiz rooms
    Object.values(activeQuizRooms).forEach(room => {
      if (room.participants[socket.id]) {
        const p = room.participants[socket.id];
        io.to(room.adminSocket).emit('quiz:participantLeft', {
          memberName: p.memberName
        });
        delete room.participants[socket.id];
      }
    });
  });
});

// ─── Fallback to SPA ───
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ─── Start server ───
server.listen(PORT, () => {
  console.log(`\n  ╔══════════════════════════════════════════╗`);
  console.log(`  ║                                          ║`);
  console.log(`  ║   🚀 AI CatalyESt Dashboard                ║`);
  console.log(`  ║   Engineering Systems · Siemens           ║`);
  console.log(`  ║                                          ║`);
  console.log(`  ║   → http://localhost:${PORT}                ║`);
  console.log(`  ║                                          ║`);
  console.log(`  ╚══════════════════════════════════════════╝\n`);
});
