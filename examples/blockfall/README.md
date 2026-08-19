# Blockfall

A small falling-block puzzle used as a ChatSOL multi-session development experiment. The game is intentionally dependency-free: the engine is a pure ES module, the UI uses Canvas, and tests use Node's built-in test runner.

## Run

From the repository root:

```bash
python -m http.server 8000
```

Then open `/examples/blockfall/` in your browser.

## Controls

- Left / right arrows: move
- Down arrow: soft drop
- Up arrow or X: rotate clockwise
- Z: rotate counter-clockwise
- Space: hard drop
- P: pause
- R: restart

Touch controls appear on narrow screens.

## Worker split

This demo was partitioned so independent Sol sessions can work without overlapping write scopes:

- `session/blockfall-core` — `examples/blockfall/core.mjs`
- `session/blockfall-ui` — `index.html`, `style.css`, `app.mjs`
- `session/blockfall-tests` — `core.test.mjs` and Blockfall CI
- `session/blockfall-docs` — this file

All worker branches target `sol/blockfall-v1` before the integration branch is merged into `main`.

## Rules implemented

- 10×20 board
- seven standard tetromino shapes
- shuffled seven-piece bags
- movement and clockwise/counter-clockwise rotation with lightweight wall kicks
- soft and hard drop
- ghost piece
- line clearing and classic-style line rewards
- level increase every 10 lines with faster gravity
- pause, restart, next-piece preview, and game-over detection
