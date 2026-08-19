import { COLS, ROWS, Game, SHAPES } from './core.mjs';

const boardCanvas = document.querySelector('#board');
const boardCtx = boardCanvas.getContext('2d');
const nextCanvas = document.querySelector('#next');
const nextCtx = nextCanvas.getContext('2d');
const boardCard = document.querySelector('#board-card');
const nextPanel = document.querySelector('#next-panel');
const scoreEl = document.querySelector('#score');
const linesEl = document.querySelector('#lines');
const levelEl = document.querySelector('#level');
const levelProgress = document.querySelector('#level-progress');
const levelProgressCopy = document.querySelector('#level-progress-copy');
const statusText = document.querySelector('#status-text');
const srStatus = document.querySelector('#sr-status');
const overlay = document.querySelector('#overlay');
const overlayTitle = document.querySelector('#overlay-title');
const overlayCopy = document.querySelector('#overlay-copy');
const lineBurst = document.querySelector('#line-burst');
const pauseButton = document.querySelector('#pause-button');

const COLORS = {
  I: '#50d9f5',
  J: '#6576ff',
  L: '#ff9f43',
  O: '#ffd75e',
  S: '#42d392',
  T: '#b977ff',
  Z: '#ff6472',
};

const game = new Game();
const boardMetrics = { width: 320, height: 640, cell: 32 };
const nextMetrics = { width: 160, height: 116 };
let last = performance.now();
let accumulator = 0;
let dirty = true;
let lastUi = {
  score: -1,
  lines: -1,
  level: -1,
  currentType: null,
  paused: null,
  gameOver: null,
};

function shade(hex, amount) {
  const raw = hex.replace('#', '');
  const value = Number.parseInt(raw, 16);
  const shift = Math.round(255 * amount);
  const clamp = (channel) => Math.max(0, Math.min(255, channel + shift));
  const r = clamp((value >> 16) & 255);
  const g = clamp((value >> 8) & 255);
  const b = clamp(value & 255);
  return `rgb(${r} ${g} ${b})`;
}

function withAlpha(hex, alpha) {
  const raw = hex.replace('#', '');
  const value = Number.parseInt(raw, 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;
  return `rgb(${r} ${g} ${b} / ${alpha})`;
}

function restartAnimation(element, className) {
  element.classList.remove(className);
  void element.offsetWidth;
  element.classList.add(className);
}

function announce(message) {
  srStatus.textContent = '';
  requestAnimationFrame(() => { srStatus.textContent = message; });
}

function syncCanvas(canvas, ctx, metrics, ratio = null) {
  const rect = canvas.getBoundingClientRect();
  const cssWidth = Math.max(1, Math.round(rect.width));
  const cssHeight = ratio ? Math.round(cssWidth * ratio) : Math.max(1, Math.round(rect.height));
  const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
  const targetWidth = Math.max(1, Math.round(cssWidth * dpr));
  const targetHeight = Math.max(1, Math.round(cssHeight * dpr));
  const changed = canvas.width !== targetWidth || canvas.height !== targetHeight;

  if (changed) {
    canvas.width = targetWidth;
    canvas.height = targetHeight;
  }

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  metrics.width = cssWidth;
  metrics.height = cssHeight;
  if ('cell' in metrics) metrics.cell = cssWidth / COLS;
  return changed;
}

function resizeCanvases() {
  const boardChanged = syncCanvas(boardCanvas, boardCtx, boardMetrics, ROWS / COLS);
  const nextChanged = syncCanvas(nextCanvas, nextCtx, nextMetrics);
  if (boardChanged || nextChanged) dirty = true;
}

function roundedRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, radius);
}

function drawBlock(ctx, x, y, size, type, { ghost = false, alpha = 1 } = {}) {
  const color = COLORS[type];
  const pad = Math.max(1.4, size * .055);
  const px = x + pad;
  const py = y + pad;
  const side = size - pad * 2;
  const radius = Math.max(3, size * .15);

  ctx.save();
  ctx.globalAlpha = alpha;

  if (ghost) {
    ctx.strokeStyle = withAlpha(color, .72);
    ctx.lineWidth = Math.max(1.3, size * .055);
    ctx.setLineDash([Math.max(2, size * .14), Math.max(2, size * .1)]);
    roundedRect(ctx, px + 1, py + 1, side - 2, side - 2, radius);
    ctx.stroke();
    ctx.restore();
    return;
  }

  const gradient = ctx.createLinearGradient(px, py, px, py + side);
  gradient.addColorStop(0, shade(color, .08));
  gradient.addColorStop(.58, color);
  gradient.addColorStop(1, shade(color, -.13));
  ctx.fillStyle = gradient;
  ctx.shadowColor = withAlpha(color, .18);
  ctx.shadowBlur = Math.max(2, size * .16);
  roundedRect(ctx, px, py, side, side, radius);
  ctx.fill();

  ctx.shadowBlur = 0;
  ctx.fillStyle = 'rgb(255 255 255 / .17)';
  roundedRect(ctx, px + side * .12, py + side * .1, side * .76, Math.max(2, side * .09), radius * .45);
  ctx.fill();

  ctx.strokeStyle = 'rgb(255 255 255 / .075)';
  ctx.lineWidth = 1;
  roundedRect(ctx, px + .5, py + .5, side - 1, side - 1, radius);
  ctx.stroke();
  ctx.restore();
}

function drawMatrix(ctx, matrix, ox, oy, type, { ghost = false, cell = boardMetrics.cell, offsetX = 0, offsetY = 0 } = {}) {
  for (let y = 0; y < matrix.length; y += 1) {
    for (let x = 0; x < matrix[y].length; x += 1) {
      if (!matrix[y][x]) continue;
      const py = oy + y;
      if (py < 0) continue;
      drawBlock(
        ctx,
        offsetX + (ox + x) * cell,
        offsetY + py * cell,
        cell,
        type,
        { ghost },
      );
    }
  }
}

function drawGrid() {
  const { width, height, cell } = boardMetrics;
  const background = boardCtx.createLinearGradient(0, 0, 0, height);
  background.addColorStop(0, '#0b111c');
  background.addColorStop(1, '#080c14');
  boardCtx.fillStyle = background;
  boardCtx.fillRect(0, 0, width, height);

  const danger = boardCtx.createLinearGradient(0, 0, 0, cell * 4.5);
  danger.addColorStop(0, 'rgb(255 95 109 / .055)');
  danger.addColorStop(1, 'rgb(255 95 109 / 0)');
  boardCtx.fillStyle = danger;
  boardCtx.fillRect(0, 0, width, cell * 4.5);

  boardCtx.lineWidth = 1;
  for (let x = 1; x < COLS; x += 1) {
    boardCtx.strokeStyle = x === 5 ? 'rgb(255 255 255 / .045)' : 'rgb(255 255 255 / .026)';
    boardCtx.beginPath();
    boardCtx.moveTo(Math.round(x * cell) + .5, 0);
    boardCtx.lineTo(Math.round(x * cell) + .5, height);
    boardCtx.stroke();
  }
  for (let y = 1; y < ROWS; y += 1) {
    boardCtx.strokeStyle = y % 5 === 0 ? 'rgb(255 255 255 / .04)' : 'rgb(255 255 255 / .026)';
    boardCtx.beginPath();
    boardCtx.moveTo(0, Math.round(y * cell) + .5);
    boardCtx.lineTo(width, Math.round(y * cell) + .5);
    boardCtx.stroke();
  }
}

function renderBoard() {
  drawGrid();
  const cell = boardMetrics.cell;

  for (let y = 0; y < ROWS; y += 1) {
    for (let x = 0; x < COLS; x += 1) {
      const type = game.board[y][x];
      if (type) drawBlock(boardCtx, x * cell, y * cell, cell, type);
    }
  }

  if (!game.current) return;
  const ghostY = game.current.y + game.getDropDistance();
  drawMatrix(boardCtx, game.current.matrix, game.current.x, ghostY, game.current.type, { ghost: true });
  drawMatrix(boardCtx, game.current.matrix, game.current.x, game.current.y, game.current.type);
}

function renderNext() {
  const { width, height } = nextMetrics;
  nextCtx.clearRect(0, 0, width, height);
  const type = game.preview(1)[0];
  const matrix = SHAPES[type];
  if (!type || !matrix) return;

  const maxColumns = Math.max(matrix[0].length, matrix.length);
  const cell = Math.min(28, Math.max(18, Math.min(width, height) / (maxColumns + 1)));
  const pieceWidth = matrix[0].length * cell;
  const pieceHeight = matrix.length * cell;
  const offsetX = (width - pieceWidth) / 2;
  const offsetY = (height - pieceHeight) / 2;
  drawMatrix(nextCtx, matrix, 0, 0, type, { cell, offsetX, offsetY });
}

function stateName() {
  if (game.gameOver) return 'over';
  if (game.paused) return 'paused';
  return 'playing';
}

function renderHud(force = false) {
  const currentType = game.current?.type ?? null;
  const scoreChanged = game.score !== lastUi.score;
  const linesChanged = game.lines !== lastUi.lines;
  const levelChanged = game.level !== lastUi.level;
  const pieceChanged = currentType !== lastUi.currentType;
  const stateChanged = game.paused !== lastUi.paused || game.gameOver !== lastUi.gameOver;

  if (force || scoreChanged) {
    scoreEl.textContent = game.score.toLocaleString();
    if (lastUi.score >= 0 && game.score > lastUi.score) restartAnimation(scoreEl, 'is-bump');
  }
  if (force || linesChanged) linesEl.textContent = String(game.lines);
  if (force || levelChanged) levelEl.textContent = String(game.level);

  if (force || linesChanged || levelChanged) {
    const progress = game.lines % 10;
    levelProgress.style.width = `${progress * 10}%`;
    levelProgressCopy.textContent = `${progress} / 10`;
  }

  if (force || pieceChanged) {
    renderNext();
    if (lastUi.currentType) restartAnimation(nextPanel, 'is-pop');
  }

  if (force || stateChanged) {
    const state = stateName();
    boardCard.dataset.state = state;
    document.body.dataset.gameState = state;

    if (game.gameOver) {
      statusText.textContent = 'Game over';
      overlay.hidden = false;
      overlayTitle.textContent = 'Game over';
      overlayCopy.textContent = 'Press R or restart to try again';
      overlay.querySelector('[data-action="pause"]').hidden = true;
      pauseButton.disabled = true;
      pauseButton.querySelector('span').textContent = 'Ended';
    } else if (game.paused) {
      statusText.textContent = 'Paused';
      overlay.hidden = false;
      overlayTitle.textContent = 'Paused';
      overlayCopy.textContent = 'Press P to resume';
      const resume = overlay.querySelector('[data-action="pause"]');
      resume.hidden = false;
      resume.textContent = 'Resume';
      pauseButton.disabled = false;
      pauseButton.querySelector('span').textContent = 'Resume';
    } else {
      statusText.textContent = 'Playing';
      overlay.hidden = true;
      pauseButton.disabled = false;
      pauseButton.querySelector('span').textContent = 'Pause';
    }
  }

  lastUi = {
    score: game.score,
    lines: game.lines,
    level: game.level,
    currentType,
    paused: game.paused,
    gameOver: game.gameOver,
  };
}

function render(force = false) {
  resizeCanvases();
  renderBoard();
  renderHud(force);
  dirty = false;
}

function visualSnapshot() {
  return {
    score: game.score,
    lines: game.lines,
    level: game.level,
    currentType: game.current?.type ?? null,
    paused: game.paused,
    gameOver: game.gameOver,
  };
}

function triggerFeedback(before, action, result) {
  const lineDelta = game.lines - before.lines;
  if (lineDelta > 0) {
    lineBurst.textContent = lineDelta === 4 ? 'TETRIS · +4' : `+${lineDelta} LINE${lineDelta > 1 ? 'S' : ''}`;
    restartAnimation(lineBurst, 'is-visible');
    restartAnimation(boardCard, 'is-clear');
    announce(`${lineDelta} line${lineDelta > 1 ? 's' : ''} cleared. Score ${game.score}.`);
    navigator.vibrate?.(lineDelta === 4 ? [18, 30, 30] : 18);
  } else if (action === 'drop' && result > 0) {
    restartAnimation(boardCard, 'is-impact');
    navigator.vibrate?.(10);
  }

  if (!before.gameOver && game.gameOver) announce(`Game over. Final score ${game.score}.`);
  if (action === 'pause' && before.paused !== game.paused) announce(game.paused ? 'Game paused.' : 'Game resumed.');
  if (action === 'restart') announce('New game started.');
}

function act(action) {
  if (game.gameOver && action !== 'restart') return false;
  if (game.paused && action !== 'pause' && action !== 'restart') return false;

  const before = visualSnapshot();
  let result = false;

  switch (action) {
    case 'left': result = game.move(-1, 0); break;
    case 'right': result = game.move(1, 0); break;
    case 'down': result = game.softDrop(); break;
    case 'rotate': result = game.rotate(1); break;
    case 'rotate-left': result = game.rotate(-1); break;
    case 'drop': result = game.hardDrop(); break;
    case 'pause': result = game.togglePause(); break;
    case 'restart':
      game.reset();
      accumulator = 0;
      last = performance.now();
      result = true;
      break;
    default: return false;
  }

  dirty = true;
  triggerFeedback(before, action, result);
  render();
  return true;
}

const KEY_ACTIONS = {
  ArrowLeft: 'left',
  ArrowRight: 'right',
  ArrowDown: 'down',
  ArrowUp: 'rotate',
  KeyZ: 'rotate-left',
  KeyX: 'rotate',
  Space: 'drop',
  KeyP: 'pause',
  Escape: 'pause',
  KeyR: 'restart',
};

const REPEATABLE_KEYS = new Set(['left', 'right', 'down']);

window.addEventListener('keydown', (event) => {
  const action = KEY_ACTIONS[event.code];
  if (!action) return;
  if (event.code === 'Space' && event.target instanceof Element && event.target.closest('button')) return;
  if (event.repeat && !REPEATABLE_KEYS.has(action)) {
    event.preventDefault();
    return;
  }
  event.preventDefault();
  act(action);
});

const holdState = new Map();

function clearHold(button) {
  const state = holdState.get(button);
  if (!state) return;
  clearTimeout(state.delay);
  clearInterval(state.interval);
  holdState.delete(button);
  button.classList.remove('is-held');
}

function startHold(button) {
  clearHold(button);
  const action = button.dataset.action;
  act(action);
  button.classList.add('is-held');

  const state = { delay: 0, interval: 0 };
  state.delay = window.setTimeout(() => {
    state.interval = window.setInterval(() => act(action), action === 'down' ? 46 : 64);
  }, 175);
  holdState.set(button, state);
}

document.querySelectorAll('[data-action]').forEach((button) => {
  button.addEventListener('pointerdown', (event) => {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    event.preventDefault();
    button.setPointerCapture?.(event.pointerId);
    if (button.hasAttribute('data-hold')) startHold(button);
    else act(button.dataset.action);
  });

  button.addEventListener('click', (event) => {
    if (event.detail === 0) act(button.dataset.action);
  });

  ['pointerup', 'pointercancel', 'lostpointercapture', 'pointerleave'].forEach((name) => {
    button.addEventListener(name, () => clearHold(button));
  });
});

function tickOnce() {
  const before = visualSnapshot();
  game.tick();
  dirty = true;
  triggerFeedback(before, 'tick', false);
}

function frame(now) {
  const delta = Math.min(100, now - last);
  last = now;

  if (!game.paused && !game.gameOver) {
    accumulator += delta;
    const interval = game.dropIntervalMs();
    while (accumulator >= interval) {
      tickOnce();
      accumulator -= interval;
      if (game.gameOver) break;
    }
  }

  if (dirty) render();
  requestAnimationFrame(frame);
}

if ('ResizeObserver' in window) {
  const resizeObserver = new ResizeObserver(() => {
    resizeCanvases();
    dirty = true;
  });
  resizeObserver.observe(boardCanvas);
  resizeObserver.observe(nextCanvas);
}

window.addEventListener('resize', () => {
  resizeCanvases();
  dirty = true;
}, { passive: true });
document.addEventListener('visibilitychange', () => {
  if (document.hidden && !game.paused && !game.gameOver) act('pause');
});

resizeCanvases();
render(true);
requestAnimationFrame(frame);
