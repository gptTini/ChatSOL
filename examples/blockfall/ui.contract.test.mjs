import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const html = await readFile(new URL('./index.html', import.meta.url), 'utf8');
const app = await readFile(new URL('./app.mjs', import.meta.url), 'utf8');

function touchActions() {
  return new Set([...html.matchAll(/data-action="([^"]+)"/g)].map((match) => match[1]));
}

test('every DOM id queried by app.mjs exists in index.html', () => {
  const queriedIds = [...app.matchAll(/querySelector\('#([^']+)'\)/g)].map((match) => match[1]);
  assert.ok(queriedIds.length > 0, 'expected app.mjs to query DOM ids');
  for (const id of queriedIds) {
    assert.match(html, new RegExp(`id=["']${id}["']`), `missing #${id} in index.html`);
  }
});

test('touch controls expose all essential gameplay and lifecycle actions', () => {
  const actions = touchActions();
  for (const action of ['left', 'right', 'down', 'rotate', 'drop', 'pause', 'restart']) {
    assert.ok(actions.has(action), `touch UI does not expose ${action}`);
  }
});

test('touch actions are recognized by the app action dispatcher', () => {
  for (const action of touchActions()) {
    assert.match(app, new RegExp(`case ['"]${action}['"]:`), `unhandled touch action: ${action}`);
  }
});

test('game-over and pause overlays have lifecycle controls available on touch', () => {
  const actions = touchActions();
  assert.ok(actions.has('restart'), 'game-over overlay can require restart but touch UI has no restart action');
  assert.ok(actions.has('pause'), 'paused game cannot be resumed from a touch-only UI');
});
