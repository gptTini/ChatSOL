import test from 'node:test';
import assert from 'node:assert/strict';

import {
  COLS,
  ROWS,
  Game,
  SHAPES,
  collides,
  createEmptyBoard,
  rotateMatrix,
} from './core.mjs';

test('empty board is 20x10 and independent by row', () => {
  const board = createEmptyBoard();
  assert.equal(board.length, ROWS);
  assert.equal(board[0].length, COLS);
  board[0][0] = 'X';
  assert.equal(board[1][0], null);
});

test('rotation is reversible', () => {
  const original = SHAPES.T;
  const clockwise = rotateMatrix(original, 1);
  const restored = rotateMatrix(clockwise, -1);
  assert.deepEqual(restored, original);
});

test('collision rejects walls and floor but permits cells above the board', () => {
  const board = createEmptyBoard();
  assert.equal(collides(board, SHAPES.O, -1, 0), true);
  assert.equal(collides(board, SHAPES.O, 0, ROWS - 1), true);
  assert.equal(collides(board, SHAPES.O, 4, -2), false);
});

test('movement cannot pass through an occupied cell', () => {
  const game = new Game({ sequence: ['O', 'I'] });
  game.current.x = 4;
  game.current.y = 5;
  game.board[6][6] = 'Z';
  assert.equal(game.move(1, 0), false);
  assert.equal(game.current.x, 4);
});

test('hard drop locks the piece and awards two points per dropped row', () => {
  const game = new Game({ sequence: ['O', 'I'] });
  const distance = game.getDropDistance();
  const dropped = game.hardDrop();
  assert.equal(dropped, distance);
  assert.equal(game.score, distance * 2);
  assert.equal(game.current.type, 'I');
  assert.equal(game.board[ROWS - 1].filter(Boolean).length, 2);
});

test('zero-distance hard drop still locks and spawns the next piece', () => {
  const game = new Game({ sequence: ['O', 'I'] });
  game.current = {
    type: 'O',
    matrix: SHAPES.O.map((row) => [...row]),
    x: 4,
    y: ROWS - 2,
    rotation: 0,
  };

  assert.equal(game.getDropDistance(), 0);
  assert.equal(game.hardDrop(), 0);
  assert.equal(game.current.type, 'I');
  assert.equal(game.board[ROWS - 1][4], 'O');
  assert.equal(game.board[ROWS - 1][5], 'O');
});

test('locking a line clears it and awards line-clear score', () => {
  const game = new Game({ sequence: ['I'] });
  game.board = createEmptyBoard();
  game.board[ROWS - 1] = Array(COLS).fill('J');
  game.board[ROWS - 1][8] = null;
  game.board[ROWS - 1][9] = null;
  game.current = {
    type: 'O',
    matrix: SHAPES.O.map((row) => [...row]),
    x: 8,
    y: ROWS - 2,
    rotation: 0,
  };

  game.lockPiece();
  assert.equal(game.lines, 1);
  assert.equal(game.score, 100);
  assert.equal(game.board.length, ROWS);
  assert.ok(game.board[0].every((cell) => cell === null));
});

test('four-line clear awards the tetris reward and preserves board dimensions', () => {
  const game = new Game({ sequence: ['O'] });
  game.board = createEmptyBoard();
  for (let y = ROWS - 4; y < ROWS; y += 1) {
    game.board[y] = Array(COLS).fill('J');
    game.board[y][COLS - 1] = null;
  }
  game.current = {
    type: 'I',
    matrix: rotateMatrix(SHAPES.I, 1),
    x: COLS - 1,
    y: ROWS - 4,
    rotation: 1,
  };

  assert.equal(game.lockPiece(), true);
  assert.equal(game.lines, 4);
  assert.equal(game.score, 800);
  assert.equal(game.board.length, ROWS);
  assert.ok(game.board.every((row) => row.length === COLS));
  assert.ok(game.board.every((row) => row.every((cell) => cell === null)));
});

test('level advances every ten cleared lines and accelerates gravity', () => {
  const game = new Game({ sequence: ['I'] });
  const levelOne = game.dropIntervalMs();
  game.lines = 10;
  game.level = 2;
  assert.ok(game.dropIntervalMs() < levelOne);
});

test('line clear crossing a level boundary scores at the pre-clear level', () => {
  const game = new Game({ sequence: ['I'] });
  game.lines = 9;
  game.level = 1;
  game.board[ROWS - 1] = Array(COLS).fill('J');
  game.board[ROWS - 1][8] = null;
  game.board[ROWS - 1][9] = null;
  game.current = {
    type: 'O',
    matrix: SHAPES.O.map((row) => [...row]),
    x: 8,
    y: ROWS - 2,
    rotation: 0,
  };

  game.lockPiece();
  assert.equal(game.lines, 10);
  assert.equal(game.level, 2);
  assert.equal(game.score, 100);
});

test('a piece locking above the visible board ends the game', () => {
  const game = new Game({ sequence: ['O'] });
  game.current = {
    type: 'O',
    matrix: SHAPES.O.map((row) => [...row]),
    x: 4,
    y: -1,
    rotation: 0,
  };
  assert.equal(game.lockPiece(), true);
  assert.equal(game.gameOver, true);
});

test('pause blocks movement until resumed', () => {
  const game = new Game({ sequence: ['T'] });
  const x = game.current.x;
  game.togglePause();
  assert.equal(game.move(1, 0), false);
  assert.equal(game.current.x, x);
  game.togglePause();
  assert.equal(game.move(1, 0), true);
});

test('pause is a true freeze for soft drop, hard drop, tick, rotation, and direct locking', () => {
  const game = new Game({ sequence: ['O', 'I'] });
  game.current.y = ROWS - 2;
  game.togglePause();

  const before = structuredClone({
    board: game.board,
    current: game.current,
    score: game.score,
    lines: game.lines,
    level: game.level,
    gameOver: game.gameOver,
  });

  assert.equal(game.softDrop(), false);
  assert.equal(game.hardDrop(), 0);
  assert.equal(game.tick(), false);
  assert.equal(game.rotate(1), false);
  assert.equal(game.lockPiece(), false);

  const after = {
    board: game.board,
    current: game.current,
    score: game.score,
    lines: game.lines,
    level: game.level,
    gameOver: game.gameOver,
  };
  assert.deepEqual(after, before);
});

test('game-over state rejects all gameplay mutation paths', () => {
  const game = new Game({ sequence: ['T', 'I'] });
  game.gameOver = true;
  const before = structuredClone({ board: game.board, current: game.current, score: game.score });

  assert.equal(game.move(1, 0), false);
  assert.equal(game.rotate(1), false);
  assert.equal(game.softDrop(), false);
  assert.equal(game.hardDrop(), 0);
  assert.equal(game.tick(), false);
  assert.equal(game.lockPiece(), false);

  assert.deepEqual(
    { board: game.board, current: game.current, score: game.score },
    before,
  );
});

test('scripted preview matches the actual next pieces without consuming them', () => {
  const game = new Game({ sequence: ['T', 'I', 'O'], random: () => 0.42 });
  assert.equal(game.current.type, 'T');
  assert.deepEqual(game.preview(2), ['I', 'O']);
  assert.deepEqual(game.preview(2), ['I', 'O']);

  game.hardDrop();
  assert.equal(game.current.type, 'I');
  assert.deepEqual(game.preview(1), ['O']);
});

test('reset restores the configured deterministic sequence and clears runtime state', () => {
  const game = new Game({ sequence: ['T', 'I', 'O'], random: () => 0.42 });
  game.hardDrop();
  game.hardDrop();
  assert.notEqual(game.score, 0);
  assert.equal(game.current.type, 'O');

  game.reset();

  assert.equal(game.current.type, 'T');
  assert.deepEqual(game.preview(2), ['I', 'O']);
  assert.equal(game.score, 0);
  assert.equal(game.lines, 0);
  assert.equal(game.level, 1);
  assert.equal(game.paused, false);
  assert.equal(game.gameOver, false);
  assert.ok(game.board.every((row) => row.every((cell) => cell === null)));
});

test('a generated seven-piece bag contains every tetromino exactly once', () => {
  const game = new Game({ random: () => 0.42 });
  const first = game.current.type;
  const remaining = game.preview(6);
  const bag = [first, ...remaining];
  assert.equal(bag.length, 7);
  assert.deepEqual([...new Set(bag)].sort(), Object.keys(SHAPES).sort());
});

test('two consecutive generated bags each contain all seven tetrominoes once', () => {
  const game = new Game({ random: () => 0.42 });
  const pieces = [game.current.type, ...game.preview(13)];
  const expected = Object.keys(SHAPES).sort();

  assert.deepEqual([...new Set(pieces.slice(0, 7))].sort(), expected);
  assert.deepEqual([...new Set(pieces.slice(7, 14))].sort(), expected);
});
