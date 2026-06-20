/* ═══════════════════════════════════════════════════════════════════
  app.js  —  AI Travel Itinerary Frontend
  Pure vanilla JS: no frameworks, no build step.
  Communicates with FastAPI backend via fetch + Server-Sent Events.
═══════════════════════════════════════════════════════════════════ */

const API = 'http://localhost:8000/api';

// ── State ─────────────────────────────────────────────────────────────────
let activeTab   = 'itinerary';
let currentData = null;

// ── DOM refs ──────────────────────────────────────────────────────────────
const $main    = () => document.getElementById('main-content');
const $logArea = () => document.getElementById('log-scroll');

// ── Init ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initStyleButtons();
  initInterestTags();
  initForm();
  showWelcome();
});

// ────────────────────────────────────────────────────────────────────────────
// Style selector
// ────────────────────────────────────────────────────────────────────────────
function initStyleButtons() {
  document.querySelectorAll('.style-opt').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.style-opt').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}

// ────────────────────────────────────────────────────────────────────────────
// Interest tags
// ────────────────────────────────────────────────────────────────────────────
function initInterestTags() {
  document.querySelectorAll('.itag').forEach(tag => {
    tag.addEventListener('click', () => tag.classList.toggle('active'));
  });
}

function getSelectedInterests() {
  return [...document.querySelectorAll('.itag.active')].map(t => t.dataset.value);
}

function getSelectedStyle() {
  const el = document.querySelector('.style-opt.active');
  return el ? el.dataset.value : 'comfort';
}

// ────────────────────────────────────────────────────────────────────────────
// Form submit
// ────────────────────────────────────────────────────────────────────────────
function initForm() {
  document.getElementById('travel-form').addEventListener('submit', async e => {
    e.preventDefault();
    const btn = document.getElementById('gen-btn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px"></div> Launching Agents...';

    const payload = {
      origin:           document.getElementById('origin').value.trim(),
      destination:      document.getElementById('destination').value.trim(),
      departure_date:   document.getElementById('dep-date').value,
      return_date:      document.getElementById('ret-date').value || null,
      adults:           parseInt(document.getElementById('adults').value),
      budget:           parseFloat(document.getElementById('budget').value),
      currency:         document.getElementById('currency').value,
      travel_style:     getSelectedStyle(),
      interests:        getSelectedInterests(),
      accommodation_type: 'hotel',
    };

    try {
      const res = await fetch(`${API}/generate`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Server error');
      streamUpdates(data.session_id, payload);
    } catch (err) {
      showError(err.message);
      btn.disabled = false;
      btn.innerHTML = '✨ Generate AI Itinerary';
    }
  });
}

// ────────────────────────────────────────────────────────────────────────────
// SSE streaming
// ────────────────────────────────────────────────────────────────────────────
function streamUpdates(sessionId, prefs) {
  showLoading(`Planning your trip to ${prefs.destination}…`);
  resetAgentPanel();

  const es = new EventSource(`${API}/stream/${sessionId}`);

  es.addEventListener('log', e => {
    const d = JSON.parse(e.data);
    appendLog(d.message);
    updateAgentDots(d.agent_statuses || {});
  });

  es.addEventListener('done', e => {
    es.close();
    const d = JSON.parse(e.data);
    currentData = d.state;
    renderResult(d.state);
    resetGenBtn();
  });

  es.addEventListener('error', e => {
    es.close();
    let msg = 'Generation failed';
    try { msg = JSON.parse(e.data).error; } catch(_){}
    showError(msg);
    resetGenBtn();
  });

  // Fallback: poll if SSE not supported / error
  es.onerror = () => {
    es.close();
    pollResult(sessionId);
  };
}

async function pollResult(sessionId) {
  for (let i = 0; i < 90; i++) {
    await sleep(2000);
    try {
      const res  = await fetch(`${API}/result/${sessionId}`);
      const data = await res.json();
      if (data.status === 'completed') {
        currentData = data.state;
        renderResult(data.state);
        resetGenBtn();
        return;
      } else if (data.status === 'error') {
        showError(data.error || 'Unknown error');
        resetGenBtn();
        return;
      }
      if (data.state?.log?.length) {
        const lines = data.state.log;
        lines.forEach(l => appendLog(l));
        updateAgentDots(data.state.agent_statuses || {});
      }
    } catch (_) {}
  }
  showError('Timed out waiting for result');
  resetGenBtn();
}

// ────────────────────────────────────────────────────────────────────────────
// Render full result
// ────────────────────────────────────────────────────────────────────────────
function renderResult(state) {
  const info   = state.final_itinerary || {};
  const days   = state.day_plans       || [];
  const flights= state.flights         || [];
  const hotels = state.hotels          || [];
  const budget = state.budget_breakdown;

  // Mark all agents done
  const allDone = {};
  (state.agent_statuses ? Object.keys(state.agent_statuses) : []).forEach(k => allDone[k] = 'completed');
  updateAgentDots(allDone);

  document.getElementById('main-content').innerHTML = `
    ${renderHero(info, state)}
    ${renderTabs()}
    <div id="panel-itinerary" class="tab-panel active">
      ${days.map(renderDayCard).join('')}
      ${renderTips(info)}
      ${renderCuisine(info)}
    </div>
    <div id="panel-flights" class="tab-panel">
      ${flights.length ? flights.map((f,i) => renderFlightCard(f,i)).join('') : '<p style="color:var(--faint);padding:20px">No flights found.</p>'}
    </div>
    <div id="panel-hotels" class="tab-panel">
      <div class="hotels-grid">
        ${hotels.length ? hotels.map((h,i) => renderHotelCard(h,i)).join('') : '<p style="color:var(--faint);padding:20px">No hotels found.</p>'}
      </div>
    </div>
    <div id="panel-budget" class="tab-panel">
      ${renderBudget(budget)}
    </div>
  `;

  // Day card expand/collapse
  document.querySelectorAll('.day-header').forEach(h => {
    h.addEventListener('click', () => {
      const body  = h.nextElementSibling;
      const chev  = h.querySelector('.chevron');
      const open  = body.style.display !== 'none';
      body.style.display = open ? 'none' : 'block';
      chev.classList.toggle('open', !open);
    });
  });

  // Tab switching
  document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => switchTab(t.dataset.tab));
  });

  // Open first day by default
  const firstBody = document.querySelector('.day-body');
  const firstChev = document.querySelector('.chevron');
  if (firstBody) { firstBody.style.display = 'block'; firstChev.classList.add('open'); }
}

// ────────────────────────────────────────────────────────────────────────────
// Hero
// ────────────────────────────────────────────────────────────────────────────
function renderHero(info, state) {
  const prefs   = state.preferences || {};
  const nights  = info.num_days || '?';
  const budget  = info.budget_breakdown || state.budget_breakdown || {};
  const within  = budget.within_budget;
  const highlights = (info.highlights || []).slice(0,5);
  return `
<div class="hero">
  <div class="hero-content">
    <div class="hero-tags">
      <span class="hero-tag tag-blue">📍 ${info.destination || prefs.destination || '—'}</span>
      <span class="hero-tag tag-violet">🗓 ${nights} days</span>
      ${within !== undefined
        ? `<span class="hero-tag ${within ? 'tag-green' : 'tag-amber'}">${within ? '✅ Within Budget' : '⚠️ Over Budget'}</span>`
        : ''}
    </div>
    <h1>${esc(info.title || `Discover ${info.destination || prefs.destination}`)}</h1>
    <p>${esc(info.tagline || 'Your personalised AI-curated travel plan')}</p>
    ${highlights.length ? `<div class="highlights">${highlights.map(h => `<span class="hlitem">✨ ${esc(h)}</span>`).join('')}</div>` : ''}
  </div>
</div>`;
}

// ────────────────────────────────────────────────────────────────────────────
// Tabs bar
// ────────────────────────────────────────────────────────────────────────────
function renderTabs() {
  const tabs = [
    { id:'itinerary', label:'📋 Itinerary' },
    { id:'flights',   label:'✈️ Flights'   },
    { id:'hotels',    label:'🏨 Hotels'    },
    { id:'budget',    label:'💰 Budget'    },
  ];
  return `<div class="tabs">${tabs.map(t =>
    `<button class="tab${t.id === 'itinerary' ? ' active' : ''}" data-tab="${t.id}">${t.label}</button>`
  ).join('')}</div>`;
}

function switchTab(id) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === id));
  document.querySelectorAll('.tab-panel').forEach(p => {
    p.classList.toggle('active', p.id === `panel-${id}`);
  });
}

// ────────────────────────────────────────────────────────────────────────────
// Day cards
// ────────────────────────────────────────────────────────────────────────────
function renderDayCard(day) {
  const w        = day.weather || {};
  const allActs  = [...(day.morning||[]), ...(day.afternoon||[]), ...(day.evening||[])];
  const cost     = day.estimated_daily_cost || 0;
  return `
<div class="day-card">
  <div class="day-header">
    <div class="day-num">${day.day_number}</div>
    <div class="day-info">
      <h4>Day ${day.day_number} &nbsp;<span style="font-weight:400;color:var(--faint)">${day.date || ''}</span></h4>
      <small>${allActs.length} activities</small>
    </div>
    <div class="day-right">
      ${w.icon ? `<div class="weather-pill">${w.icon} <b>${Math.round(w.temp_high||0)}°</b> / ${Math.round(w.temp_low||0)}° ${esc(w.condition||'')}</div>` : ''}
      <span class="day-cost">${fmtCurrency(cost, 'INR')}</span>
      <span class="chevron">▼</span>
    </div>
  </div>
  <div class="day-body" style="display:none">
    ${renderSlot('☀️ Morning', 'morning', day.morning)}
    ${renderSlot('☕ Afternoon', 'afternoon', day.afternoon)}
    ${renderSlot('🌙 Evening', 'evening', day.evening)}
  </div>
</div>`;
}

function renderSlot(label, cls, acts) {
  if (!acts || !acts.length) return '';
  return `
<div class="slot-title ${cls}">${label}</div>
${acts.map(renderActivity).join('')}`;
}

function renderActivity(a) {
  const typeClass = `type-${(a.type||'').toLowerCase().replace(/\s+/g,'-')}`;
  const priceTxt  = a.price > 0 ? fmtCurrency(a.price, a.currency || 'INR') : 'Free';
  const priceClass= a.price > 0 ? '' : 'free';
  return `
<div class="act-row">
  <div class="act-body">
    <div class="act-name">${esc(a.name)}</div>
    <div class="act-desc">${esc(a.description)}</div>
    <div class="act-meta">
      <span>⏱ ${a.duration_hours}h</span>
      ${a.best_time ? `<span>🕐 ${a.best_time}</span>` : ''}
      ${a.booking_required ? '<span>📌 Pre-book</span>' : ''}
    </div>
  </div>
  <div class="act-right">
    <span class="act-type-badge ${typeClass}">${esc(a.type||'activity')}</span>
    <div class="act-price ${priceClass}">${priceTxt}</div>
  </div>
</div>`;
}

// ────────────────────────────────────────────────────────────────────────────
// Flights
// ────────────────────────────────────────────────────────────────────────────
function renderFlightCard(f, idx) {
  const isTop = idx === 0;
  return `
<div class="flight-card ${isTop ? 'top' : ''}">
  <div class="flight-icon">✈️</div>
  <div class="flight-info">
    <div class="flight-airline">
      <span class="airline-name">${esc(f.airline)}</span>
      <span class="flight-num">${esc(f.flight_number)}</span>
      ${isTop ? '<span class="rec-pill">⭐ AI Recommended</span>' : ''}
    </div>
    <div class="flight-route">
      <span class="f-time">${esc(f.departure_time)}</span>
      <div class="f-line"></div>
      <span class="f-stop">${f.stops === 0 ? 'Direct' : f.stops + ' stop'}</span>
      <div class="f-line"></div>
      <span class="f-time">${esc(f.arrival_time)}</span>
    </div>
    <div class="f-meta">
      <span>⏱ ${esc(f.duration)}</span>
      <span>${esc(f.cabin_class)}</span>
    </div>
  </div>
  <div class="flight-price">
    <div class="fp-amount">${fmtCurrency(f.price, f.currency)}</div>
    <a href="${esc(f.booking_url)}" target="_blank" class="fp-book">Book →</a>
  </div>
</div>`;
}

// ────────────────────────────────────────────────────────────────────────────
// Hotels
// ────────────────────────────────────────────────────────────────────────────
function renderHotelCard(h, idx) {
  const isTop = idx === 0;
  const stars = '⭐'.repeat(Math.min(h.stars || 3, 5));
  return `
<div class="hotel-card ${isTop ? 'top' : ''}">
  <div class="hotel-img-placeholder">🏨</div>
  <div class="hotel-body">
    ${isTop ? '<div style="font-size:10px;color:#6ee7b7;font-weight:700;margin-bottom:4px">⭐ AI Top Pick</div>' : ''}
    <div class="hotel-name">${esc(h.name)}</div>
    <div class="hotel-stars">${stars} <span style="color:var(--faint);font-size:11px">(${h.rating})</span></div>
    <div class="hotel-price-row">
      <div>
        <div class="h-price">${fmtCurrency(h.price_per_night, h.currency)}</div>
        <div class="h-per">per night</div>
      </div>
      <a href="${esc(h.booking_url)}" target="_blank" style="font-size:11px;color:var(--blue)">Book →</a>
    </div>
    <div class="amenity-list">
      ${(h.amenities||[]).slice(0,5).map(a => `<span class="amenity">${esc(a)}</span>`).join('')}
    </div>
  </div>
</div>`;
}

// ────────────────────────────────────────────────────────────────────────────
// Budget
// ────────────────────────────────────────────────────────────────────────────
function renderBudget(b) {
  if (!b) return '<div class="info-card"><p style="color:var(--faint)">Budget data unavailable.</p></div>';
  const items = [
    { icon:'✈️', label:'Flights',       val: b.flights       || 0 },
    { icon:'🏨', label:'Accommodation', val: b.accommodation  || 0 },
    { icon:'🎯', label:'Activities',    val: b.activities    || 0 },
    { icon:'🍽️', label:'Meals',        val: b.meals         || 0 },
    { icon:'🚌', label:'Transport',     val: b.transport     || 0 },
    { icon:'💡', label:'Misc',          val: b.miscellaneous || 0 },
  ];
  const max     = Math.max(...items.map(i => i.val), 1);
  const cur     = b.currency || 'INR';
  const within  = b.within_budget;
  const remaining = b.remaining || 0;

  return `
<div class="budget-card">
  <h4 style="margin-bottom:18px">💰 Budget Breakdown</h4>
  ${items.map(i => `
  <div class="budget-row">
    <span class="b-icon">${i.icon}</span>
    <span class="b-label">${i.label}</span>
    <div class="b-bar-wrap">
      <div class="b-bar-bg">
        <div class="b-bar" style="width:${Math.round((i.val/max)*100)}%"></div>
      </div>
    </div>
    <span class="b-val">${fmtCurrency(i.val, cur)}</span>
  </div>`).join('')}
  <div class="b-total">
    <span class="b-total-label">Total Estimate</span>
    <span class="b-total-val">${fmtCurrency(b.total || 0, cur)}</span>
  </div>
  <div class="b-status ${within ? 'ok' : 'over'}">
    ${within
      ? `✅ Within budget! You have ${fmtCurrency(Math.abs(remaining), cur)} to spare for shopping.`
      : `⚠️ Over budget by ${fmtCurrency(Math.abs(remaining), cur)}. Consider choosing a cheaper hotel or fewer activities.`}
  </div>
</div>`;
}

// ────────────────────────────────────────────────────────────────────────────
// Tips + Cuisine
// ────────────────────────────────────────────────────────────────────────────
function renderTips(info) {
  const tips = info.travel_tips || [];
  if (!tips.length) return '';
  return `
<div class="info-card" style="margin-top:10px">
  <h4>💡 Travel Tips</h4>
  <ul class="tip-list">
    ${tips.map(t => `<li>${esc(t)}</li>`).join('')}
  </ul>
  ${info.cultural_notes ? `<p style="margin-top:10px;font-size:13px;color:var(--muted)">🎭 ${esc(info.cultural_notes)}</p>` : ''}
</div>`;
}

function renderCuisine(info) {
  const dishes = info.local_cuisine || [];
  if (!dishes.length) return '';
  return `
<div class="info-card">
  <h4>🍽️ Must-Try Food</h4>
  <div class="cuisine-tags">
    ${dishes.map(d => `<span class="cuisine-tag">${esc(d)}</span>`).join('')}
  </div>
</div>`;
}

// ────────────────────────────────────────────────────────────────────────────
// Agent panel helpers
// ────────────────────────────────────────────────────────────────────────────
const AGENT_IDS = [
  'flight_agent', 'hotel_agent', 'weather_agent',
  'activity_agent', 'budget_agent', 'itinerary_agent',
];

function resetAgentPanel() {
  AGENT_IDS.forEach(id => setAgentStatus(id, 'pending'));
  const el = document.getElementById('log-scroll');
  if (el) el.innerHTML = '';
}

function updateAgentDots(statuses) {
  Object.entries(statuses).forEach(([id, st]) => setAgentStatus(id, st));
}

function setAgentStatus(id, status) {
  const row   = document.getElementById(`agent-row-${id}`);
  const dot   = document.getElementById(`dot-${id}`);
  const badge = document.getElementById(`badge-${id}`);
  if (!row) return;

  row.className   = `agent-row ${status}`;
  dot.className   = `agent-dot ${status}`;
  badge.className = `agent-badge ${status}`;

  const labels = { pending:'Pending', running:'Running…', completed:'Done ✓', error:'Error' };
  badge.textContent = labels[status] || status;
}

function appendLog(msg) {
  const el = document.getElementById('log-scroll');
  if (!el) return;
  const div = document.createElement('div');
  div.className   = 'log-line';
  div.innerHTML   = msg.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}

// ────────────────────────────────────────────────────────────────────────────
// Placeholder screens
// ────────────────────────────────────────────────────────────────────────────
function showWelcome() {
  document.getElementById('main-content').innerHTML = `
<div class="welcome">
  <div class="big-icon">✈️</div>
  <h2>AI Travel Itinerary Planner</h2>
  <p>Fill in your trip details on the left and click <strong>Generate AI Itinerary</strong>. Six specialised AI agents will work in parallel to plan your perfect trip.</p>
  <p style="margin-top:8px;font-size:12px;opacity:.5">Powered by LangGraph · MCP · A2A · Amadeus · Claude LLM</p>
</div>`;
}

function showLoading(msg) {
  document.getElementById('main-content').innerHTML = `
<div class="loading">
  <div class="spinner"></div>
  <div class="loading-msg">${esc(msg)}</div>
  <div class="loading-sub">AI agents are working in parallel…</div>
</div>`;
}

function showError(msg) {
  document.getElementById('main-content').innerHTML = `
<div class="error-box">❌ <strong>Error:</strong> ${esc(msg)}<br><br>
Make sure the backend is running: <code>uvicorn backend.main:app --reload --port 8000</code></div>`;
}

function resetGenBtn() {
  const btn = document.getElementById('gen-btn');
  btn.disabled  = false;
  btn.innerHTML = '✨ Generate AI Itinerary';
}

// ────────────────────────────────────────────────────────────────────────────
// Utilities
// ────────────────────────────────────────────────────────────────────────────
function fmtCurrency(val, cur) {
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency', currency: cur || 'INR', maximumFractionDigits: 0,
    }).format(val);
  } catch (_) {
    return `${cur} ${Math.round(val).toLocaleString()}`;
  }
}

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
