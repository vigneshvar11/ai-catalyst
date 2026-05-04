/* ═══════════════════════════════════════════════════════════
   AI CatalyESt — Frontend Application
   ═══════════════════════════════════════════════════════════ */

// ════════════════════ STATE ════════════════════
const state = {
  isAdmin: false,
  isEngSys: false,
  currentTab: 'dashboard',
  members: [],
  events: [],
  points: [],
  leaderboard: [],
  quizzes: [],
  surveys: [],
  socket: null,
  quizState: null,       // participant quiz state
  adminQuizState: null,  // admin quiz room state
  selectedMonth: 1,
};

// ════════════════════ INIT ════════════════════
document.addEventListener('DOMContentLoaded', async () => {
  showLoader('Connecting to server...');
  try {
    await loadAllData();
    state.socket = io({ reconnection: true, reconnectionAttempts: 10, reconnectionDelay: 1000 });
    setupNavigation();
    setupAuth();
    setupSocketListeners();
    renderCurrentTab();
    startCountdown();
    checkForActiveSurvey();
    hideLoader();
  } catch (e) {
    console.error('Init failed:', e);
    showLoader('Server is waking up... retrying', true);
    // Auto-retry after 5s
    setTimeout(() => location.reload(), 5000);
  }

  // Easter egg: type "aicatalyst" anywhere
  let easterBuf = '';
  document.addEventListener('keypress', e => {
    easterBuf += e.key;
    if (easterBuf.includes('aicatalyst')) {
      easterBuf = '';
      document.body.style.transition = '1s';
      document.querySelector('.hero-text h1').innerHTML = '🤖 You found the <span class="gradient-text">secret</span>!';
      toast('🎉 Easter egg unlocked! You truly AI CatalyESt.', 'success');
      setTimeout(() => location.reload(), 3000);
    }
    if (easterBuf.length > 20) easterBuf = easterBuf.slice(-20);
  });
});

// ════════════════════ LOADER ════════════════════
function showLoader(msg, showRetry = false) {
  const el = document.getElementById('app-loader');
  if (!el) return;
  el.classList.remove('hidden');
  document.getElementById('loader-text').textContent = msg;
  document.getElementById('loader-retry').style.display = showRetry ? 'inline-block' : 'none';
}
function hideLoader() {
  const el = document.getElementById('app-loader');
  if (!el) return;
  el.classList.add('hidden');
  setTimeout(() => el.remove(), 500);
}

// ════════════════════ DATA LOADING ════════════════════
async function loadAllData() {
  const [members, events, points, leaderboard, quizzes, surveys] = await Promise.all([
    api('/api/members'),
    api('/api/events'),
    api('/api/points'),
    api('/api/leaderboard'),
    api('/api/quizzes'),
    api('/api/surveys'),
  ]);
  // Validate we got real data (not all empty from cold-start failures)
  if (!members.length && !events.length) {
    throw new Error('No data returned — server may still be starting');
  }
  state.members = members;
  state.events = events.sort((a, b) => a.month - b.month);
  state.points = points;
  state.leaderboard = leaderboard;
  state.quizzes = quizzes;
  state.surveys = surveys;
}

async function api(url, options = {}) {
  const maxRetries = 3;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn(`API ${url} attempt ${attempt + 1}/${maxRetries}:`, e.message);
      if (attempt < maxRetries - 1) {
        await new Promise(r => setTimeout(r, 1000 * (attempt + 1))); // 1s, 2s backoff
      }
    }
  }
  console.error('API failed after retries:', url);
  return [];
}

// ════════════════════ NAVIGATION ════════════════════
function setupNavigation() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      switchTab(tab);
    });
  });
}

function switchTab(tab) {
  state.currentTab = tab;
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const activeBtn = document.querySelector(`.nav-btn[data-tab="${tab}"]`);
  if (activeBtn) activeBtn.classList.add('active');
  document.querySelectorAll('.tab-content').forEach(s => s.classList.remove('active'));
  const section = document.getElementById(`tab-${tab}`);
  if (section) section.classList.add('active');
  renderCurrentTab();
}

function renderCurrentTab() {
  switch (state.currentTab) {
    case 'dashboard': renderDashboard(); break;
    case 'leaderboard': renderLeaderboard(); break;
    case 'calendar': renderCalendar(); break;
    case 'team': renderTeam(); break;
    case 'quiz': renderQuizParticipant(); break;
    case 'survey-report': renderSurveyReport(); break;
    case 'admin-members': renderAdminMembers(); break;
    case 'admin-points': renderAdminPoints(); break;
    case 'admin-quiz': renderAdminQuiz(); break;
    case 'admin-survey': renderAdminSurvey(); break;
  }
}

// ════════════════════ AUTH ════════════════════
function setupAuth() {
  const profileBtn = document.getElementById('profileBtn');
  const loginModal = document.getElementById('loginModal');
  const closeLogin = document.getElementById('closeLogin');
  const loginForm = document.getElementById('loginForm');

  profileBtn.addEventListener('click', () => {
    if (state.isAdmin || state.isEngSys) {
      state.isAdmin = false;
      state.isEngSys = false;
      profileBtn.classList.remove('admin-active');
      profileBtn.innerHTML = '<i class="ri-user-line"></i>';
      document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
      document.querySelectorAll('.engsys-only').forEach(el => el.style.display = 'none');
      document.getElementById('nav-quiz').style.display = '';
      switchTab('dashboard');
      toast('Logged out');
    } else {
      loginModal.classList.add('show');
    }
  });

  closeLogin.addEventListener('click', () => loginModal.classList.remove('show'));
  loginModal.addEventListener('click', e => { if (e.target === loginModal) loginModal.classList.remove('show'); });

  loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    const user = document.getElementById('loginUser').value;
    const pass = document.getElementById('loginPass').value;
    const res = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username: user, password: pass }),
    });
    if (res.success) {
      loginModal.classList.remove('show');
      loginForm.reset();
      document.getElementById('loginError').textContent = '';
      profileBtn.classList.add('admin-active');

      if (res.role === 'admin') {
        state.isAdmin = true;
        state.isEngSys = false;
        profileBtn.innerHTML = '<i class="ri-shield-user-line"></i>';
        document.querySelectorAll('.admin-only').forEach(el => el.style.display = '');
        document.querySelectorAll('.engsys-only').forEach(el => el.style.display = 'none');
        document.getElementById('nav-quiz').style.display = 'none';
        toast('Welcome, Admin!', 'success');
      } else if (res.role === 'engsys') {
        state.isEngSys = true;
        state.isAdmin = false;
        profileBtn.innerHTML = '<i class="ri-team-line"></i>';
        document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
        document.querySelectorAll('.engsys-only').forEach(el => el.style.display = '');
        document.getElementById('nav-quiz').style.display = '';
        toast('Welcome, EngSys!', 'success');
      }
      renderCurrentTab();
    } else {
      document.getElementById('loginError').textContent = 'Invalid credentials';
    }
  });

  // Close generic modal
  document.getElementById('closeGenericModal').addEventListener('click', () => {
    document.getElementById('genericModal').classList.remove('show');
  });
  document.getElementById('genericModal').addEventListener('click', e => {
    if (e.target.id === 'genericModal') e.target.classList.remove('show');
  });
}

// ════════════════════ HELPERS ════════════════════
function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function getMember(id) {
  return state.members.find(m => m.id === id);
}

function avatarHTML(member, size = 36) {
  if (member?.avatar) {
    return `<img src="${member.avatar}" alt="${member.name}" style="width:${size}px;height:${size}px;border-radius:50%;object-fit:cover;">`;
  }
  return getInitials(member?.name || '??');
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function getNextEvent() {
  const now = new Date();
  now.setHours(0,0,0,0);
  return state.events.find(e => new Date(e.date + 'T00:00:00') >= now) || state.events[state.events.length - 1];
}

function getCurrentOrLastEvent() {
  const now = new Date();
  now.setHours(0,0,0,0);
  let current = state.events.find(e => {
    const ed = new Date(e.date + 'T00:00:00');
    const diff = (ed - now) / (1000*60*60*24);
    return diff >= -7 && diff <= 30;
  });
  return current || getNextEvent();
}

function getPhaseColor(phase) {
  const colors = { SPARK: '#f59e0b', BUILD: '#3b82f6', APPLY: '#f97316', DELIVER: '#ef4444' };
  return colors[phase] || '#6b7280';
}

function toast(msg, type = '') {
  const container = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateY(10px)'; setTimeout(() => t.remove(), 300); }, 3000);
}

function openModal(html) {
  document.getElementById('genericModalContent').innerHTML = html;
  document.getElementById('genericModal').classList.add('show');
}

function closeModal() {
  document.getElementById('genericModal').classList.remove('show');
}

// ════════════════════ DASHBOARD ════════════════════
function renderDashboard() {
  renderCountdownCard();
  renderActivityCard();
  renderSeminarCard();
  renderTop3Card();
  renderProgressCard();
}

function renderCountdownCard() {
  const next = getNextEvent();
  if (!next) return;
  document.getElementById('countdown-title').textContent = `Month ${next.month}: ${next.title}`;
  document.getElementById('countdown-date').textContent = `${formatDate(next.date)} · ${next.time || '14:00'} IST · ${next.duration} min`;
}

function startCountdown() {
  function update() {
    const next = getNextEvent();
    if (!next) return;
    const target = new Date(next.date + 'T' + (next.time || '14:00') + ':00+05:30');
    const now = new Date();
    const diff = target - now;
    if (diff <= 0) {
      document.getElementById('cd-days').textContent = '00';
      document.getElementById('cd-hours').textContent = '00';
      document.getElementById('cd-mins').textContent = '00';
      return;
    }
    const days = Math.floor(diff / (1000*60*60*24));
    const hours = Math.floor((diff % (1000*60*60*24)) / (1000*60*60));
    const mins = Math.floor((diff % (1000*60*60)) / (1000*60));
    document.getElementById('cd-days').textContent = String(days).padStart(2, '0');
    document.getElementById('cd-hours').textContent = String(hours).padStart(2, '0');
    document.getElementById('cd-mins').textContent = String(mins).padStart(2, '0');
  }
  update();
  setInterval(update, 60000);
}

function renderActivityCard() {
  const event = getCurrentOrLastEvent();
  if (!event) return;
  document.getElementById('activity-body').innerHTML = `
    <span class="activity-phase phase-${event.phase}">${event.phase}</span>
    <div class="activity-title">${event.title}</div>
    <div class="activity-desc">${event.description}</div>
    <div class="activity-type"><i class="ri-flashlight-line"></i> ${event.activityType}</div>
    <div class="activity-skills">
      ${(event.skills || '').split(',').map(s => `<span class="skill-tag">${s.trim()}</span>`).join('')}
    </div>
  `;
}

function renderSeminarCard() {
  const event = getCurrentOrLastEvent();
  if (!event) return;
  const presenter = getMember(event.seminarPresenter);
  const presenterName = presenter ? presenter.name : 'TBD (To be drawn)';
  document.getElementById('seminar-body').innerHTML = `
    <div class="seminar-presenter">
      <div class="presenter-avatar">
        ${presenter ? avatarHTML(presenter, 40) : '<i class="ri-user-line"></i>'}
      </div>
      <div>
        <div class="presenter-name">${presenterName}</div>
        <div class="presenter-label">Seminar Presenter · Month ${event.month}</div>
      </div>
    </div>
    <div class="seminar-topic">
      <i class="ri-chat-quote-line" style="color:var(--siemens-petrol);margin-right:4px;"></i>
      ${event.seminarTopic}
    </div>
  `;
}

function renderTop3Card() {
  const top = state.leaderboard.slice(0, 3);
  if (!top.length || top.every(t => t.total === 0)) {
    document.getElementById('top3-body').innerHTML = `
      <div class="top3-empty">
        <i class="ri-trophy-line" style="font-size:32px;color:var(--border);"></i>
        <p style="margin-top:8px;">Points will appear here once activities begin</p>
      </div>`;
    return;
  }
  const medals = ['🥇', '🥈', '🥉'];
  document.getElementById('top3-body').innerHTML = top.map((m, i) => `
    <div class="top3-item">
      <div class="top3-rank">${medals[i]}</div>
      <div class="top3-avatar">${avatarHTML(m, 68)}</div>
      <div class="top3-name">${m.name.split(' ').slice(0, 2).join(' ')}</div>
      <div class="top3-points">${m.total}</div>
      <div class="top3-pts-label">points</div>
    </div>
  `).join('');
}

function renderProgressCard() {
  const total = state.events.length;
  const completed = state.events.filter(e => e.status === 'completed').length;
  const progress = total > 0 ? Math.round((completed / total) * 100) : 0;

  document.getElementById('progress-body').innerHTML = `
    <div class="flowline-progress">
      <div class="flowline-track">
        ${state.events.map((e, i) => {
          const isDone = e.status === 'completed';
          const isCurrent = !isDone && (i === 0 || state.events[i-1]?.status === 'completed');
          const dotClass = isDone ? 'done' : isCurrent ? 'current' : '';
          return `
            <div class="flowline-step ${dotClass}">
              <div class="flowline-dot"></div>
              ${i < total - 1 ? '<div class="flowline-line"></div>' : ''}
            </div>
          `;
        }).join('')}
      </div>
      <div class="flowline-labels">
        <span>${completed} of ${total} sessions done</span>
        <span>${progress}%</span>
      </div>
    </div>
  `;
}

// ════════════════════ LEADERBOARD ════════════════════
function renderLeaderboard() {
  const lb = state.leaderboard;
  const maxMonth = state.events.length > 0 ? Math.max(...state.events.map(e => e.month)) : 12;
  const months = Array.from({ length: maxMonth }, (_, i) => i + 1);

  document.getElementById('leaderboard-content').innerHTML = `
    <div class="leaderboard-table-wrap">
      <table class="leaderboard-table">
        <thead>
          <tr>
            <th style="width:48px;">#</th>
            <th>Member</th>
            ${months.map(m => `<th class="month-col">M${m}</th>`).join('')}
            <th style="text-align:right;">Total</th>
          </tr>
        </thead>
        <tbody>
          ${lb.map((m, i) => `
            <tr class="rank-${i + 1}">
              <td><span class="lb-rank lb-rank-${i + 1}">${i + 1}</span></td>
              <td>
                <div class="lb-member">
                  <div class="lb-avatar">${avatarHTML(m, 36)}</div>
                  <div>
                    <div class="lb-name">${m.name}</div>
                    <div class="lb-domain">${m.domain}</div>
                  </div>
                </div>
              </td>
              ${months.map(mo => {
                const pts = m.monthlyBreakdown[mo] || 0;
                return `<td class="lb-month-pts ${pts > 0 ? 'has-pts' : ''}">${pts || '·'}</td>`;
              }).join('')}
              <td style="text-align:right;"><span class="lb-total">${m.total}</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

// ════════════════════ CALENDAR ════════════════════
function renderCalendar() {
  const now = new Date();
  now.setHours(0,0,0,0);

  document.getElementById('calendar-content').innerHTML = `
    <div class="calendar-timeline">
      ${state.events.map(e => {
        const eventDate = new Date(e.date + 'T00:00:00');
        const isPast = eventDate < now && (now - eventDate) > 7 * 24 * 60 * 60 * 1000;
        const isCurrent = !isPast && Math.abs(eventDate - now) <= 30 * 24 * 60 * 60 * 1000;
        const cls = isPast ? 'past' : isCurrent ? 'current' : '';
        const presenter = getMember(e.seminarPresenter);

        return `
          <div class="cal-event ${cls}">
            <div class="cal-dot"></div>
            <div class="cal-card">
              <div class="cal-header">
                <span class="cal-month-badge">MONTH ${e.month}</span>
                <span class="activity-phase phase-${e.phase}" style="margin:0;padding:2px 8px;font-size:10px;">${e.phase}</span>
                ${e.activityType ? `<span class="cal-tag-pill"><i class="ri-flashlight-line"></i>${e.activityType}</span>` : ''}
                <span class="cal-date"><i class="ri-calendar-line"></i> ${formatDate(e.date)}</span>
                ${state.isAdmin ? `
                  <button class="cal-edit-btn" onclick="editEventModal('${e.id}')"><i class="ri-edit-line"></i> Edit</button>
                  <button class="cal-edit-btn cal-delete-btn" onclick="deleteEvent('${e.id}')"><i class="ri-delete-bin-line"></i></button>
                ` : ''}
              </div>
              <div class="cal-title">${e.title}</div>
              <div class="cal-desc">${e.description}</div>
              <div class="cal-meta">
                <span class="cal-tag"><i class="ri-time-line"></i>${e.duration} min</span>
                <span class="cal-tag"><i class="ri-mic-line"></i>${presenter ? presenter.name : 'TBD'}</span>
                ${e.status === 'completed' ? '<span class="badge badge-completed">Completed</span>' : '<span class="badge badge-upcoming">Upcoming</span>'}
              </div>
              ${e.comments ? `<div style="margin-top:10px;padding:8px;background:var(--bg);border-radius:var(--radius-sm);font-size:12px;color:var(--text-secondary);"><i class="ri-chat-3-line"></i> ${e.comments}</div>` : ''}
            </div>
          </div>
        `;
      }).join('')}
    </div>
    ${state.isAdmin ? `<button class="btn btn-primary" style="margin-top:20px;" onclick="addEventModal()"><i class="ri-add-line"></i> Add Session</button>` : ''}
  `;
}

// Admin: Delete event
window.deleteEvent = async function(eventId) {
  if (!confirm('Delete this event?')) return;
  await api(`/api/events/${eventId}`, { method: 'DELETE' });
  await loadAllData();
  renderCurrentTab();
  toast('Event deleted', 'success');
};

// Admin: Add event modal
window.addEventModal = function() {
  const nextMonth = state.events.length > 0 ? Math.max(...state.events.map(e => e.month)) + 1 : 1;
  openModal(`
    <h2 style="text-align:left;margin-bottom:20px;">Add New Session</h2>
    <form id="addEventForm">
      <div class="form-row">
        <div><label class="form-label">Month #</label><div class="input-group"><i class="ri-calendar-line"></i><input type="number" id="ae-month" value="${nextMonth}" required></div></div>
        <div><label class="form-label">Phase</label>
          <div class="input-group"><i class="ri-flag-line"></i>
            <select id="ae-phase"><option>SPARK</option><option>BUILD</option><option>APPLY</option><option>DELIVER</option></select>
          </div>
        </div>
      </div>
      <label class="form-label">Title</label>
      <div class="input-group"><i class="ri-text"></i><input id="ae-title" placeholder="Session title" required></div>
      <label class="form-label">Description</label>
      <div class="input-group"><i class="ri-file-text-line"></i><textarea id="ae-desc" placeholder="What happens in this session"></textarea></div>
      <div class="form-row">
        <div><label class="form-label">Date</label><div class="input-group"><i class="ri-calendar-line"></i><input type="date" id="ae-date" required></div></div>
        <div><label class="form-label">Time</label><div class="input-group"><i class="ri-time-line"></i><input type="time" id="ae-time" value="14:00"></div></div>
      </div>
      <div class="form-row">
        <div><label class="form-label">Duration (min)</label><div class="input-group"><i class="ri-timer-line"></i><input type="number" id="ae-duration" value="60"></div></div>
        <div><label class="form-label">Activity Type</label><div class="input-group"><i class="ri-flashlight-line"></i><input id="ae-type" placeholder="e.g. Pre-worked"></div></div>
      </div>
      <label class="form-label">Skills (comma-separated)</label>
      <div class="input-group"><i class="ri-tools-line"></i><input id="ae-skills" placeholder="e.g. Python, prompt engineering"></div>
      <label class="form-label">Seminar Presenter</label>
      <div class="input-group"><i class="ri-user-line"></i>
        <select id="ae-presenter"><option value="">TBD</option>${state.members.map(m => `<option value="${m.id}">${m.name}</option>`).join('')}</select>
      </div>
      <label class="form-label">Seminar Topic</label>
      <div class="input-group"><i class="ri-chat-quote-line"></i><input id="ae-topic" placeholder="Optional"></div>
      <button type="submit" class="btn btn-primary btn-full" style="margin-top:12px;">Add Session</button>
    </form>
  `);
  document.getElementById('addEventForm').onsubmit = async (ev) => {
    ev.preventDefault();
    await api('/api/events', {
      method: 'POST',
      body: JSON.stringify({
        month: parseInt(document.getElementById('ae-month').value),
        phase: document.getElementById('ae-phase').value,
        title: document.getElementById('ae-title').value,
        description: document.getElementById('ae-desc').value,
        date: document.getElementById('ae-date').value,
        time: document.getElementById('ae-time').value,
        duration: parseInt(document.getElementById('ae-duration').value),
        activityType: document.getElementById('ae-type').value,
        skills: document.getElementById('ae-skills').value,
        seminarPresenter: document.getElementById('ae-presenter').value || null,
        seminarTopic: document.getElementById('ae-topic').value,
        status: 'upcoming',
        comments: '',
      }),
    });
    await loadAllData();
    closeModal();
    renderCurrentTab();
    toast('Session added', 'success');
  };
};

// Admin: Edit event modal
window.editEventModal = function(eventId) {
  const e = state.events.find(ev => ev.id === eventId);
  if (!e) return;
  openModal(`
    <h2 style="text-align:left;margin-bottom:20px;">Edit Event: Month ${e.month}</h2>
    <form id="editEventForm">
      <label class="form-label">Title</label>
      <div class="input-group"><i class="ri-text"></i><input id="ee-title" value="${e.title}" required></div>
      <div class="form-row">
        <div><label class="form-label">Month #</label><div class="input-group"><i class="ri-calendar-line"></i><input type="number" id="ee-month" value="${e.month}"></div></div>
        <div><label class="form-label">Phase</label>
          <div class="input-group"><i class="ri-flag-line"></i>
            <select id="ee-phase"><option ${e.phase==='SPARK'?'selected':''}>SPARK</option><option ${e.phase==='BUILD'?'selected':''}>BUILD</option><option ${e.phase==='APPLY'?'selected':''}>APPLY</option><option ${e.phase==='DELIVER'?'selected':''}>DELIVER</option></select>
          </div>
        </div>
      </div>
      <div class="form-row">
        <div><label class="form-label">Date</label><div class="input-group"><i class="ri-calendar-line"></i><input type="date" id="ee-date" value="${e.date}" required></div></div>
        <div><label class="form-label">Time</label><div class="input-group"><i class="ri-time-line"></i><input type="time" id="ee-time" value="${e.time || '14:00'}"></div></div>
      </div>
      <div class="form-row">
        <div><label class="form-label">Duration (min)</label><div class="input-group"><i class="ri-timer-line"></i><input type="number" id="ee-duration" value="${e.duration}"></div></div>
        <div><label class="form-label">Status</label><div class="input-group"><i class="ri-flag-line"></i>
          <select id="ee-status"><option value="upcoming" ${e.status==='upcoming'?'selected':''}>Upcoming</option><option value="completed" ${e.status==='completed'?'selected':''}>Completed</option></select>
        </div></div>
      </div>
      <label class="form-label">Activity Type</label>
      <div class="input-group"><i class="ri-flashlight-line"></i><input id="ee-acttype" value="${e.activityType || ''}"></div>
      <label class="form-label">Description</label>
      <div class="input-group"><i class="ri-file-text-line"></i><textarea id="ee-desc">${e.description}</textarea></div>
      <label class="form-label">Skills (comma-separated)</label>
      <div class="input-group"><i class="ri-tools-line"></i><input id="ee-skills" value="${e.skills || ''}"></div>
      <label class="form-label">Seminar Presenter</label>
      <div class="input-group"><i class="ri-user-line"></i>
        <select id="ee-presenter">
          <option value="">TBD</option>
          ${state.members.map(m => `<option value="${m.id}" ${e.seminarPresenter === m.id ? 'selected' : ''}>${m.name}</option>`).join('')}
        </select>
      </div>
      <label class="form-label">Seminar Topic</label>
      <div class="input-group"><i class="ri-chat-quote-line"></i><input id="ee-topic" value="${e.seminarTopic || ''}"></div>
      <label class="form-label">Comments</label>
      <div class="input-group"><i class="ri-chat-3-line"></i><textarea id="ee-comments">${e.comments || ''}</textarea></div>
      <button type="submit" class="btn btn-primary btn-full" style="margin-top:12px;">Save Changes</button>
    </form>
  `);
  document.getElementById('editEventForm').onsubmit = async (ev) => {
    ev.preventDefault();
    await api(`/api/events/${eventId}`, {
      method: 'PUT',
      body: JSON.stringify({
        month: parseInt(document.getElementById('ee-month').value),
        phase: document.getElementById('ee-phase').value,
        title: document.getElementById('ee-title').value,
        date: document.getElementById('ee-date').value,
        time: document.getElementById('ee-time').value,
        duration: parseInt(document.getElementById('ee-duration').value),
        status: document.getElementById('ee-status').value,
        activityType: document.getElementById('ee-acttype').value,
        skills: document.getElementById('ee-skills').value,
        description: document.getElementById('ee-desc').value,
        seminarPresenter: document.getElementById('ee-presenter').value || null,
        seminarTopic: document.getElementById('ee-topic').value,
        comments: document.getElementById('ee-comments').value,
      }),
    });
    await loadAllData();
    closeModal();
    renderCurrentTab();
    toast('Event updated', 'success');
  };
};

// ════════════════════ TEAM ════════════════════
function renderTeam() {
  const domains = ['All', ...new Set(state.members.map(m => m.domain))];
  const subtitle = document.getElementById('team-subtitle');
  if (subtitle) subtitle.textContent = `Engineering Systems \u2014 ${state.members.length} members across ${domains.length - 1} domains`;
  const filterEl = document.getElementById('domain-filter');
  filterEl.innerHTML = domains.map(d =>
    `<button class="filter-btn ${d === 'All' ? 'active' : ''}" onclick="filterTeam('${d}')">${d}</button>`
  ).join('');
  renderTeamCards('All');
}

window.filterTeam = function(domain) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  renderTeamCards(domain);
};

function renderTeamCards(domain) {
  const filtered = domain === 'All' ? state.members : state.members.filter(m => m.domain === domain);
  document.getElementById('team-content').innerHTML = filtered.map((m, i) => `
    <div class="team-card" style="animation-delay:${i * 0.05}s;">
      <div class="team-avatar">${avatarHTML(m, 72)}</div>
      <div class="team-name">${m.name}</div>
      <div class="team-role">${m.role || ''}</div>
      <span class="team-domain-badge domain-${m.domain.split(' ')[0]}">${m.domain}</span>
    </div>
  `).join('');
}

// ════════════════════ SURVEY REPORT ════════════════════
function renderSurveyReport() {
  const container = document.getElementById('survey-report-content');
  if (!container) return;
  if (container.querySelector('.sr-subtabs')) return; // already built

  container.innerHTML = `
    <div class="section-header">
      <h2><i class="ri-bar-chart-box-line"></i> Survey Report</h2>
      <p>AI CatalyESt adoption survey — 21 use cases from 15 respondents</p>
    </div>
    <div class="sr-subtabs" id="sr-subtabs">
      <button class="sr-tab active" data-srtab="overview"><i class="ri-pie-chart-line"></i> Overview</button>
      <button class="sr-tab" data-srtab="catalogue"><i class="ri-grid-line"></i> Catalogue</button>
      <button class="sr-tab" data-srtab="impact"><i class="ri-bar-chart-line"></i> Impact</button>
      <button class="sr-tab" data-srtab="rawdata"><i class="ri-database-2-line"></i> Raw Data</button>
    </div>
    <iframe id="sr-iframe" src="/survey-report.html" style="width:100%;border:none;overflow:hidden;display:block;min-height:800px;"></iframe>
  `;

  // Auto-resize iframe to content height — no scrollbar
  window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'sr-height') {
      const iframe = document.getElementById('sr-iframe');
      if (iframe) iframe.style.height = (e.data.height + 20) + 'px';
    }
  });

  // Sub-tab switching
  document.querySelectorAll('.sr-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sr-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const iframe = document.getElementById('sr-iframe');
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage({ type: 'sr-switch-tab', tab: btn.dataset.srtab }, '*');
      }
    });
  });
}

// ════════════════════ ADMIN: MEMBERS ════════════════════
function renderAdminMembers() {
  document.getElementById('admin-members-content').innerHTML = `
    <div class="admin-toolbar">
      <span style="font-size:14px;color:var(--text-secondary);">${state.members.length} members</span>
      <button class="btn btn-primary btn-sm" onclick="addMemberModal()"><i class="ri-user-add-line"></i> Add Member</button>
    </div>
    <div class="admin-member-list">
      ${state.members.map(m => `
        <div class="admin-member-row">
          <div class="lb-avatar" style="width:40px;height:40px;font-size:14px;">${avatarHTML(m, 40)}</div>
          <div class="admin-member-info" style="flex:1;">
            <div class="lb-name">${m.name}</div>
            <div class="lb-domain">${m.email} · ${m.domain}</div>
          </div>
          <div class="admin-member-actions">
            <button class="btn-icon" title="Upload Photo" onclick="uploadAvatarModal('${m.id}')"><i class="ri-camera-line"></i></button>
            <button class="btn-icon" title="Edit" onclick="editMemberModal('${m.id}')"><i class="ri-edit-line"></i></button>
            <button class="btn-icon" title="Remove" onclick="deleteMember('${m.id}','${m.name}')"><i class="ri-delete-bin-line"></i></button>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

window.addMemberModal = function() {
  openModal(`
    <h2 style="text-align:left;margin-bottom:20px;">Add Member</h2>
    <form id="addMemberForm">
      <label class="form-label">Full Name</label>
      <div class="input-group"><i class="ri-user-line"></i><input id="am-name" placeholder="e.g. John Doe" required></div>
      <label class="form-label">Email</label>
      <div class="input-group"><i class="ri-mail-line"></i><input type="email" id="am-email" placeholder="john.doe@siemens.com"></div>
      <div class="form-row">
        <div><label class="form-label">Role</label><div class="input-group"><i class="ri-briefcase-line"></i><input id="am-role" placeholder="Optional"></div></div>
        <div><label class="form-label">Domain</label><div class="input-group"><i class="ri-building-line"></i>
          <select id="am-domain"><option>PLM</option><option>Manufacturing</option><option>OT & Automation</option><option>Cross-Functional</option></select>
        </div></div>
      </div>
      <button type="submit" class="btn btn-primary btn-full" style="margin-top:12px;">Add Member</button>
    </form>
  `);
  document.getElementById('addMemberForm').onsubmit = async (e) => {
    e.preventDefault();
    await api('/api/members', {
      method: 'POST',
      body: JSON.stringify({
        name: document.getElementById('am-name').value,
        email: document.getElementById('am-email').value,
        role: document.getElementById('am-role').value,
        domain: document.getElementById('am-domain').value,
      }),
    });
    await loadAllData();
    closeModal();
    renderAdminMembers();
    toast('Member added', 'success');
  };
};

window.editMemberModal = function(id) {
  const m = getMember(id);
  if (!m) return;
  openModal(`
    <h2 style="text-align:left;margin-bottom:20px;">Edit Member</h2>
    <form id="editMemberForm">
      <label class="form-label">Full Name</label>
      <div class="input-group"><i class="ri-user-line"></i><input id="em-name" value="${m.name}" required></div>
      <label class="form-label">Email</label>
      <div class="input-group"><i class="ri-mail-line"></i><input type="email" id="em-email" value="${m.email}"></div>
      <div class="form-row">
        <div><label class="form-label">Role</label><div class="input-group"><i class="ri-briefcase-line"></i><input id="em-role" value="${m.role || ''}"></div></div>
        <div><label class="form-label">Domain</label><div class="input-group"><i class="ri-building-line"></i>
          <select id="em-domain">
            ${['PLM','Manufacturing','OT & Automation','Cross-Functional'].map(d => `<option ${m.domain===d?'selected':''}>${d}</option>`).join('')}
          </select>
        </div></div>
      </div>
      <button type="submit" class="btn btn-primary btn-full" style="margin-top:12px;">Save</button>
    </form>
  `);
  document.getElementById('editMemberForm').onsubmit = async (e) => {
    e.preventDefault();
    await api(`/api/members/${id}`, {
      method: 'PUT',
      body: JSON.stringify({
        name: document.getElementById('em-name').value,
        email: document.getElementById('em-email').value,
        role: document.getElementById('em-role').value,
        domain: document.getElementById('em-domain').value,
      }),
    });
    await loadAllData();
    closeModal();
    renderAdminMembers();
    toast('Member updated', 'success');
  };
};

window.uploadAvatarModal = function(id) {
  const m = getMember(id);
  openModal(`
    <h2 style="text-align:left;margin-bottom:20px;">Upload Photo: ${m?.name}</h2>
    <div style="text-align:center;margin-bottom:16px;">
      <div class="team-avatar" style="width:96px;height:96px;font-size:32px;margin:0 auto;">${avatarHTML(m, 96)}</div>
    </div>
    <form id="uploadAvatarForm" enctype="multipart/form-data">
      <input type="file" id="avatar-file" accept="image/*" required style="margin-bottom:12px;width:100%;">
      <button type="submit" class="btn btn-primary btn-full">Upload</button>
    </form>
  `);
  document.getElementById('uploadAvatarForm').onsubmit = async (e) => {
    e.preventDefault();
    const file = document.getElementById('avatar-file').files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('avatar', file);
    await fetch(`/api/members/${id}/avatar`, { method: 'POST', body: formData });
    await loadAllData();
    closeModal();
    renderAdminMembers();
    toast('Photo uploaded', 'success');
  };
};

window.deleteMember = async function(id, name) {
  if (!confirm(`Remove ${name} from the team?`)) return;
  await api(`/api/members/${id}`, { method: 'DELETE' });
  await loadAllData();
  renderAdminMembers();
  toast('Member removed');
};

// ════════════════════ ADMIN: POINTS ════════════════════
function renderAdminPoints() {
  const months = Array.from({ length: 12 }, (_, i) => i + 1);
  const monthPoints = state.points.filter(p => p.month === state.selectedMonth);

  document.getElementById('admin-points-content').innerHTML = `
    <div class="points-month-selector">
      ${months.map(m => {
        const e = state.events.find(ev => ev.month === m);
        return `<button class="month-btn ${m === state.selectedMonth ? 'active' : ''}" onclick="selectPointsMonth(${m})">M${m}${e ? ': ' + e.title.split(':')[0].substring(0, 12) : ''}</button>`;
      }).join('')}
    </div>
    <div class="admin-toolbar">
      <span style="font-size:14px;color:var(--text-secondary);">Month ${state.selectedMonth} — ${monthPoints.length} entries</span>
      <button class="btn btn-primary btn-sm" onclick="addPointsModal(${state.selectedMonth})"><i class="ri-add-line"></i> Award Points</button>
    </div>
    <div class="points-entry-list">
      ${monthPoints.length === 0 ? '<div class="empty-state"><i class="ri-star-line"></i><p>No points awarded for this month yet</p></div>' : ''}
      ${monthPoints.map(p => {
        const m = getMember(p.memberId);
        return `
          <div class="points-entry">
            <span class="pe-member">${m ? m.name : p.memberId}</span>
            <span class="pe-category">${p.category}</span>
            <span class="pe-points">+${p.points}</span>
            <button class="btn-icon btn-xs" title="Delete" onclick="deletePoints('${p.id}')"><i class="ri-delete-bin-line"></i></button>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

window.selectPointsMonth = function(m) {
  state.selectedMonth = m;
  renderAdminPoints();
};

window.addPointsModal = function(month) {
  const event = state.events.find(e => e.month === month);
  const categories = event ? event.categories : [];
  openModal(`
    <h2 style="text-align:left;margin-bottom:20px;">Award Points — Month ${month}</h2>
    <form id="addPointsForm">
      <label class="form-label">Member</label>
      <div class="input-group"><i class="ri-user-line"></i>
        <select id="ap-member" required>
          <option value="">Select member...</option>
          ${state.members.map(m => `<option value="${m.id}">${m.name}</option>`).join('')}
        </select>
      </div>
      <label class="form-label">Category</label>
      <div class="input-group"><i class="ri-medal-line"></i>
        <select id="ap-category" required>
          <option value="">Select category...</option>
          ${categories.map(c => `<option value="${c}">${c}</option>`).join('')}
          <option value="Quiz - 1st Place">Quiz - 1st Place</option>
          <option value="Quiz - 2nd Place">Quiz - 2nd Place</option>
          <option value="Quiz - 3rd Place">Quiz - 3rd Place</option>
          <option value="Seminar Presenter">Seminar Presenter</option>
          <option value="First to Submit">First to Submit</option>
          <option value="Custom">Custom...</option>
        </select>
      </div>
      <div id="custom-category-wrap" style="display:none;">
        <label class="form-label">Custom Category</label>
        <div class="input-group"><i class="ri-edit-line"></i><input id="ap-custom-cat" placeholder="Enter category name"></div>
      </div>
      <label class="form-label">Points</label>
      <div class="input-group"><i class="ri-star-line"></i><input type="number" id="ap-points" min="1" max="20" value="5" required></div>
      <button type="submit" class="btn btn-primary btn-full" style="margin-top:12px;">Award Points</button>
    </form>
  `);
  document.getElementById('ap-category').addEventListener('change', e => {
    document.getElementById('custom-category-wrap').style.display = e.target.value === 'Custom' ? 'block' : 'none';
  });
  document.getElementById('addPointsForm').onsubmit = async (e) => {
    e.preventDefault();
    let category = document.getElementById('ap-category').value;
    if (category === 'Custom') category = document.getElementById('ap-custom-cat').value;
    await api('/api/points', {
      method: 'POST',
      body: JSON.stringify({
        memberId: document.getElementById('ap-member').value,
        month: month,
        category: category,
        points: parseInt(document.getElementById('ap-points').value),
      }),
    });
    await loadAllData();
    closeModal();
    renderAdminPoints();
    toast('Points awarded!', 'success');
  };
};

window.deletePoints = async function(id) {
  if (!confirm('Remove this points entry?')) return;
  await api(`/api/points/${id}`, { method: 'DELETE' });
  await loadAllData();
  renderAdminPoints();
  toast('Points removed');
};

// ════════════════════ ADMIN: QUIZ ════════════════════
function renderAdminQuiz() {
  document.getElementById('admin-quiz-content').innerHTML = `
    <div class="admin-toolbar">
      <span style="font-size:14px;color:var(--text-secondary);">${state.quizzes.length} quizzes created</span>
      <button class="btn btn-primary btn-sm" onclick="createQuizModal()"><i class="ri-add-line"></i> Create Quiz</button>
    </div>
    <div style="display:flex;flex-direction:column;gap:12px;">
      ${state.quizzes.map(q => `
        <div class="quiz-builder">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div>
              <h3 style="margin:0;">${q.title}</h3>
              <span style="font-size:12px;color:var(--text-tertiary);">Room: <strong>${q.roomCode}</strong> · ${q.questions.length} questions · ${q.status}</span>
            </div>
            <div style="display:flex;gap:6px;">
              ${q.status === 'waiting' ? `<button class="btn btn-primary btn-sm" onclick="startQuizRoom('${q.id}','${q.roomCode}')"><i class="ri-play-line"></i> Host</button>` : ''}
              ${q.status === 'completed' && q.results?.length ? `<button class="btn btn-secondary btn-sm" onclick="viewQuizResults('${q.id}')"><i class="ri-bar-chart-line"></i> Results</button>` : ''}
            </div>
          </div>
        </div>
      `).join('')}
    </div>
    ${state.adminQuizState ? renderAdminQuizLive() : ''}
  `;
}

function renderAdminQuizLive() {
  return `
    <div class="quiz-admin-live" id="admin-quiz-live">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h3>🔴 Live Quiz Room: ${state.adminQuizState.roomCode}</h3>
        <div style="display:flex;gap:8px;">
          ${!state.adminQuizState.started ? `<button class="btn btn-primary btn-sm" onclick="adminStartQuiz()"><i class="ri-play-line"></i> Start Quiz</button>` : ''}
          <button class="btn btn-danger btn-sm" onclick="adminEndQuiz()"><i class="ri-stop-line"></i> End Quiz</button>
        </div>
      </div>
      <p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px;">Share room code <strong>${state.adminQuizState.roomCode}</strong> with participants</p>
      <div class="quiz-participant-grid" id="admin-quiz-participants"></div>
    </div>
  `;
}

window.createQuizModal = function() {
  openModal(`
    <h2 style="text-align:left;margin-bottom:20px;">Create Quiz</h2>
    <form id="createQuizForm">
      <label class="form-label">Quiz Title</label>
      <div class="input-group"><i class="ri-gamepad-line"></i><input id="cq-title" placeholder="e.g. Month 3 - GenAI Basics" required></div>
      <label class="form-label">Month</label>
      <div class="input-group"><i class="ri-calendar-line"></i>
        <select id="cq-month">${Array.from({length:12},(_,i)=>`<option value="${i+1}">Month ${i+1}</option>`).join('')}</select>
      </div>
      <div id="cq-questions">
        ${[1,2,3,4,5].map(i => `
          <div class="question-builder">
            <strong style="font-size:13px;color:var(--text-secondary);display:block;margin-bottom:8px;">Question ${i}</strong>
            <div class="input-group"><i class="ri-question-line"></i><input id="cq-q${i}" placeholder="Question ${i}" required></div>
            <div class="form-row">
              <div class="input-group"><i class="ri-checkbox-blank-circle-line"></i><input id="cq-q${i}a" placeholder="Option A" required></div>
              <div class="input-group"><i class="ri-checkbox-blank-circle-line"></i><input id="cq-q${i}b" placeholder="Option B" required></div>
            </div>
            <div class="form-row">
              <div class="input-group"><i class="ri-checkbox-blank-circle-line"></i><input id="cq-q${i}c" placeholder="Option C" required></div>
              <div class="input-group"><i class="ri-checkbox-blank-circle-line"></i><input id="cq-q${i}d" placeholder="Option D" required></div>
            </div>
            <label class="form-label">Correct Answer</label>
            <div class="input-group"><i class="ri-check-line"></i>
              <select id="cq-q${i}ans"><option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option></select>
            </div>
          </div>
        `).join('')}
      </div>
      <button type="submit" class="btn btn-primary btn-full" style="margin-top:12px;">Create Quiz</button>
    </form>
  `);
  document.getElementById('createQuizForm').onsubmit = async (e) => {
    e.preventDefault();
    const questions = [1,2,3,4,5].map(i => ({
      id: `q${i}`,
      question: document.getElementById(`cq-q${i}`).value,
      options: {
        A: document.getElementById(`cq-q${i}a`).value,
        B: document.getElementById(`cq-q${i}b`).value,
        C: document.getElementById(`cq-q${i}c`).value,
        D: document.getElementById(`cq-q${i}d`).value,
      },
      correctAnswer: document.getElementById(`cq-q${i}ans`).value,
    }));
    await api('/api/quizzes', {
      method: 'POST',
      body: JSON.stringify({
        title: document.getElementById('cq-title').value,
        month: parseInt(document.getElementById('cq-month').value),
        questions,
      }),
    });
    await loadAllData();
    closeModal();
    renderAdminQuiz();
    toast('Quiz created!', 'success');
  };
};

window.startQuizRoom = function(quizId, roomCode) {
  state.adminQuizState = { quizId, roomCode, started: false, participants: [] };
  state.socket.emit('quiz:create', { quizId, roomCode });
  renderAdminQuiz();
  toast('Quiz room created! Share code: ' + roomCode, 'success');
};

window.adminStartQuiz = function() {
  if (!state.adminQuizState) return;
  state.adminQuizState.started = true;
  state.socket.emit('quiz:start', { roomCode: state.adminQuizState.roomCode });
  renderAdminQuiz();
  toast('Quiz started!', 'success');
};

window.adminEndQuiz = function() {
  if (!state.adminQuizState) return;
  state.socket.emit('quiz:end', { roomCode: state.adminQuizState.roomCode });
  state.adminQuizState = null;
  loadAllData().then(() => renderAdminQuiz());
  toast('Quiz ended');
};

window.viewQuizResults = function(quizId) {
  const quiz = state.quizzes.find(q => q.id === quizId);
  if (!quiz || !quiz.results) return;
  const sorted = [...quiz.results].sort((a, b) => b.finalScore - a.finalScore);
  openModal(`
    <h2 style="text-align:left;margin-bottom:20px;">Quiz Results: ${quiz.title}</h2>
    <div style="display:flex;flex-direction:column;gap:8px;">
      ${sorted.map((r, i) => `
        <div class="points-entry">
          <span style="font-weight:800;color:var(--text-tertiary);min-width:24px;">#${i+1}</span>
          <span class="pe-member">${r.memberName}</span>
          <span style="font-size:12px;color:var(--text-secondary);">Score: ${r.score}/5</span>
          ${r.tabSwitches > 0 ? `<span style="font-size:12px;color:#ef4444;">-${r.tabSwitches} penalty</span>` : ''}
          <span class="pe-points">${r.finalScore}</span>
        </div>
      `).join('')}
    </div>
  `);
};

// ════════════════════ QUIZ: PARTICIPANT ════════════════════
function renderQuizParticipant() {
  if (state.quizState?.inProgress) {
    renderQuizQuestion();
    return;
  }
  if (state.quizState?.finished) {
    renderQuizResult();
    return;
  }
  document.getElementById('quiz-content').innerHTML = `
    <div class="quiz-join-wrap">
      <div style="font-size:48px;margin-bottom:16px;">🎮</div>
      <h3 style="margin-bottom:8px;">Join a Quiz Session</h3>
      <p style="color:var(--text-secondary);font-size:14px;margin-bottom:24px;">Enter the room code provided by the admin</p>
      <div class="input-group"><i class="ri-key-2-line"></i>
        <input id="quiz-room-code" placeholder="Room Code (e.g. ABC123)" style="text-transform:uppercase;font-size:18px;text-align:center;letter-spacing:4px;" maxlength="6">
      </div>
      <div class="input-group"><i class="ri-user-line"></i>
        <select id="quiz-member-select">
          <option value="">Select your name...</option>
          ${state.members.map(m => `<option value="${m.id}" data-name="${m.name}">${m.name}</option>`).join('')}
        </select>
      </div>
      <button class="btn btn-primary btn-full" onclick="joinQuizRoom()"><i class="ri-login-box-line"></i> Join Quiz</button>
    </div>
  `;
}

window.joinQuizRoom = function() {
  const code = document.getElementById('quiz-room-code').value.toUpperCase();
  const select = document.getElementById('quiz-member-select');
  const memberId = select.value;
  const memberName = select.options[select.selectedIndex]?.dataset?.name;
  if (!code || !memberId) { toast('Please enter room code and select your name', 'error'); return; }
  state.quizState = { roomCode: code, memberId, memberName, inProgress: false, finished: false, questions: [], currentQ: 0, tabSwitches: 0, answers: [] };
  state.socket.emit('quiz:join', { roomCode: code, memberId, memberName });
  document.getElementById('quiz-content').innerHTML = `
    <div class="quiz-join-wrap">
      <div style="font-size:48px;margin-bottom:16px;">⏳</div>
      <h3>Waiting for the quiz to start...</h3>
      <p style="color:var(--text-secondary);font-size:14px;margin-top:8px;">Room: <strong>${code}</strong></p>
      <p style="color:var(--text-secondary);font-size:14px;">You: <strong>${memberName}</strong></p>
    </div>
  `;
};

function renderQuizQuestion() {
  const qs = state.quizState;
  if (!qs || qs.currentQ >= qs.questions.length) {
    state.socket.emit('quiz:finished', { roomCode: qs.roomCode });
    qs.finished = true;
    qs.inProgress = false;
    renderQuizResult();
    return;
  }
  const q = qs.questions[qs.currentQ];
  document.getElementById('quiz-content').innerHTML = `
    <div class="quiz-question-card">
      <div class="quiz-question-number">Question ${qs.currentQ + 1} of ${qs.questions.length}</div>
      <div class="quiz-question-text">${q.question}</div>
      <div class="quiz-options">
        ${Object.entries(q.options).map(([key, val]) =>
          `<button class="quiz-option" data-key="${key}" onclick="answerQuiz('${q.id}','${key}')">${key}. ${val}</button>`
        ).join('')}
      </div>
      <div class="quiz-warning ${qs.tabSwitches > 0 ? 'show' : ''}" id="quiz-tab-warning">
        ⚠️ Tab switches detected: ${qs.tabSwitches} (−${qs.tabSwitches} point${qs.tabSwitches !== 1 ? 's' : ''})
      </div>
    </div>
  `;
  // Disable copy/paste
  document.addEventListener('copy', preventCopy);
  document.addEventListener('paste', preventCopy);
  document.addEventListener('cut', preventCopy);
}

function preventCopy(e) { e.preventDefault(); toast('Copy/paste disabled during quiz', 'error'); }

window.answerQuiz = function(questionId, answer) {
  const qs = state.quizState;
  document.querySelectorAll('.quiz-option').forEach(b => b.disabled = true);
  document.querySelector(`.quiz-option[data-key="${answer}"]`).classList.add('selected');
  state.socket.emit('quiz:answer', { roomCode: qs.roomCode, questionId, answer, timeTaken: 0 });
};

function renderQuizResult() {
  const qs = state.quizState;
  const score = qs.answers.filter(a => a.isCorrect).length;
  const finalScore = Math.max(0, score - qs.tabSwitches);
  document.getElementById('quiz-content').innerHTML = `
    <div class="quiz-result-card">
      <div style="font-size:48px;margin-bottom:16px;">${finalScore >= 4 ? '🏆' : finalScore >= 2 ? '👍' : '📚'}</div>
      <h3 style="margin-bottom:4px;">Quiz Complete!</h3>
      <div class="quiz-result-score">${finalScore}/${qs.questions.length}</div>
      <p style="color:var(--text-secondary);margin-top:8px;">
        Correct: ${score} · Tab switches: −${qs.tabSwitches}
      </p>
      <button class="btn btn-secondary" style="margin-top:20px;" onclick="resetQuiz()">Back to Lobby</button>
    </div>
  `;
  // Re-enable copy/paste
  document.removeEventListener('copy', preventCopy);
  document.removeEventListener('paste', preventCopy);
  document.removeEventListener('cut', preventCopy);
}

window.resetQuiz = function() {
  state.quizState = null;
  renderQuizParticipant();
};

// ════════════════════ ADMIN: SURVEY ════════════════════
function renderAdminSurvey() {
  document.getElementById('admin-survey-content').innerHTML = `
    <div class="admin-toolbar">
      <span style="font-size:14px;color:var(--text-secondary);">${state.surveys.length} surveys</span>
      <button class="btn btn-primary btn-sm" onclick="createSurveyModal()"><i class="ri-add-line"></i> Launch Survey</button>
    </div>
    <div style="display:flex;flex-direction:column;gap:12px;">
      ${state.surveys.map(s => {
        const presenter = getMember(s.presenterId);
        const avgRating = s.votes.length > 0 ? (s.votes.reduce((sum, v) => sum + v.rating, 0) / s.votes.length).toFixed(1) : '–';
        return `
          <div class="card" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div>
                <strong>${presenter ? presenter.name : 'Unknown'}</strong> — ${s.topic || 'Seminar'}
                <div style="font-size:12px;color:var(--text-tertiary);">Month ${s.month} · ${s.votes.length} votes · Avg: ⭐ ${avgRating}</div>
              </div>
              <div style="display:flex;gap:6px;align-items:center;">
                ${s.status === 'active' ? `<span class="badge badge-live">LIVE</span><button class="btn btn-danger btn-sm" onclick="closeSurvey('${s.id}')">Close</button>` : '<span class="badge badge-completed">Closed</span>'}
              </div>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

window.createSurveyModal = function() {
  openModal(`
    <h2 style="text-align:left;margin-bottom:20px;">Launch Seminar Survey</h2>
    <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px;">Anonymous rating — team members will rate the presenter 1–5 stars</p>
    <form id="createSurveyForm">
      <label class="form-label">Presenter</label>
      <div class="input-group"><i class="ri-user-line"></i>
        <select id="cs-presenter" required>
          <option value="">Select presenter...</option>
          ${state.members.map(m => `<option value="${m.id}">${m.name}</option>`).join('')}
        </select>
      </div>
      <label class="form-label">Month</label>
      <div class="input-group"><i class="ri-calendar-line"></i>
        <select id="cs-month">${Array.from({length:12},(_,i)=>`<option value="${i+1}">Month ${i+1}</option>`).join('')}</select>
      </div>
      <label class="form-label">Topic</label>
      <div class="input-group"><i class="ri-chat-quote-line"></i><input id="cs-topic" placeholder="Seminar topic"></div>
      <button type="submit" class="btn btn-primary btn-full" style="margin-top:12px;">Launch Survey</button>
    </form>
  `);
  document.getElementById('createSurveyForm').onsubmit = async (e) => {
    e.preventDefault();
    await api('/api/surveys', {
      method: 'POST',
      body: JSON.stringify({
        presenterId: document.getElementById('cs-presenter').value,
        month: parseInt(document.getElementById('cs-month').value),
        topic: document.getElementById('cs-topic').value,
      }),
    });
    await loadAllData();
    closeModal();
    renderAdminSurvey();
    toast('Survey launched! Team can rate now.', 'success');
  };
};

window.closeSurvey = async function(id) {
  await api(`/api/surveys/${id}/close`, { method: 'PUT' });
  await loadAllData();
  renderAdminSurvey();
  toast('Survey closed');
};

// ════════════════════ SURVEY: PARTICIPANT ════════════════════
function checkForActiveSurvey() {
  const active = state.surveys.find(s => s.status === 'active');
  if (active && !state.isAdmin) showSurveyCard(active);
}

function showSurveyCard(survey) {
  const presenter = getMember(survey.presenterId);
  const card = document.getElementById('active-survey-card');
  card.style.display = '';
  document.getElementById('active-survey-body').innerHTML = `
    <div style="text-align:center;">
      <p style="margin-bottom:4px;">How would you rate <strong>${presenter?.name || 'the presenter'}</strong>'s seminar?</p>
      <p style="font-size:12px;color:var(--text-tertiary);margin-bottom:16px;">${survey.topic || ''} — Your vote is anonymous</p>
      <div class="survey-stars" id="survey-stars">
        ${[1,2,3,4,5].map(i => `<span class="survey-star" data-rating="${i}" onclick="voteSurvey('${survey.id}',${i})">★</span>`).join('')}
      </div>
      <div class="survey-note">🔒 Anonymous · Click a star to submit</div>
    </div>
  `;
}

window.voteSurvey = async function(surveyId, rating) {
  document.querySelectorAll('.survey-star').forEach((s, i) => {
    s.classList.toggle('active', i < rating);
  });
  await api(`/api/surveys/${surveyId}/vote`, {
    method: 'POST',
    body: JSON.stringify({ rating }),
  });
  setTimeout(() => {
    document.getElementById('active-survey-body').innerHTML = `
      <div style="text-align:center;padding:16px;">
        <div style="font-size:32px;margin-bottom:8px;">✅</div>
        <p style="font-weight:600;">Thank you for your rating!</p>
        <p style="font-size:12px;color:var(--text-tertiary);">Your anonymous vote has been recorded</p>
      </div>
    `;
  }, 500);
  toast('Vote submitted!', 'success');
};

// ════════════════════ SOCKET LISTENERS ════════════════════
function setupSocketListeners() {
  const s = state.socket;

  // Quiz: room created confirmation
  s.on('quiz:roomCreated', (data) => {
    toast('Room created: ' + data.roomCode, 'success');
  });

  // Quiz: participant joined
  s.on('quiz:participantJoined', (data) => {
    if (state.adminQuizState) {
      state.adminQuizState.participants = data.participants;
      const grid = document.getElementById('admin-quiz-participants');
      if (grid) {
        grid.innerHTML = data.participants.map(p => `
          <div class="quiz-participant-card">
            <div class="qpc-name">${p.memberName}</div>
            <div style="font-size:12px;color:var(--text-tertiary);">Joined ✓</div>
          </div>
        `).join('');
      }
    }
  });

  // Quiz: started (participant receives questions)
  s.on('quiz:started', (data) => {
    if (state.quizState) {
      state.quizState.questions = data.questions;
      state.quizState.inProgress = true;
      state.quizState.currentQ = 0;
      // Setup tab visibility detection
      document.addEventListener('visibilitychange', onTabSwitch);
      renderQuizQuestion();
    }
  });

  // Quiz: admin started confirmation
  s.on('quiz:adminStarted', (data) => {
    toast(`Quiz started for ${data.participantCount} participants`);
  });

  // Quiz: answer result
  s.on('quiz:answerResult', (data) => {
    if (!state.quizState) return;
    state.quizState.answers.push(data);
    // Highlight correct/incorrect
    document.querySelectorAll('.quiz-option').forEach(btn => {
      if (btn.dataset.key === data.correctAnswer) btn.classList.add('correct');
      if (btn.classList.contains('selected') && !data.isCorrect) btn.classList.add('incorrect');
    });
    // Move to next question after delay
    setTimeout(() => {
      state.quizState.currentQ++;
      renderQuizQuestion();
    }, 1500);
  });

  // Quiz: tab switch penalty
  s.on('quiz:tabSwitchPenalty', (data) => {
    if (state.quizState) {
      state.quizState.tabSwitches = data.totalSwitches;
      const warn = document.getElementById('quiz-tab-warning');
      if (warn) {
        warn.classList.add('show');
        warn.textContent = `⚠️ Tab switches detected: ${data.totalSwitches} (−${data.totalSwitches} point${data.totalSwitches !== 1 ? 's' : ''})`;
      }
      toast(`⚠️ Tab switch detected! -1 point penalty`, 'error');
    }
  });

  // Quiz: participant tab switch (admin view)
  s.on('quiz:participantTabSwitch', (data) => {
    toast(`⚠️ ${data.memberName} switched tabs (${data.totalSwitches}x)`, 'error');
  });

  // Quiz: live results for admin
  s.on('quiz:liveResults', (data) => {
    const grid = document.getElementById('admin-quiz-participants');
    if (grid) {
      grid.innerHTML = data.results.map(r => `
        <div class="quiz-participant-card">
          <div class="qpc-name">${r.memberName}</div>
          <div class="qpc-score">${r.finalScore}/${5}</div>
          <div style="font-size:12px;color:var(--text-secondary);">Correct: ${r.score}</div>
          ${r.tabSwitches > 0 ? `<div class="qpc-penalty">Tab switches: −${r.tabSwitches}</div>` : ''}
          <div style="font-size:11px;color:var(--text-tertiary);margin-top:4px;">${r.finished ? '✅ Finished' : '⏳ In progress'}</div>
        </div>
      `).join('');
    }
  });

  // Quiz: ended
  s.on('quiz:ended', (data) => {
    document.removeEventListener('visibilitychange', onTabSwitch);
    if (state.quizState) {
      state.quizState.finished = true;
      state.quizState.inProgress = false;
      renderQuizResult();
    }
  });

  // Quiz: your final result
  s.on('quiz:yourResult', (data) => {
    if (state.quizState) {
      state.quizState.finished = true;
      state.quizState.inProgress = false;
      state.quizState.finalResult = data;
    }
  });

  // Quiz: participant left
  s.on('quiz:participantLeft', (data) => {
    toast(`${data.memberName} disconnected from quiz`);
  });

  // Quiz: error
  s.on('quiz:error', (data) => {
    toast(data.message, 'error');
  });

  // Survey: started
  s.on('survey:started', (survey) => {
    if (!state.isAdmin) {
      state.surveys.push(survey);
      showSurveyCard(survey);
      toast('📋 A survey has been launched! Rate the presenter.', 'success');
    }
  });

  // Survey: vote received (admin)
  s.on('survey:voteReceived', (data) => {
    // Could update admin view in real-time
  });

  // Survey: ended
  s.on('survey:ended', (data) => {
    const card = document.getElementById('active-survey-card');
    if (card) card.style.display = 'none';
  });
}

function onTabSwitch() {
  if (document.hidden && state.quizState?.inProgress) {
    state.socket.emit('quiz:tabSwitch', { roomCode: state.quizState.roomCode });
  }
}
