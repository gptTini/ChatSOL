import { COLS, ROWS, Game, SHAPES } from './core.mjs';

const boardCanvas = document.querySelector('#board');
const boardCtx = boardCanvas.getContext('2d');
const nextCanvas = document.querySelector('#next');
const nextCtx = nextCanvas.getContext('2d');
const scoreEl = document.querySelector('#score');
const linesEl = document.querySelector('#lines');
const levelEl = document.querySelector('#level');
const overlay = document.querySelector('#overlay');
const overlayTitle = document.querySelector('#overlay-title');
const overlayCopy = document.querySelector('#overlay-copy');

const CELL = boardCanvas.width / COLS;
const COLORS = {
  I: '#50d9f5',
  J: '#5b6bff',
  L: '#ff9f43',
  O: '#ffd93d',
  S: '#42d392',
  T: '#b66cff',
  Z: '#ff5f6d',
};

const game = new Game();
let last = performance.now();
let accumulator = 0;

function roundedBlock(ctx, x, y, size, color, alpha = 1) {
  const pad = 2;
  const r = 5;
  const px = x + pad;
  const py = y + pad;
  const s = size - pad * 2;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.roundRect(px, py, s, s, r);
  ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.18)';
  ctx.beginPath();
  ctx.roundRect(px + 3, py + 3, s - 6, Math.max(3, s * .16), 3);
  ctx.fill();
  ctx.restore();
}

function drawGrid() {
  boardCtx.fillStyle = '#0c111c';
  boardCtx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);
  boardCtx.strokeStyle = 'rgba(255,255,255,.035)';
  boardCtx.lineWidth = 1;
  for (let x = 1; x < COLS; x += 1) {
    boardCtx.beginPath();
    boardCtx.moveTo(x * CELL, 0);
    boardCtx.lineTo(x * CELL, boardCanvas.height);
    boardCtx.stroke();
  }
  for (let y = 1; y < ROWS; y += 1) {
    boardCtx.beginPath();
    boardCtx.moveTo(0, y * CELL);
    boardCtx.lineTo(boardCanvas.width, y * CELL);
    boardCtx.stroke();
  }
}

function drawMatrix(ctx, matrix, ox, oy, type, { ghost = false, cell = CELL } = {}) {
  for (let y = 0; y < matrix.length; y += 1) {
    for (let x = 0; x < matrix[y].length; x += 1) {
      if (!matrix[y][x]) continue;
      const py = oy + y;
      if (py < 0) continue;
      roundedBlock(ctx, (ox + x) * cell, py * cell, cell, COLORS[type], ghost ? .18 : 1);
    }
  }
}

function renderBoard() {
  drawGrid();
  for (let y = 0; y < ROWS; y += 1) {
    for (let x = 0; x < COLS; x += 1) {
      const type = game.board[y][x];
      if (type) roundedBlock(boardCtx, x * CELL, y * CELL, CELL, COLORS[type]);
    }
  }

  if (game.current) {
    const ghostY = game.current.y + game.getDropDistance();
    drawMatrix(boardCtx, game.current.matrix, game.current.x, ghostY, game.current.type, { ghost: true });
    drawMatrix(boardCtx, game.current.matrix, game.current.x, game.current.y, game.current.type);
  }
}

function renderNext() {
  nextCtx.clearRect(0, 0, nextCanvas.width, nextCanvas.height);
  const type = game.preview(1)[0];
  const matrix = SHAPES[type];
  const cell = 24;
  const w = matrix[0].length * cell;
  const h = matrix.length * cell;
  const ox = (nextCanvas.width - w) / 2 / cell;
  const oy = (nextCanvas.height - h) / 2 / cell;
  drawMatrix(nextCtx, matrix, ox, oy, type, { cell });
}

function renderHud() {
  scoreEl.textContent = game.score.toLocaleString();
  linesEl.textContent = String(game.lines);
  levelEl.textContent = String(game.level);

  if (game.gameOver) {
    overlay.classList.remove('hidden');
    overlayTitle.textContent = 'Game over';
    overlayCopy.textContent = 'Press R to restart';
  } else if (game.paused) {
    overlay.classList.remove('hidden');
    overlayTitle.textContent = 'Paused';
    overlayCopy.textContent = 'Press P to resume';
  } else {
    overlay.classList.add('hidden');
  }
}

function render() {
  renderBoard();
  renderNext();
  renderHud();
}

function act(action) {
  if (action !== 'restart' && game.gameOver) return;
  switch (action) {
    case 'left': game.move(-1, 0); break;
    case 'right': game.move(1, 0); break;
    case 'down': game.softDrop(); break;
    case 'rotate': game.rotate(1); break;
    case 'rotate-left': game.rotate(-1); break;
    case 'drop': game.hardDrop(); break;
    case 'pause': game.togglePause(); break;
    case 'restart': game.reset(); accumulator = 0; break;
    default: break;
  }
  render();
}

window.addEventListener('keydown', (event) => {
  const actions = {
    ArrowLeft: 'left',
    ArrowRight: 'right',
    ArrowDown: 'down',
    ArrowUp: 'rotate',
    z: 'rotate-left',
    Z: 'rotate-left',
    x: 'rotate',
    X: 'rotate',
    ' ': 'drop',
    p: 'pause',
    P: 'pause',
    r: 'restart',
    R: 'restart',
  };
  const action = actions[event.key];
  if (!action) return;
  event.preventDefault();
  act(action);
});

document.querySelectorAll('[data-action]').forEach((button) => {
  button.addEventListener('pointerdown', (event) => {
    event.preventDefault();
    act(button.dataset.action);
  });
});

function frame(now) {
  const delta = Math.min(100, now - last);
  last = now;
  if (!game.paused && !game.gameOver) {
    accumulator += delta;
    const interval = game.dropIntervalMs();
    while (accumulator >= interval) {
      game.tick();
      accumulator -= interval;
    }
  }
  render();
  requestAnimationFrame(frame);
}

render();
requestAnimationFrame(frame);
