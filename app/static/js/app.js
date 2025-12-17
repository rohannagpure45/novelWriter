/**
 * Novel Engine UI - Core Application Logic
 */

const API_BASE = ''; // Relative path since served from same origin

// State
const state = {
    currentView: 'dashboard',
    projects: [],
    currentProject: null,
    scenes: [],
    characters: [],
    currentScene: null
};

// DOM Elements (initialized in DOMContentLoaded)
let mainContent;
let modalOverlay;

// --- Utilities ---
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

// --- API Client ---
const api = {
    async get(endpoint) {
        const res = await fetch(`${API_BASE}${endpoint}`);
        if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
        return res.json();
    },
    async post(endpoint, data) {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
        return res.json();
    },
    async put(endpoint, data) {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
        return res.json();
    },
    async delete(endpoint) {
        const res = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
        return true;
    }
};

// --- Views ---

function loadDashboardView() {
    mainContent.innerHTML = `
        <div class="view-header">
            <h2 class="view-title">Projects</h2>
            <button class="btn btn-primary" onclick="showCreateProjectModal()">+ New Project</button>
        </div>
        <div class="card-grid" id="project-list">
            <!-- Projects injected here -->
        </div>
    `;
    loadProjects();
    updateSidebar('dashboard');
}

async function loadProjects() {
    try {
        const projects = await api.get('/projects');
        state.projects = projects;
        const grid = document.getElementById('project-list');

        if (projects.length === 0) {
            grid.innerHTML = `<p class="text-secondary">No projects found. Create one to get started.</p>`;
            return;
        }

        grid.innerHTML = projects.map(p => `
            <div class="card" tabindex="0" role="button" onclick="openProject(${p.id})" onkeydown="if(event.key==='Enter'||event.key===' '){openProject(${p.id});event.preventDefault();}">
                <h3>${escapeHtml(p.name)}</h3>
                <p>${escapeHtml(p.description) || 'No description'}</p>
                <div class="flex justify-between items-center" style="margin-top: 1rem;">
                    <span class="text-sm text-secondary">ID: ${p.id}</span>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
        alert('Failed to load projects');
    }
}

async function openProject(id) {
    try {
        state.currentProject = state.projects.find(p => p.id === id);
        if (!state.currentProject) {
            // Fetch strictly if not in memory
            state.currentProject = await api.get(`/projects/${id}`);
        }
        renderProjectView();
    } catch (err) {
        console.error(err);
        alert('Failed to open project');
    }
}

function renderProjectView() {
    const p = state.currentProject;
    mainContent.innerHTML = `
        <div class="view-header">
            <div>
                <button class="btn text-sm" onclick="renderDashboard()">← Back</button>
                <h2 class="view-title" style="margin-top: 0.5rem;">${escapeHtml(p.name)}</h2>
                <p class="text-secondary">${escapeHtml(p.description) || ''}</p>
            </div>
            <div class="flex gap-2">
                 <button class="btn" onclick="showCreateCharacterModal()">+ Character</button>
                 <button class="btn btn-primary" onclick="showCreateSceneModal()">+ Scene</button>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 300px 1fr; gap: 2rem;">
            <!-- Characters Sidebar -->
            <div>
                <h3 class="text-lg font-bold" style="margin-bottom: 1rem;">Characters</h3>
                <div id="character-list" class="flex flex-col gap-2">
                    <!-- Loaded async -->
                </div>
            </div>

            <!-- Scenes List -->
            <div>
                <h3 class="text-lg font-bold" style="margin-bottom: 1rem;">Scenes</h3>
                <div id="scene-list" class="flex flex-col gap-4">
                    <!-- Loaded async -->
                </div>
            </div>
        </div>
    `;
    loadProjectDetails(p.id);
}

async function loadProjectDetails(projectId) {
    // Load Characters
    const chars = await api.get(`/projects/${projectId}/characters`);
    state.characters = chars;
    document.getElementById('character-list').innerHTML = chars.map(c => `
        <div class="card" style="padding: 1rem;">
            <strong>${escapeHtml(c.name)}</strong>
            <p class="text-sm text-secondary">ID: ${c.id}</p>
        </div>
    `).join('');

    // Load Scenes
    const scenes = await api.get(`/projects/${projectId}/scenes`);
    state.scenes = scenes;
    document.getElementById('scene-list').innerHTML = scenes.map(s => {
        const title = (s.card_jsonb && s.card_jsonb.title) ? s.card_jsonb.title : `Scene ${s.scene_no}`;
        return `
        <div class="card" tabindex="0" role="button" onclick="openScene(${s.id})" onkeydown="if(event.key==='Enter'||event.key===' '){openScene(${s.id});event.preventDefault();}">
            <div class="flex justify-between">
                <strong>${escapeHtml(title)}</strong>
                <span class="text-sm text-secondary">Ch ${s.chapter_no} / Sc ${s.scene_no}</span>
            </div>
        </div>
        `;
    }).join('');
}

async function openScene(sceneId) {
    const scene = await api.get(`/scenes/${sceneId}`);
    state.currentScene = scene;

    // Attempt to get latest draft content
    let content = "";
    try {
        const drafts = await api.get(`/scenes/${sceneId}/drafts`);
        if (drafts.length > 0) {
            content = drafts[0].text; // Fixed: DraftRead uses 'text' not 'content', verifying schema... DraftBase: text: str.
        }
    } catch (e) { console.warn("No drafts found", e); }

    const title = (scene.card_jsonb && scene.card_jsonb.title) ? scene.card_jsonb.title : `Scene ${scene.scene_no}`;

    mainContent.innerHTML = `
        <div class="view-header">
            <div>
                 <button class="btn text-sm" onclick="renderProjectView()">← Project</button>
                 <h2 class="view-title" style="margin-top:0.5rem;">${escapeHtml(title)}</h2>
            </div>
            <div class="flex gap-2">
                <button class="btn" onclick="runPipeline(${sceneId})">✨ Run Pipeline</button>
                <button class="btn btn-primary" onclick="saveDraft(${sceneId})">Save Draft</button>
            </div>
        </div>

        <div class="editor-container">
            <div class="editor-toolbar">
                <span class="text-sm text-secondary">Ch ${scene.chapter_no} / Sc ${scene.scene_no}</span>
                <span class="text-sm text-secondary">Words: <span id="word-count">0</span></span>
            </div>
            <textarea id="scene-editor" class="editor-textarea" placeholder="Start writing..."></textarea>
        </div>
    `;

    // Set content via .value to prevent XSS
    document.getElementById('scene-editor').value = content;

    document.getElementById('scene-editor').addEventListener('input', (e) => {
        const text = e.target.value;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        document.getElementById('word-count').textContent = words;
    });
}

// --- Actions ---

async function saveDraft(sceneId) {
    const content = document.getElementById('scene-editor').value;
    try {
        await api.post(`/scenes/${sceneId}/drafts`, {
            text: content,
            version_notes: "Manual save from web UI"
        });
        alert('Draft saved!');
    } catch (e) {
        alert('Error saving draft: ' + e.message);
    }
}

async function runPipeline(sceneId) {
    if (!confirm('Start pipeline iteration? this will analyze the current draft.')) return;
    try {
        await api.post(`/pipeline/scenes/${sceneId}/run`, { max_attempts: 3 });
        alert('Pipeline started! Check console/worker for progress.');
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

// --- Modals ---

function showCreateProjectModal() {
    showModal(`
        <h3 class="text-lg font-bold" style="margin-bottom:1rem;">New Project</h3>
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="new-proj-title">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea id="new-proj-desc"></textarea>
        </div>
        <div class="flex justify-between">
            <button class="btn" onclick="hideModal()">Cancel</button>
            <button class="btn btn-primary" onclick="createProject()">Create</button>
        </div>
    `);
}

async function createProject() {
    const title = document.getElementById('new-proj-title').value;
    const description = document.getElementById('new-proj-desc').value;
    if (!title) return alert('Title required');

    try {
        await api.post('/projects', { name: title, description });
        hideModal();
        loadProjects();
    } catch (e) { alert(e.message); }
}

function showCreateCharacterModal() {
    if (!state.currentProject) return;
    showModal(`
        <h3 class="text-lg font-bold" style="margin-bottom:1rem;">New Character</h3>
        <div class="form-group">
            <label>Name</label>
            <input type="text" id="new-char-name">
        </div>
        <div class="flex justify-between">
            <button class="btn" onclick="hideModal()">Cancel</button>
            <button class="btn btn-primary" onclick="createCharacter()">Create</button>
        </div>
    `);
}

async function createCharacter() {
    const name = document.getElementById('new-char-name').value.trim();
    if (!name) return alert('Name required');

    try {
        await api.post(`/projects/${state.currentProject.id}/characters`, { name, data_jsonb: {} });
        hideModal();
        loadProjectDetails(state.currentProject.id);
    } catch (e) { alert(e.message); }
}

function showCreateSceneModal() {
    if (!state.currentProject) return;
    showModal(`
        <h3 class="text-lg font-bold" style="margin-bottom:1rem;">New Scene</h3>
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="new-scene-title">
        </div>
        <div class="flex gap-4">
             <div class="form-group flex-1">
                <label>Chapter</label>
                <input type="number" id="new-scene-ch" value="1">
            </div>
            <div class="form-group flex-1">
                <label>Scene #</label>
                <input type="number" id="new-scene-no" value="1">
            </div>
        </div>
        <div class="flex justify-between">
            <button class="btn" onclick="hideModal()">Cancel</button>
            <button class="btn btn-primary" onclick="createScene()">Create</button>
        </div>
    `);
}

async function createScene() {
    const title = document.getElementById('new-scene-title').value;
    const chapterInput = document.getElementById('new-scene-ch').value.trim();
    const sceneInput = document.getElementById('new-scene-no').value.trim();

    const chapter = parseInt(chapterInput, 10);
    const scene_number = parseInt(sceneInput, 10);

    // Validate chapter
    if (!Number.isFinite(chapter) || !Number.isInteger(chapter) || chapter < 1) {
        alert('Chapter must be a positive integer');
        return;
    }

    // Validate scene number
    if (!Number.isFinite(scene_number) || !Number.isInteger(scene_number) || scene_number < 1) {
        alert('Scene number must be a positive integer');
        return;
    }

    try {
        await api.post(`/projects/${state.currentProject.id}/scenes`, {
            chapter_no: chapter,
            scene_no: scene_number,
            card_jsonb: { title: title }
        });
        hideModal();
        loadProjectDetails(state.currentProject.id);
    } catch (e) { alert(e.message); }
}

// --- Modal Utilities ---
function showModal(content) {
    modalOverlay.innerHTML = `<div class="modal">${content}</div>`;
    modalOverlay.classList.remove('hidden');
}

function hideModal() {
    modalOverlay.classList.add('hidden');
    modalOverlay.innerHTML = '';
}

// --- Placeholders ---
function renderArchive() {
    mainContent.innerHTML = `
        <div class="view-header">
            <h2 class="view-title">Archive</h2>
        </div>
        <div class="card">
            <p class="text-secondary">Archive features coming soon.</p>
        </div>
    `;
    updateSidebar('archive');
}

function renderSettings() {
    mainContent.innerHTML = `
        <div class="view-header">
            <h2 class="view-title">Settings</h2>
        </div>
        <div class="card">
            <p class="text-secondary">Settings coming soon.</p>
        </div>
    `;
    updateSidebar('settings');
}

function updateSidebar(activeItem) {
    document.querySelectorAll('#sidebar li').forEach(li => li.classList.remove('active'));
    const map = { 'dashboard': 0, 'archive': 1, 'settings': 2 };
    const idx = map[activeItem] !== undefined ? map[activeItem] : 0;
    // Simple index based selection for now
    const items = document.querySelectorAll('#sidebar li');
    if (items[idx]) items[idx].classList.add('active');
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    // Initialize DOM elements
    mainContent = document.getElementById('main-content');
    modalOverlay = document.getElementById('modal-overlay');

    // Basic router logic
    loadDashboardView();

    // Expose functions globally for HTML event handlers
    window.showCreateProjectModal = showCreateProjectModal;
    window.createProject = createProject;
    window.hideModal = hideModal;
    window.openProject = openProject;
    window.renderDashboard = loadDashboardView;
    window.renderProjectView = renderProjectView;
    window.showCreateCharacterModal = showCreateCharacterModal;
    window.createCharacter = createCharacter;
    window.showCreateSceneModal = showCreateSceneModal;
    window.createScene = createScene;
    window.openScene = openScene;
    window.saveDraft = saveDraft;
    window.runPipeline = runPipeline;
    window.renderArchive = renderArchive;
    window.renderSettings = renderSettings;
});
