/**
 * Calendar & Reminder Studio - Frontend Engine
 * Handles interactive monthly grid, real-time reminders CRUD,
 * Web Audio API chime alerts, live digital clock, and search filters.
 */

// Category Metadata - Harmonized with Calenda Bell & Calendar Logo
const CATEGORIES = {
    Work: { color: '#e83848', icon: '💼', className: 'cat-work' },
    Personal: { color: '#10b981', icon: '🏠', className: 'cat-personal' },
    Meeting: { color: '#8b5cf6', icon: '👥', className: 'cat-meeting' },
    Urgent: { color: '#dc2626', icon: '🚨', className: 'cat-urgent' },
    General: { color: '#f59e0b', icon: '📌', className: 'cat-general' }
};

// Global State
const state = {
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1, // 1-12
    selectedDate: formatDate(new Date()),
    activeFilter: 'date', // 'date' | 'today' | 'upcoming' | 'all'
    searchQuery: '',
    monthReminders: {},
    audioContext: null,
    editingReminderId: null,
    activeToasts: new Set()
};

// DOM Selectors
const DOM = {
    // Clock
    clockDisplay: document.getElementById('live-clock-display'),
    dateDisplay: document.getElementById('live-date-display'),
    themeToggle: document.getElementById('btn-theme-toggle'),

    // Calendar
    calHeading: document.getElementById('calendar-heading'),
    calContainer: document.getElementById('calendar-days-container'),
    btnPrevMonth: document.getElementById('btn-prev-month'),
    btnNextMonth: document.getElementById('btn-next-month'),
    btnJumpToday: document.getElementById('btn-jump-today'),

    // Reminders
    remindersList: document.getElementById('reminders-list-container'),
    remindersTitle: document.getElementById('reminders-panel-title'),
    reminderCountBadge: document.getElementById('badge-reminder-count'),
    searchInput: document.getElementById('input-search-reminders'),
    btnClearSearch: document.getElementById('btn-clear-search'),
    filterTabs: document.querySelectorAll('.filter-tab'),

    // Stats
    statTotal: document.getElementById('val-stat-total'),
    statToday: document.getElementById('val-stat-today'),
    statUpcoming: document.getElementById('val-stat-upcoming'),
    statCompleted: document.getElementById('val-stat-completed'),

    // Modal
    modalBackdrop: document.getElementById('modal-reminder-backdrop'),
    modalTitle: document.getElementById('modal-dialog-title'),
    modalCloseBtn: document.getElementById('btn-close-modal'),
    modalCancelBtn: document.getElementById('btn-cancel-modal'),
    btnOpenCreate: document.getElementById('btn-open-create-modal'),
    formReminder: document.getElementById('form-reminder'),
    formId: document.getElementById('form-reminder-id'),
    formTitle: document.getElementById('form-title'),
    formDate: document.getElementById('form-date'),
    formTime: document.getElementById('form-time'),
    formCategory: document.getElementById('form-category'),
    formDesc: document.getElementById('form-desc'),
    formAlarmEnabled: document.getElementById('form-alarm-enabled'),
    btnShortcutToday: document.getElementById('btn-shortcut-today'),
    btnShortcutTomorrow: document.getElementById('btn-shortcut-tomorrow'),

    // Alarms
    btnTestAlarm: document.getElementById('btn-test-alarm'),
    toastContainer: document.getElementById('alarm-toast-container')
};

/* ==========================================================================
   Helper Functions
   ========================================================================== */

function formatDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function getMonthName(monthNumber) {
    const names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return names[monthNumber - 1];
}

function formatDisplayDate(dateStr) {
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
    return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}

/* ==========================================================================
   Web Audio API - Melodic Chime Synthesizer
   ========================================================================== */

function playChime() {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;

        if (!state.audioContext) {
            state.audioContext = new AudioContext();
        }
        if (state.audioContext.state === 'suspended') {
            state.audioContext.resume();
        }

        const ctx = state.audioContext;
        const now = ctx.currentTime;

        // Two-tone bell chime: G5 (784Hz) then C6 (1046Hz)
        const notes = [
            { freq: 784, start: now, dur: 0.25 },
            { freq: 1046, start: now + 0.15, dur: 0.45 }
        ];

        notes.forEach(({ freq, start, dur }) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, start);

            gain.gain.setValueAtTime(0, start);
            gain.gain.linearRampToValueAtTime(0.35, start + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.0001, start + dur);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start(start);
            osc.stop(start + dur);
        });
    } catch (e) {
        console.warn('Audio playback notice:', e);
    }
}

/* ==========================================================================
   Live Digital Clock
   ========================================================================== */

function updateLiveClock() {
    const now = new Date();
    DOM.clockDisplay.textContent = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
    DOM.dateDisplay.textContent = now.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}
setInterval(updateLiveClock, 1000);
updateLiveClock();

/* ==========================================================================
   Calendar Grid Rendering
   ========================================================================== */

async function fetchMonthReminders() {
    try {
        const res = await fetch(`/api/reminders/month?year=${state.currentYear}&month=${state.currentMonth}`);
        state.monthReminders = await res.json();
    } catch (e) {
        console.error('Failed to load month reminders:', e);
        state.monthReminders = {};
    }
}

async function renderCalendar() {
    await fetchMonthReminders();

    DOM.calHeading.textContent = `${getMonthName(state.currentMonth)} ${state.currentYear}`;
    DOM.calContainer.innerHTML = '';

    const firstDayIndex = new Date(state.currentYear, state.currentMonth - 1, 1).getDay();
    // Monday start: 0 = Mon, ..., 6 = Sun
    const startOffset = (firstDayIndex + 6) % 7;
    const totalDaysInMonth = new Date(state.currentYear, state.currentMonth, 0).getDate();

    const todayStr = formatDate(new Date());

    // Fill leading empty cells
    for (let i = 0; i < startOffset; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'day-cell empty';
        DOM.calContainer.appendChild(emptyCell);
    }

    // Fill active month days
    for (let day = 1; day <= totalDaysInMonth; day++) {
        const dateStr = `${state.currentYear}-${String(state.currentMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isToday = (dateStr === todayStr);
        const isSelected = (dateStr === state.selectedDate);

        const dayReminders = state.monthReminders[dateStr] || [];
        const count = dayReminders.length;

        const cell = document.createElement('div');
        cell.className = `day-cell ${isToday ? 'is-today' : ''} ${isSelected ? 'is-selected' : ''}`;
        cell.dataset.date = dateStr;

        // Day Header
        const header = document.createElement('div');
        header.className = 'day-header';

        const dayNum = document.createElement('span');
        dayNum.className = 'day-number';
        dayNum.textContent = day;
        header.appendChild(dayNum);

        if (isToday) {
            const todayPill = document.createElement('span');
            todayPill.className = 'today-pill';
            todayPill.textContent = 'Today';
            header.appendChild(todayPill);
        }
        cell.appendChild(header);

        // Reminders Badges in Cell
        if (count > 0) {
            const badgesWrap = document.createElement('div');
            badgesWrap.className = 'day-badges';

            const uncompleted = dayReminders.filter(r => !r.completed).length;
            const chip = document.createElement('div');
            chip.className = 'day-event-chip';
            chip.style.backgroundColor = uncompleted > 0 ? '#e83848' : '#10b981';
            chip.textContent = `● ${count} event${count > 1 ? 's' : ''}`;
            badgesWrap.appendChild(chip);

            cell.appendChild(badgesWrap);
        }

        cell.addEventListener('click', () => {
            selectDate(dateStr);
        });

        DOM.calContainer.appendChild(cell);
    }
}

function selectDate(dateStr) {
    state.selectedDate = dateStr;
    state.activeFilter = 'date';
    state.searchQuery = '';
    DOM.searchInput.value = '';
    DOM.btnClearSearch.classList.add('hidden');

    updateFilterTabsUI();
    renderCalendar();
    renderRemindersList();
}

function prevMonth() {
    if (state.currentMonth === 1) {
        state.currentMonth = 12;
        state.currentYear--;
    } else {
        state.currentMonth--;
    }
    renderCalendar();
}

function nextMonth() {
    if (state.currentMonth === 12) {
        state.currentMonth = 1;
        state.currentYear++;
    } else {
        state.currentMonth++;
    }
    renderCalendar();
}

function jumpToToday() {
    const today = new Date();
    state.currentYear = today.getFullYear();
    state.currentMonth = today.getMonth() + 1;
    selectDate(formatDate(today));
}

/* ==========================================================================
   Reminders List & CRUD
   ========================================================================== */

async function fetchReminders() {
    let url = '/api/reminders?';
    if (state.searchQuery) {
        url += `q=${encodeURIComponent(state.searchQuery)}`;
    } else if (state.activeFilter === 'date') {
        url += `filter=date&date=${state.selectedDate}`;
    } else {
        url += `filter=${state.activeFilter}`;
    }

    try {
        const res = await fetch(url);
        return await res.json();
    } catch (e) {
        console.error('Failed to fetch reminders:', e);
        return [];
    }
}

async function renderRemindersList() {
    const reminders = await fetchReminders();
    DOM.remindersList.innerHTML = '';

    // Update panel title & count
    if (state.searchQuery) {
        DOM.remindersTitle.textContent = `Search: "${state.searchQuery}"`;
    } else if (state.activeFilter === 'date') {
        DOM.remindersTitle.textContent = formatDisplayDate(state.selectedDate);
    } else if (state.activeFilter === 'today') {
        DOM.remindersTitle.textContent = "Today's Reminders";
    } else if (state.activeFilter === 'upcoming') {
        DOM.remindersTitle.textContent = 'Upcoming Reminders';
    } else {
        DOM.remindersTitle.textContent = 'All Reminders';
    }

    DOM.reminderCountBadge.textContent = `${reminders.length} item${reminders.length !== 1 ? 's' : ''}`;

    if (reminders.length === 0) {
        renderEmptyState();
        return;
    }

    reminders.forEach(reminder => {
        const card = createReminderCard(reminder);
        DOM.remindersList.appendChild(card);
    });
}

function renderEmptyState() {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.innerHTML = `
        <div class="empty-icon" aria-hidden="true">📅✨</div>
        <div class="empty-title">No Reminders Found</div>
        <p class="empty-subtitle">You have no tasks scheduled for this view. Create one to stay organized!</p>
        <button type="button" class="btn btn-primary" id="btn-empty-add">
            <span>＋ Add Reminder for this Date</span>
        </button>
    `;
    empty.querySelector('#btn-empty-add').addEventListener('click', openCreateModal);
    DOM.remindersList.appendChild(empty);
}

function createReminderCard(rem) {
    const card = document.createElement('article');
    card.className = `reminder-card ${rem.completed ? 'completed' : ''}`;
    card.id = `reminder-card-${rem.id}`;

    const catInfo = CATEGORIES[rem.category] || CATEGORIES.General;

    card.innerHTML = `
        <div class="reminder-checkbox-wrapper">
            <button type="button" class="custom-checkbox" aria-label="Toggle completed" title="Toggle status">
                <span>✓</span>
            </button>
        </div>
        <div class="reminder-body">
            <div class="reminder-meta-row">
                <span class="badge ${catInfo.className}">${catInfo.icon} ${rem.category}</span>
                <span class="time-chip">⏰ ${rem.time}</span>
                ${(state.activeFilter !== 'date' || state.searchQuery) ? `<span class="date-chip">📅 ${rem.date}</span>` : ''}
                ${rem.alarm_enabled ? `<span class="alarm-chip">🔔 Alert ON</span>` : ''}
            </div>
            <h3 class="reminder-title">${escapeHtml(rem.title)}</h3>
            ${rem.description ? `<p class="reminder-desc">${escapeHtml(rem.description)}</p>` : ''}
        </div>
        <div class="reminder-actions">
            <button type="button" class="btn-action-icon edit" title="Edit reminder" aria-label="Edit">✏️</button>
            <button type="button" class="btn-action-icon delete" title="Delete reminder" aria-label="Delete">🗑️</button>
        </div>
    `;

    // Checkbox toggle
    const chk = card.querySelector('.custom-checkbox');
    chk.addEventListener('click', () => toggleReminderCompleted(rem.id));

    // Edit button
    card.querySelector('.btn-action-icon.edit').addEventListener('click', () => openEditModal(rem));

    // Delete button
    card.querySelector('.btn-action-icon.delete').addEventListener('click', () => deleteReminder(rem.id));

    return card;
}

async function toggleReminderCompleted(id) {
    try {
        await fetch(`/api/reminders/${id}/toggle`, { method: 'POST' });
        refreshAllViews();
    } catch (e) {
        console.error('Failed to toggle completion:', e);
    }
}

async function deleteReminder(id) {
    if (!confirm('Are you sure you want to delete this reminder?')) return;
    try {
        await fetch(`/api/reminders/${id}`, { method: 'DELETE' });
        refreshAllViews();
    } catch (e) {
        console.error('Failed to delete reminder:', e);
    }
}

/* ==========================================================================
   Dashboard Metrics
   ========================================================================== */

async function updateStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        DOM.statTotal.textContent = data.total || 0;
        DOM.statToday.textContent = data.today_pending || 0;
        DOM.statUpcoming.textContent = data.upcoming || 0;
        DOM.statCompleted.textContent = data.completed || 0;
    } catch (e) {
        console.error('Failed to fetch stats:', e);
    }
}

/* ==========================================================================
   Modal Dialog Management
   ========================================================================== */

function openCreateModal() {
    state.editingReminderId = null;
    DOM.modalTitle.textContent = '➕ Add New Reminder';
    DOM.formId.value = '';
    DOM.formTitle.value = '';
    DOM.formDate.value = state.selectedDate;

    // Set next rounded hour
    const nextHour = new Date(Date.now() + 3600000);
    DOM.formTime.value = `${String(nextHour.getHours()).padStart(2, '0')}:00`;

    DOM.formCategory.value = 'General';
    DOM.formDesc.value = '';
    DOM.formAlarmEnabled.checked = true;

    DOM.modalBackdrop.classList.remove('hidden');
    DOM.formTitle.focus();
}

function openEditModal(rem) {
    state.editingReminderId = rem.id;
    DOM.modalTitle.textContent = '✏️ Edit Reminder';
    DOM.formId.value = rem.id;
    DOM.formTitle.value = rem.title;
    DOM.formDate.value = rem.date;
    DOM.formTime.value = rem.time;
    DOM.formCategory.value = rem.category || 'General';
    DOM.formDesc.value = rem.description || '';
    DOM.formAlarmEnabled.checked = Boolean(rem.alarm_enabled);

    DOM.modalBackdrop.classList.remove('hidden');
    DOM.formTitle.focus();
}

function closeModal() {
    DOM.modalBackdrop.classList.add('hidden');
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const title = DOM.formTitle.value.trim();
    const dateVal = DOM.formDate.value.trim();
    const timeVal = DOM.formTime.value.trim();
    const category = DOM.formCategory.value;
    const description = DOM.formDesc.value.trim();
    const alarm_enabled = DOM.formAlarmEnabled.checked;

    if (!title || !dateVal || !timeVal) {
        alert('Please fill out the title, date, and time fields.');
        return;
    }

    const payload = {
        title,
        date: dateVal,
        time: timeVal,
        category,
        description,
        alarm_enabled
    };

    try {
        if (state.editingReminderId) {
            await fetch(`/api/reminders/${state.editingReminderId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            await fetch('/api/reminders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            state.selectedDate = dateVal;
        }

        closeModal();
        refreshAllViews();
    } catch (err) {
        console.error('Failed to save reminder:', err);
        alert('An error occurred while saving the reminder.');
    }
}

/* ==========================================================================
   Background Alarm Engine & Pop-up Toasts
   ========================================================================== */

async function checkDueReminders() {
    try {
        const res = await fetch('/api/reminders/due');
        const dueList = await res.json();

        if (Array.isArray(dueList) && dueList.length > 0) {
            for (const rem of dueList) {
                if (state.activeToasts.has(rem.id)) continue;
                state.activeToasts.add(rem.id);

                // Mark notified on backend
                await fetch(`/api/reminders/${rem.id}/notify`, { method: 'POST' });

                // Play audio chime
                playChime();

                // Trigger in-app toast notification
                showAlarmToast(rem);
            }
            refreshAllViews();
        }
    } catch (e) {
        // Silently catch background poll issues
    }
}

function showAlarmToast(rem) {
    const toast = document.createElement('div');
    toast.className = 'alarm-card-toast';
    toast.id = `toast-${rem.id}`;

    const catInfo = CATEGORIES[rem.category] || CATEGORIES.General;

    toast.innerHTML = `
        <div class="alarm-toast-header">
            <span>🔔 REMINDER ALERT</span>
            <span>⏰ ${rem.time}</span>
        </div>
        <div class="alarm-toast-body">
            <span class="badge ${catInfo.className}" style="margin-bottom: 6px;">${catInfo.icon} ${rem.category}</span>
            <div class="alarm-toast-title">${escapeHtml(rem.title)}</div>
            ${rem.description ? `<div class="alarm-toast-desc">${escapeHtml(rem.description)}</div>` : ''}
            <div class="alarm-toast-actions">
                <button type="button" class="btn-toast dismiss">Dismiss</button>
                <button type="button" class="btn-toast snooze">Snooze 5m</button>
                <button type="button" class="btn-toast done">✓ Done</button>
            </div>
        </div>
    `;

    toast.querySelector('.dismiss').addEventListener('click', () => {
        closeToast(rem.id);
    });

    toast.querySelector('.snooze').addEventListener('click', async () => {
        await fetch(`/api/reminders/${rem.id}/snooze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ minutes: 5 })
        });
        closeToast(rem.id);
        refreshAllViews();
    });

    toast.querySelector('.done').addEventListener('click', async () => {
        await fetch(`/api/reminders/${rem.id}/toggle`, { method: 'POST' });
        closeToast(rem.id);
        refreshAllViews();
    });

    DOM.toastContainer.appendChild(toast);
}

function closeToast(id) {
    const el = document.getElementById(`toast-${id}`);
    if (el) el.remove();
    state.activeToasts.delete(id);
}

// Background poll loop every 3 seconds
setInterval(checkDueReminders, 3000);

/* ==========================================================================
   Theme Management
   ========================================================================== */

function initTheme() {
    const savedTheme = localStorage.getItem('theme_preference') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme_preference', next);
}

/* ==========================================================================
   UI Event Bindings & Initialization
   ========================================================================== */

function updateFilterTabsUI() {
    DOM.filterTabs.forEach(tab => {
        if (tab.dataset.filter === state.activeFilter) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function refreshAllViews() {
    renderCalendar();
    renderRemindersList();
    updateStats();
}

function setupEventListeners() {
    // Calendar Navigation
    DOM.btnPrevMonth.addEventListener('click', prevMonth);
    DOM.btnNextMonth.addEventListener('click', nextMonth);
    DOM.btnJumpToday.addEventListener('click', jumpToToday);

    // Theme Toggle
    DOM.themeToggle.addEventListener('click', toggleTheme);

    // Test Alarm Button
    DOM.btnTestAlarm.addEventListener('click', () => {
        playChime();
        showAlarmToast({
            id: 'test-' + Date.now(),
            title: 'Test Reminder Notification',
            time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
            category: 'Urgent',
            description: 'Melodic chime and pop-up notifications are functioning properly in your browser!'
        });
    });

    // Filter Tabs
    DOM.filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            state.activeFilter = tab.dataset.filter;
            state.searchQuery = '';
            DOM.searchInput.value = '';
            DOM.btnClearSearch.classList.add('hidden');
            updateFilterTabsUI();
            renderRemindersList();
        });
    });

    // Stat Cards Clicks
    document.getElementById('stat-total').addEventListener('click', () => {
        state.activeFilter = 'all';
        updateFilterTabsUI();
        renderRemindersList();
    });
    document.getElementById('stat-today-pending').addEventListener('click', () => {
        state.activeFilter = 'today';
        updateFilterTabsUI();
        renderRemindersList();
    });
    document.getElementById('stat-upcoming').addEventListener('click', () => {
        state.activeFilter = 'upcoming';
        updateFilterTabsUI();
        renderRemindersList();
    });
    document.getElementById('stat-completed').addEventListener('click', () => {
        state.activeFilter = 'all';
        updateFilterTabsUI();
        renderRemindersList();
    });

    // Search Input
    DOM.searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value.trim();
        if (state.searchQuery) {
            DOM.btnClearSearch.classList.remove('hidden');
        } else {
            DOM.btnClearSearch.classList.add('hidden');
        }
        renderRemindersList();
    });

    DOM.btnClearSearch.addEventListener('click', () => {
        DOM.searchInput.value = '';
        state.searchQuery = '';
        DOM.btnClearSearch.classList.add('hidden');
        renderRemindersList();
    });

    // Modal Events
    DOM.btnOpenCreate.addEventListener('click', openCreateModal);
    DOM.modalCloseBtn.addEventListener('click', closeModal);
    DOM.modalCancelBtn.addEventListener('click', closeModal);
    DOM.modalBackdrop.addEventListener('click', (e) => {
        if (e.target === DOM.modalBackdrop) closeModal();
    });
    DOM.formReminder.addEventListener('submit', handleFormSubmit);

    // Modal Shortcuts
    DOM.btnShortcutToday.addEventListener('click', () => {
        DOM.formDate.value = formatDate(new Date());
    });
    DOM.btnShortcutTomorrow.addEventListener('click', () => {
        const tmrw = new Date();
        tmrw.setDate(tmrw.getDate() + 1);
        DOM.formDate.value = formatDate(tmrw);
    });
}

// Initial boot
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setupEventListeners();
    refreshAllViews();
});
