export const COLS = 10;
export const ROWS = 20;

export const SHAPES = Object.freeze({
  I: [[1, 1, 1, 1]],
  J: [[1, 0, 0], [1, 1, 1]],
  L: [[0, 0, 1], [1, 1, 1]],
  O: [[1, 1], [1, 1]],
  S: [[0, 1, 1], [1, 1, 0]],
  T: [[0, 1, 0], [1, 1, 1]],
  Z: [[1, 1, 0], [0, 1, 1]],
});

export function createEmptyBoard(rows = ROWS, cols = COLS) {
  return Array.from({ length: rows }, () => Array(cols).fill(null));
}

export function cloneMatrix(matrix) {
  return matrix.map((row) => [...row]);
}

export function rotateMatrix(matrix, direction = 1) {
  const h = matrix.length;
  const w = matrix[0].length;
  const rotated = Array.from({ length: w }, () => Array(h).fill(0));

  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      if (direction >= 0) rotated[x][h - 1 - y] = matrix[y][x];
      else rotated[w - 1 - x][y] = matrix[y][x];
    }
  }
  return rotated;
}

export function collides(board, matrix, x, y) {
  for (let py = 0; py < matrix.length; py += 1) {
    for (let px = 0; px < matrix[py].length; px += 1) {
      if (!matrix[py][px]) continue;
      const bx = x + px;
      const by = y + py;
      if (bx < 0 || bx >= board[0].length || by >= board.length) return true;
      if (by >= 0 && board[by][bx] !== null) return true;
    }
  }
  return false;
}

function shuffledBag(random) {
  const bag = Object.keys(SHAPES);
  for (let i = bag.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [bag[i], bag[j]] = [bag[j], bag[i]];
  }
  return bag;
}

export class Game {
  constructor({ random = Math.random, sequence = [] } = {}) {
    this.random = random;
    this.initialSequence = [...sequence];
    this.sequence = [];
    this.reset();
  }

  reset() {
    this.sequence = [...this.initialSequence];
    this.board = createEmptyBoard();
    this.score = 0;
    this.lines = 0;
    this.level = 1;
    this.gameOver = false;
    this.paused = false;
    this.queue = [];
    this.current = null;
    this.spawn();
  }

  nextType() {
    if (this.sequence.length) return this.sequence.shift();
    if (!this.queue.length) this.queue.push(...shuffledBag(this.random));
    return this.queue.shift();
  }

  preview(count = 3) {
    const requested = Number.isFinite(count) ? Math.max(0, Math.floor(count)) : 0;
    const scripted = this.sequence.slice(0, requested);
    const generatedCount = requested - scripted.length;
    while (this.queue.length < generatedCount) this.queue.push(...shuffledBag(this.random));
    return [...scripted, ...this.queue.slice(0, generatedCount)];
  }

  spawn(type = this.nextType()) {
    const matrix = cloneMatrix(SHAPES[type]);
    const x = Math.floor((COLS - matrix[0].length) / 2);
    const y = -matrix.length;
    this.current = { type, matrix, x, y, rotation: 0 };
    if (collides(this.board, matrix, x, y)) this.gameOver = true;
    return this.current;
  }

  move(dx, dy) {
    if (this.gameOver || this.paused || !this.current) return false;
    const { matrix } = this.current;
    const nx = this.current.x + dx;
    const ny = this.current.y + dy;
    if (collides(this.board, matrix, nx, ny)) return false;
    this.current.x = nx;
    this.current.y = ny;
    return true;
  }

  rotate(direction = 1) {
    if (this.gameOver || this.paused || !this.current) return false;
    if (this.current.type === 'O') return true;

    const rotated = rotateMatrix(this.current.matrix, direction);
    const kicks = [0, -1, 1, -2, 2];
    for (const dx of kicks) {
      if (!collides(this.board, rotated, this.current.x + dx, this.current.y)) {
        this.current.matrix = rotated;
        this.current.x += dx;
        this.current.rotation = (this.current.rotation + (direction >= 0 ? 1 : 3)) % 4;
        return true;
      }
    }
    if (!collides(this.board, rotated, this.current.x, this.current.y - 1)) {
      this.current.matrix = rotated;
      this.current.y -= 1;
      this.current.rotation = (this.current.rotation + (direction >= 0 ? 1 : 3)) % 4;
      return true;
    }
    return false;
  }

  getDropDistance() {
    if (!this.current) return 0;
    let distance = 0;
    while (!collides(
      this.board,
      this.current.matrix,
      this.current.x,
      this.current.y + distance + 1,
    )) distance += 1;
    return distance;
  }

  softDrop() {
    if (this.gameOver || this.paused || !this.current) return false;
    if (this.move(0, 1)) {
      this.score += 1;
      return true;
    }
    this.lockPiece();
    return false;
  }

  hardDrop() {
    if (this.gameOver || this.paused || !this.current) return 0;
    const distance = this.getDropDistance();
    this.current.y += distance;
    this.score += distance * 2;
    this.lockPiece();
    return distance;
  }

  tick() {
    if (this.gameOver || this.paused) return false;
    if (this.move(0, 1)) return true;
    this.lockPiece();
    return false;
  }

  lockPiece() {
    if (!this.current || this.gameOver || this.paused) return false;
    const { matrix, x, y, type } = this.current;
    let aboveTop = false;

    for (let py = 0; py < matrix.length; py += 1) {
      for (let px = 0; px < matrix[py].length; px += 1) {
        if (!matrix[py][px]) continue;
        const bx = x + px;
        const by = y + py;
        if (by < 0) aboveTop = true;
        else this.board[by][bx] = type;
      }
    }

    if (aboveTop) {
      this.gameOver = true;
      return true;
    }

    const cleared = this.clearLines();
    const rewards = [0, 100, 300, 500, 800];
    this.score += rewards[cleared] * this.level;
    this.lines += cleared;
    this.level = 1 + Math.floor(this.lines / 10);
    this.spawn();
    return true;
  }

  clearLines() {
    const kept = this.board.filter((row) => row.some((cell) => cell === null));
    const cleared = ROWS - kept.length;
    while (kept.length < ROWS) kept.unshift(Array(COLS).fill(null));
    this.board = kept;
    return cleared;
  }

  togglePause() {
    if (!this.gameOver) this.paused = !this.paused;
    return this.paused;
  }

  dropIntervalMs() {
    return Math.max(90, 800 - (this.level - 1) * 65);
  }
}
