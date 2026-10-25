# ⚡ Vite.js Web Application Autonomous Repair Demo

This directory contains a complete, modern **Vite + HTML5 + CSS3 + Vanilla JavaScript** web application benchmark designed to showcase **Loop Engineering AI** resolving `package.json` dependency defects live in front of professionals.

---

## 📁 Architecture & File Layout

- **`index.html`**: Futuristic NexusAI operations center dashboard (dark glassmorphism, glowing metrics, live terminal log simulator).
- **`src/style.css`**: Modern CSS design system with variables, backdrop blur, glowing gradients, and responsive layout.
- **`src/main.js`**: Interactive ES Module logic that imports and uses `canvas-confetti`.
- **`vite.config.js`**: Standard Vite project configuration.
- **`package.json`**: Intentional dependency defect (`"canvas-confetti": "MISSING"`).
- **`test.js`**: Verification test suite executed via `node test.js` (or `npm test`).
- **`demo_agent.py`**: Automated guarded repair loop runner.
- **`run_demo.bat`**: 1-click double-clickable launcher.
- **`reset_demo.bat`**: 1-click double-clickable reset tool.

---

## 🎬 How to Run & Present

### 1. Navigate to this directory:
```powershell
cd vite_demo
```

### 2. Live Split-Screen Setup:
- **Left Screen**: Open `vite_demo/package.json` in your editor tab (notice line 11: `"canvas-confetti": "MISSING"`).
- **Right Screen**: Open your terminal in `vite_demo` and run:
  ```powershell
  python demo_agent.py
  ```
  *(Or double-click `run_demo.bat`)*

### 3. During the Execution:
1. **Baseline Test**: Fails with `ERR_MODULE_NOT_FOUND` because `'canvas-confetti'` has version `'MISSING'`.
2. **Stage 1**: LLM analyzes the error log and identifies the missing dependency version.
3. **Stage 2**: Coding AI Agent shows proposed change in `package.json`:
   ```diff
   - "canvas-confetti": "MISSING"
   + "canvas-confetti": "^1.9.2"
   ```
4. Hit **`Enter`** to approve.
5. **Real-Time Live Edit**: Watch `package.json` in your left-hand editor tab update live to `"^1.9.2"`.
6. **Stage 3**: Validation tests pass 100%, and the AI prints the uncommitted file diff. No git commit is created.

### 4. Reset for Another Live Demo:
Double-click `reset_demo.bat` (or run `python -c "..."`) to restore `package.json` back to `"MISSING"`.
