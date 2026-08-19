import test from 'node:test';
import assert from 'node:assert/strict';

import { COLS, ROWS, Game, SHAPES, collides } from './core.mjs';

const PIECES = new Set(Object.keys(SHAPES));

function seededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

function assertInvariants(game) {
  assert.equal(game.board.length, ROWS);
  for (const row of game.board) {
    assert.equal(row.length, COLS);
    for (const cell of row) assert.ok(cell === null || PIECES.has(cell));
  }

  assert.ok(Number.isInteger(game.score) && game.score >= 0);
  assert.ok(Number.isInteger(game.lines) && game.lines >= 0);
  assert.equal(game.level, 1 + Math.floor(game.lines / 10));

  if (!game.current) return;
  assert.ok(PIECES.has(game.current.type));
  assert.ok(Number.isInteger(game.current.x));
  assert.ok(Number.isInteger(game.current.y));
  assert.ok(Number.isInteger(game.current.rotation));
  assert.ok(game.current.rotation >= 0 && game.current.rotation < 4);

  if (!game.gameOver) {
    assert.equal(
      collides(game.board, game.current.matrix, game.current.x, game.current.y),
      false,
      'active piece must not overlap the settled board',
    );
    const distance = game.getDropDistance();
    assert.ok(Number.isInteger(distance) && distance >= 0);
    assert.equal(
      collides(game.board, game.current.matrix, game.current.x, game.current.y + distance),
      false,
    );
    assert.equal(
      collides(game.board, game.current.matrix, game.current.x, game.current.y + distance + 1),
      true,
      'drop distance must end immediately above a collision',
    );
  }
}

test('randomized gameplay preserves engine invariants across adversarial action streams', () => {
  const actionNames = ['left', 'right', 'soft', 'hard', 'tick', 'cw', 'ccw', 'pause'];

  for (let seed = 1; seed <= 40; seed += 1) {
    const random = seededRandom(seed);
    const game = new Game({ random });

    for (let step = 0; step < 500; step += 1) {
      if (game.gameOver) {
        game.reset();
        assertInvariants(game);
        continue;
      }

      const action = actionNames[Math.floor(random() * actionNames.length)];
      switch (action) {
        case 'left': game.move(-1, 0); break;
        case 'right': game.move(1, 0); break;
        case 'soft': game.softDrop(); break;
        case 'hard': game.hardDrop(); break;
        case 'tick': game.tick(); break;
        case 'cw': game.rotate(1); break;
        case 'ccw': game.rotate(-1); break;
        case 'pause': game.togglePause(); break;
        default: assert.fail(`unknown action ${action}`);
      }

      assertInvariants(game);
    }
  }
});
