// --- Simulation Animation Loop ---
let currentTick = 1;
let isPaused = false;
let animationTimeout = null;
let playbackStarted = false;

const AUTO_PLAY_KEY = 'linprodAutoPlayAfterSimulate';
const COLOR_PALETTE_KEY = 'linprodColorPalette';

function padTick(num) {
    return String(num).padStart(3, '0');
}

function loadTickReport(tick) {
    return fetch(`/report/report_tick_${padTick(tick)}.json`)
        .then(res => {
            if (!res.ok) throw new Error('No more ticks');
            return res.json();
        });
}

function getExecutionDelay() {
    return parseInt(document.querySelector('.execution-time-input')?.value, 10) || 1000;
}

function generateRandomColor() {
    const hue = Math.floor(Math.random() * 360);
    const saturation = 70 + Math.floor(Math.random() * 20);
    const lightness = 48 + Math.floor(Math.random() * 14);
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function generateColorPalette(numProducts) {
    const palette = [];
    for (let index = 0; index < numProducts; index += 1) {
        palette.push(generateRandomColor());
    }
    return palette;
}

function saveColorPalette(palette) {
    sessionStorage.setItem(COLOR_PALETTE_KEY, JSON.stringify(palette));
}

function loadColorPalette() {
    const raw = sessionStorage.getItem(COLOR_PALETTE_KEY);
    if (!raw) return null;
    try {
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : null;
    } catch {
        return null;
    }
}

function getProductColor(productId) {
    const palette = currentColorPalette || loadColorPalette();
    if (!palette || typeof productId !== 'number') return null;
    const index = productId - 1;
    if (index < 0 || index >= palette.length) return null;
    return palette[index];
}

function createColoredBox(productId) {
    const color = getProductColor(productId);
    if (!color) return null;

    const box = document.createElement('span');
    box.className = 'colored-product-icon';
    box.dataset.productId = String(productId);
    box.style.backgroundColor = color;
    box.style.maskImage = 'url(/static/imgs/box.svg)';
    box.style.webkitMaskImage = 'url(/static/imgs/box.svg)';
    box.style.maskRepeat = 'no-repeat';
    box.style.webkitMaskRepeat = 'no-repeat';
    box.style.maskPosition = 'center';
    box.style.webkitMaskPosition = 'center';
    box.style.maskSize = 'contain';
    box.style.webkitMaskSize = 'contain';
    return box;
}

function createDefaultBox() {
    const box = document.createElement('img');
    box.src = '/static/imgs/box.svg';
    box.alt = 'box';
    box.className = 'icon-box';
    return box;
}

function createProductBox(productId) {
    try {
        return createColoredBox(productId) || createDefaultBox();
    } catch {
        return createDefaultBox();
    }
}

function setStartButtonState(isRunning) {
    const btn = document.getElementById('iniciar-btn');
    if (btn) btn.textContent = isRunning ? '⏸' : '▶';
}

function setStartButtonAvailability(hasProcesses) {
    const btn = document.getElementById('iniciar-btn');
    if (!btn) return;
    btn.disabled = !hasProcesses;
    btn.title = hasProcesses ? '' : 'Añade al menos un proceso para iniciar la simulación';
}

function queueNextTick(nextTick) {
    if (isPaused) return;
    animationTimeout = setTimeout(() => {
        animateSimulation(nextTick);
    }, getExecutionDelay());
}

function updateUIForTick(tickData, tickNumber) {
    // Update tick-input if present
    const tickInput = document.querySelector('.tick-input');
    if (tickInput) {
        tickInput.value = tickNumber || currentTick;
    }

    // Clear all boxes/icons first
    document.querySelectorAll('.task-left').forEach(left => left.innerHTML = '');
    document.querySelectorAll('.task-right-right').forEach(right => right.innerHTML = '');

    // For each process in the tick
    tickData.forEach((process, pIdx) => {
        process.tasks.forEach((task, tIdx) => {
            const processCard = document.querySelectorAll('.process-card')[pIdx];
            if (!processCard) return;
            const taskCards = processCard.querySelectorAll('.task-card');
            const taskCard = taskCards[tIdx];
            if (!taskCard) return;

            // Queue as grid of boxes in .task-left
            const left = taskCard.querySelector('.task-left');
            if (left) {
                left.innerHTML = '';
                const queue = task.queue_product_ids || [];
                queue.forEach(productId => {
                    left.appendChild(createProductBox(productId));
                });
            }

            // Show/hide box in .task-right-right if processing
            const right = taskCard.querySelector('.task-right-right');
            if (right) {
                right.innerHTML = '';
                if (task.state === 'P' && task.product_in_process_id) {
                    right.appendChild(createProductBox(task.product_in_process_id));
                }
            }
        });
    });
}

function animateSimulation(tick = currentTick) {
    if (isPaused) return;
    loadTickReport(tick)
        .then(tickData => {
            updateUIForTick(tickData, tick);
            currentTick = tick + 1;
            queueNextTick(currentTick);
        })
        .catch(() => {
            // No more ticks, loop back to tick 1.
            currentTick = 1;
            queueNextTick(1);
        });
}

function togglePause() {
    isPaused = !isPaused;
    setStartButtonState(!isPaused);
    if (!isPaused) {
        playbackStarted = true;
        animateSimulation(currentTick);
    } else {
        clearTimeout(animationTimeout);
    }
}

function resetPlaybackState() {
    playbackStarted = false;
    isPaused = true;
    clearTimeout(animationTimeout);
    setStartButtonState(false);
}
// figma_export.js - Adds process frames to the config-card in figma_export.html



// --- Persistent, removable, scrollable process frames ---

const STORAGE_KEY = 'figmaProcesses';
const PRODUCT_KEY = 'figmaNumProducts';
const TASKS_KEY = 'figmaTaskDurations';
const EXEC_TIME_KEY = 'figmaExecTime';
let figmaProcesses = [];
function saveExecTime() {
    const execInput = document.querySelector('.execution-time-input');
    if (execInput) {
        localStorage.setItem(EXEC_TIME_KEY, execInput.value || '500');
    }
}

function loadExecTime() {
    return localStorage.getItem(EXEC_TIME_KEY) || '500';
}


function saveFigmaProcesses() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(figmaProcesses));
    saveTaskDurations();
}

function saveNumProducts() {
    const productInput = document.querySelector('.config-input[type="number"]');
    if (productInput) {
        localStorage.setItem(PRODUCT_KEY, productInput.value || '1');
    }
}

function loadNumProducts() {
    return localStorage.getItem(PRODUCT_KEY) || '1';
}

function saveTaskDurations() {
    // Save all task-input values as a nested array (processes -> tasks)
    const allDurations = [];
    document.querySelectorAll('.process-card').forEach(card => {
        const taskInputs = card.querySelectorAll('.task-input');
        const durations = [];
        taskInputs.forEach(input => durations.push(input.value));
        allDurations.push(durations);
    });
    localStorage.setItem(TASKS_KEY, JSON.stringify(allDurations));
}

function loadTaskDurations() {
    try {
        return JSON.parse(localStorage.getItem(TASKS_KEY)) || [];
    } catch {
        return [];
    }
}

function loadFigmaProcesses() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    try {
        return JSON.parse(raw);
    } catch {
        return [];
    }
}



function renderFigmaProcesses() {
    // Sidebar process list
    const container = document.getElementById('figma-process-list');
    if (container) {
        container.innerHTML = '';
        figmaProcesses.forEach((proc, idx) => {
            const processDiv = document.createElement('div');
            processDiv.className = 'figma-process-frame process';
            processDiv.textContent = `Proceso ${idx + 1}`;
            // Remove button
            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-process-btn';
            removeBtn.textContent = '✕';
            removeBtn.title = 'Eliminar proceso';
            removeBtn.onclick = function() {
                resetPlaybackState();
                figmaProcesses.splice(idx, 1);
                saveFigmaProcesses();
                renderFigmaProcesses();
            };
            processDiv.appendChild(removeBtn);
            container.appendChild(processDiv);
        });
    }

    // Right-bottom process cards
    const rightBottom = document.getElementById('right-bottom-process-list');
    if (rightBottom) {
        rightBottom.innerHTML = '';
        // Calculate n for nxn grid
        const n = Math.max(1, Math.ceil(Math.sqrt(figmaProcesses.length)));
        rightBottom.style.display = 'grid';
        rightBottom.style.gridTemplateColumns = `repeat(${n}, 1fr)`;
        rightBottom.style.gridTemplateRows = `repeat(${n}, 1fr)`;

        // Load persisted task durations
        const persistedDurations = loadTaskDurations();

        if (figmaProcesses.length === 0) {
            const empty = document.createElement('span');
            empty.className = 'empty-label';
            empty.textContent = 'Tu línea de producción está vacía, Añade procesos y tareas para realizar la simulación';
            rightBottom.appendChild(empty);
        } else {
            figmaProcesses.forEach((proc, idx) => {
                rightBottom.appendChild(createProcessCard(idx, persistedDurations[idx]));
            });
        }
    }

    setStartButtonAvailability(figmaProcesses.length > 0);
}


function createProcessCard(idx, persistedTaskDurations) {
    // Main card
    const card = document.createElement('div');
    card.className = 'process-card';

    // Header
    const header = document.createElement('div');
    header.className = 'process-header';
    const icon = document.createElement('img');
    icon.src = '/static/imgs/Home.svg';
    icon.alt = 'icon';
    icon.className = 'icon';
    const title = document.createElement('span');
    title.className = 'process-title';
    title.textContent = `Proceso #${idx + 1}`;
    header.appendChild(icon);
    header.appendChild(title);
    card.appendChild(header);

    // Tarea card (at least one by default)
    const numTasks = figmaProcesses[idx].task || 1;
    for (let i = 0; i < numTasks; i++) {
        const duration = (persistedTaskDurations && persistedTaskDurations[i]) ? persistedTaskDurations[i] : '1';
        card.appendChild(createTaskCard(i + 1, duration));
    }

    // Add tarea button
    const addTaskBtn = document.createElement('button');
    addTaskBtn.className = 'add-task-btn';
    const img = document.createElement('img');
    img.src = '/static/imgs/BlueCross.svg';
    img.alt = 'icon';
    img.className = 'icon';
    addTaskBtn.appendChild(img);

    addTaskBtn.onclick = function() {
        resetPlaybackState();
        figmaProcesses[idx].task = (figmaProcesses[idx].task || 1) + 1;
        saveFigmaProcesses();
        renderFigmaProcesses();
    };
    card.appendChild(addTaskBtn);

    // Remove button (top right)
    const removeTaskBtn = document.createElement('button');
    removeTaskBtn.className = 'remove-task-btn';
    removeTaskBtn.textContent = '✕';
    removeTaskBtn.title = 'Eliminar Tarea';
    removeTaskBtn.onclick = function() {
        resetPlaybackState();
        figmaProcesses[idx].task = Math.max(1, (figmaProcesses[idx].task || 1) - 1);
        saveFigmaProcesses();
        renderFigmaProcesses();
    };
    card.appendChild(removeTaskBtn);

    return card;
}


function createTaskCard(num, value) {
    const tarea = document.createElement('div');
    tarea.className = 'task-card';
    
    // Right side (Header, time input, box)
    const right = document.createElement('div');
    right.className = 'task-right';

    // Right side right (header and time input)
    const rightLeft = document.createElement('div');
    rightLeft.className = 'task-right-left';

    // Header
    const header = document.createElement('div');
    header.className = 'task-header';
    const icon = document.createElement('img');
    icon.src = '/static/imgs/robot-arm.svg';
    icon.alt = 'icon';
    icon.className = 'icon-robot-arm';
    const title = document.createElement('span');
    title.className = 'task-title';
    title.textContent = `Tarea #${num}`;
    header.appendChild(icon);
    header.appendChild(title);
    rightLeft.appendChild(header);

    // Body
    const body = document.createElement('div');
    body.className = 'task-body';
    const label = document.createElement('span');
    label.className = 'task-label';
    label.textContent = 'Añadir duración';
    const input = document.createElement('input');
    input.type = 'number';
    input.className = 'task-input';
    input.value = value || '1';
    input.min = '1';
    input.step = '1';

    // Save on change
    input.addEventListener('input', function() {
        resetPlaybackState();
        saveTaskDurations();
    });
    body.appendChild(label);
    body.appendChild(input);

    rightLeft.appendChild(body);

    // Box
    const rightRight = document.createElement('div');
    rightRight.className = 'task-right-right';

    const boxImg = document.createElement('img');
    boxImg.src = '/static/imgs/box.svg';
    boxImg.alt = 'box';
    boxImg.className = 'icon-box';
    rightRight.appendChild(boxImg);

    right.appendChild(rightLeft);
    right.appendChild(rightRight);
    tarea.appendChild(right);

    // Left side (icon grid)
    const left = document.createElement('div');
    left.className = 'task-left';
    tarea.appendChild(left);

    return tarea;
}

function addProcessFigma() {
    resetPlaybackState();
    figmaProcesses.push({ task: 1 });
    saveFigmaProcesses();
    renderFigmaProcesses();
}

// On page load, set up scrollable container and render
document.addEventListener('DOMContentLoaded', function() {
    // If not present, create the scrollable process list container
    let processList = document.getElementById('figma-process-list');
    if (!processList) {
        // Find the config-section inside the config-card
        const configSection = document.querySelector('.config-card .config-section');
        if (configSection) {
            processList = document.createElement('div');
            processList.id = 'figma-process-list';
            processList.className = 'figma-process-list-scroll';
            // Insert after add-process-section
            const addSection = configSection.querySelector('.add-process-section');
            if (addSection && addSection.nextSibling) {
                configSection.insertBefore(processList, addSection.nextSibling);
            } else {
                configSection.appendChild(processList);
            }
        }
    }
    figmaProcesses = loadFigmaProcesses();

    // Add error message container if not present
    let errorMsg = document.getElementById('validation-error-msg');
    if (!errorMsg) {
        errorMsg = document.createElement('div');
        errorMsg.id = 'validation-error-msg';
        errorMsg.style.display = 'none';
        errorMsg.style.color = 'red';
        errorMsg.style.margin = '10px 0';
        errorMsg.style.fontWeight = 'bold';
        errorMsg.style.background = '#fff0f0';
        errorMsg.style.border = '1px solid #e57373';
        errorMsg.style.padding = '8px 12px';
        errorMsg.style.borderRadius = '6px';
        const configCard = document.querySelector('.config-card');
        if (configCard) {
            configCard.insertBefore(errorMsg, configCard.firstChild);
        } else {
            document.body.insertBefore(errorMsg, document.body.firstChild);
        }
    }


    // Set number of products from storage
    const productInput = document.querySelector('.config-input[type="number"]');
    if (productInput) {
        productInput.value = loadNumProducts();
        productInput.addEventListener('input', function() {
            resetPlaybackState();
            saveNumProducts();
        });
    }

    // Set execution time from storage, default 500
    const execInput = document.querySelector('.execution-time-input');
    if (execInput) {
        execInput.value = loadExecTime();
        execInput.addEventListener('input', function() {
            saveExecTime();
        });
    }

    renderFigmaProcesses();

    // Add event listener to iniciar-btn
    const iniciarBtn = document.getElementById('iniciar-btn');
    if (iniciarBtn) {
        iniciarBtn.addEventListener('click', function(e) {
            e.preventDefault();

            // Hide previous error
            errorMsg.style.display = 'none';
            errorMsg.textContent = '';

            if (figmaProcesses.length === 0) {
                return;
            }

            // --- Validation ---
            let hasError = false;
            let errorMessages = [];

            // Validate number of products
            const productInput = document.querySelector('.config-input[type="number"]');
            let numProducts = 1;
            if (productInput && productInput.value) {
                numProducts = Number(productInput.value);
                if (!Number.isInteger(numProducts) || numProducts < 1) {
                    hasError = true;
                    errorMessages.push('La cantidad de productos debe ser un número entero mayor o igual a 1.');
                    productInput.classList.add('input-error');
                } else {
                    productInput.classList.remove('input-error');
                }
            }

            // Validate all task durations
            const processCards = document.querySelectorAll('.process-card');
            processCards.forEach((processCard, idx) => {
                const taskInputs = processCard.querySelectorAll('.task-input');
                taskInputs.forEach((input, tIdx) => {
                    const val = Number(input.value);
                    if (!Number.isInteger(val) || val < 1) {
                        hasError = true;
                        errorMessages.push(`La duración de la tarea #${tIdx + 1} del proceso #${idx + 1} debe ser un número entero mayor o igual a 1.`);
                        input.classList.add('input-error');
                    } else {
                        input.classList.remove('input-error');
                    }
                });
            });

            if (hasError) {
                errorMsg.textContent = errorMessages.join(' ');
                errorMsg.style.display = 'block';
                return;
            }

            if (!playbackStarted) {
                // First start: POST to /simulate and ask the next page load to autoplay.
                saveNumProducts();
                saveTaskDurations();

                // Collect processes and tasks
                const processes = [];
                figmaProcesses.forEach((proc, idx) => {
                    // For each process, get the durations from the rendered task inputs
                    const processCard = document.querySelectorAll('.process-card')[idx];
                    const taskInputs = processCard ? processCard.querySelectorAll('.task-input') : [];
                    const tasks = [];
                    taskInputs.forEach(input => {
                        const val = parseInt(input.value, 10);
                        if (!isNaN(val) && val > 0) tasks.push(val);
                    });
                    // Fallback: if no tasks found, use 1
                    if (tasks.length === 0) tasks.push(1);
                    processes.push({ tasks });
                });

                // Build form data
                const formData = new URLSearchParams();
                formData.append('num_products', numProducts);
                processes.forEach((proc, i) => {
                    proc.tasks.forEach((task, j) => {
                        formData.append(`processes[${i+1}][tasks][]`, task);
                    });
                });

                sessionStorage.setItem(AUTO_PLAY_KEY, '1');
                const palette = generateColorPalette(numProducts);
                saveColorPalette(palette);
                currentColorPalette = palette;
                setStartButtonState(true);

                // POST to /simulate
                fetch('/simulate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData.toString(),
                })
                .then(response => {
                    if (response.redirected) {
                        window.location.href = response.url;
                    } else {
                        window.location.reload();
                    }
                })
                .catch(err => {
                    alert('Error al iniciar la simulación: ' + err);
                });
            } else if (isPaused) {
                togglePause();
            } else {
                togglePause();
            }
        });
    }

    // Manual step controls (only while paused)
    const previousBtn = document.getElementById('previous-btn');
    if (previousBtn) {
        previousBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!playbackStarted || !isPaused) return;

            // currentTick points to the next tick to play, so previous shown tick is currentTick - 1.
            const targetTick = Math.max(1, currentTick - 2);
            loadTickReport(targetTick)
                .then(tickData => {
                    updateUIForTick(tickData, targetTick);
                    currentTick = targetTick + 1;
                })
                .catch(() => {});
        });
    }

    const nextBtn = document.getElementById('next-btn');
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!playbackStarted || !isPaused) return;

            const targetTick = currentTick;
            loadTickReport(targetTick)
                .then(tickData => {
                    updateUIForTick(tickData, targetTick);
                    currentTick = targetTick + 1;
                })
                .catch(() => {
                    // If there are no more reports, loop to tick 1.
                    loadTickReport(1)
                        .then(tickData => {
                            updateUIForTick(tickData, 1);
                            currentTick = 2;
                        })
                        .catch(() => {});
                });
        });
    }
});

window.addEventListener('load', function() {
    const btn = document.getElementById('iniciar-btn');
    if (btn) btn.textContent = '▶';

    fetch('/report/report_tick_001.json')
        .then(res => {
            if (res.ok) {
                currentTick = 1;
                currentColorPalette = loadColorPalette();
                const shouldAutoPlay = sessionStorage.getItem(AUTO_PLAY_KEY) === '1';
                if (shouldAutoPlay) {
                    sessionStorage.removeItem(AUTO_PLAY_KEY);
                    playbackStarted = true;
                    isPaused = false;
                    setStartButtonState(true);
                    animateSimulation(1);
                } else {
                    isPaused = true;
                    playbackStarted = false;
                    setStartButtonState(false);
                }
                setStartButtonAvailability(figmaProcesses.length > 0);
            }
        })
        .catch(() => {
            isPaused = true;
            playbackStarted = false;
            setStartButtonState(false);
            setStartButtonAvailability(figmaProcesses.length > 0);
        });
});
