let processCount = 0;

// ── Persistence helpers ──────────────────────────────────────────────────────

function saveState() {
    const state = { processCount, processes: [] };

    for (let i = 1; i <= processCount; i++) {
        const tasksDiv = document.getElementById(`tasks_${i}`);
        if (!tasksDiv) continue;

        const tasks = [];
        for (const taskDiv of tasksDiv.children) {
            const input = taskDiv.querySelector('input[type="number"]');
            tasks.push(input ? input.value : '');
        }
        state.processes.push({ id: i, tasks });
    }

    localStorage.setItem('simulationState', JSON.stringify(state));
}

function loadState() {
    const raw = localStorage.getItem('simulationState');
    if (!raw) return;

    const state = JSON.parse(raw);
    processCount = 0;

    for (const process of state.processes) {
        addProcess();
        for (const taskValue of process.tasks) {
            addTask(processCount, taskValue);
        }
    }
}

// ── Core functions ───────────────────────────────────────────────────────────

function addProcess() {
    processCount++;
    const processesDiv = document.getElementById('processes');
    const processDiv = document.createElement('div');
    processDiv.className = 'process';
    processDiv.id = `process_${processCount}`;
    processDiv.innerHTML = `
        <h3>
            Process ${processCount}
            <button type="button" onclick="removeProcess(${processCount})">Remove process</button>
        </h3>
        <div class="tasks" id="tasks_${processCount}"></div>
        <button type="button" onclick="addTask(${processCount})">Add task</button>
        <hr>
    `;
    processesDiv.appendChild(processDiv);
    saveState();
}

function removeProcess(processId) {
    const processDiv = document.getElementById(`process_${processId}`);
    if (processDiv) {
        processDiv.remove();
        renumberProcesses();
        saveState();
    }
}

function addTask(processId, value = '') {
    const tasksDiv = document.getElementById(`tasks_${processId}`);
    const taskCount = tasksDiv.children.length + 1;
    const taskDiv = document.createElement('div');
    taskDiv.className = 'task';
    taskDiv.innerHTML = `
        Task ${taskCount} time:
        <input type="number" name="processes[${processId}][tasks][]" min="1" required value="${value}">
        <button type="button" onclick="removeTask(this)">Remove</button>
    `;

    // Save state whenever an input value changes
    taskDiv.querySelector('input').addEventListener('input', saveState);

    tasksDiv.appendChild(taskDiv);
    saveState();
}

function removeTask(button) {
    const taskDiv = button.closest('.task');
    const tasksDiv = taskDiv.parentElement;
    taskDiv.remove();
    renumberTasks(tasksDiv);
    saveState();
}

// ── Renumbering after removal ─────────────────────────────────────────────────

function renumberProcesses() {
    const processDivs = document.querySelectorAll('.process');
    processCount = 0;
    processDivs.forEach((processDiv) => {
        processCount++;
        const newId = processCount;
        const oldId = parseInt(processDiv.id.split('_')[1]);

        // Update process div id
        processDiv.id = `process_${newId}`;

        // Update heading
        const h3 = processDiv.querySelector('h3');
        h3.innerHTML = `
            Process ${newId}
            <button type="button" onclick="removeProcess(${newId})">Remove process</button>
        `;

        // Update tasks div id
        const tasksDiv = processDiv.querySelector('.tasks');
        tasksDiv.id = `tasks_${newId}`;

        // Update add task button
        const addTaskBtn = processDiv.querySelector('button[onclick^="addTask"]');
        addTaskBtn.setAttribute('onclick', `addTask(${newId})`);

        // Update task input names
        const inputs = tasksDiv.querySelectorAll('input[type="number"]');
        inputs.forEach((input) => {
            input.name = `processes[${newId}][tasks][]`;
        });

        renumberTasks(tasksDiv);
    });
}

function renumberTasks(tasksDiv) {
    const taskDivs = tasksDiv.querySelectorAll('.task');
    taskDivs.forEach((taskDiv, index) => {
        const input = taskDiv.querySelector('input[type="number"]');
        taskDiv.childNodes[0].textContent = `Task ${index + 1} time: `;
    });
}

// ── Clear state ──────────────────────────────────────────────────────────────

function clearState() {
    if (!confirm('Are you sure you want to clear all processes and tasks?')) return;
    localStorage.removeItem('simulationState');
    processCount = 0;
    document.getElementById('processes').innerHTML = '';
}

// ── On page load, restore saved state ───────────────────────────────────────

document.addEventListener('DOMContentLoaded', loadState);