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

test('level advances every ten cleared lines and accelerates gravity', () => {
  const game = new Game({ sequence: ['I'] });
  const levelOne = game.dropIntervalMs();
  game.lines = 10;
  game.level = 2;
  assert.ok(game.dropIntervalMs() < levelOne);
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
  game.lockPiece();
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
