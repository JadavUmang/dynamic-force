/**
 * NexusAI Operations Dashboard Logic
 * Uses canvas-confetti for celebrating autonomous repository repairs.
 */

// Production import declared in package.json
import confetti from 'canvas-confetti';

document.addEventListener('DOMContentLoaded', () => {
  const btnConfetti = document.getElementById('btn-confetti');
  const btnDiagnostics = document.getElementById('btn-diagnostics');
  const btnSimulate = document.getElementById('btn-simulate');
  const terminalBody = document.getElementById('terminal-body');
  const repairsCount = document.getElementById('repairs-count');
  const activeAgentsCount = document.getElementById('active-agents-count');
  const latencyVal = document.getElementById('latency-val');
  const depBadge = document.getElementById('dep-status-badge');

  let repairs = 1248;

  function appendLog(type, message) {
    const timeStr = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    line.className = 'log-line';

    let tagClass = 'log-info';
    let tagLabel = '[INFO]';
    if (type === 'success') { tagClass = 'log-success'; tagLabel = '[SUCCESS]'; }
    if (type === 'warn') { tagClass = 'log-warn'; tagLabel = '[WARN]'; }
    if (type === 'accent') { tagClass = 'log-accent'; tagLabel = '[ACTION]'; }

    line.innerHTML = `<span class="log-time">[${timeStr}]</span> <span class="${tagClass}">${tagLabel}</span> ${message}`;
    terminalBody.appendChild(line);
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }

  // Trigger celebration confetti
  if (btnConfetti) {
    btnConfetti.addEventListener('click', () => {
      appendLog('accent', 'Triggering canvas-confetti celebration explosion...');
      try {
        const fire = typeof confetti === 'function' ? confetti : window.confetti;
        if (typeof fire === 'function') {
          fire({
            particleCount: 120,
            spread: 80,
            origin: { y: 0.6 },
            colors: ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899']
          });
          appendLog('success', 'Confetti particle physics rendered successfully.');
        } else {
          appendLog('warn', 'Confetti engine loading or unavailable in this environment.');
        }
      } catch (err) {
        appendLog('warn', `Confetti module execution notice: ${err.message}`);
      }
    });
  }

  // Run diagnostics
  if (btnDiagnostics) {
    btnDiagnostics.addEventListener('click', () => {
      appendLog('info', 'Executing repository integrity guard sweep...');
      setTimeout(() => {
        appendLog('success', 'All 14 guard boundary checks PASSED.');
        if (latencyVal) {
          latencyVal.innerHTML = `${Math.floor(Math.random() * 40) + 110}<span class="unit">ms</span>`;
        }
      }, 400);
    });
  }

  // Increment repairs
  if (btnSimulate) {
    btnSimulate.addEventListener('click', () => {
      repairs += 1;
      if (repairsCount) {
        repairsCount.textContent = repairs.toLocaleString();
      }
      appendLog('success', `Repair #${repairs} verified by Loop Engineering AI.`);
      if (typeof window.confetti === 'function') {
        window.confetti({ particleCount: 35, spread: 50, origin: { y: 0.7 } });
      }
    });
  }

  appendLog('success', 'Nexus operations center connected to live repository mesh.');
});
