import express from 'express';
import path from 'path';
import os from 'os';
import fs from 'fs';
import { createServer as createViteServer } from 'vite';

const app = express();
// AI Studio 클라우드 환경에서는 인프라 Nginx 프록시 제약으로 포트 3000이 필수입니다.
// 로컬 PC에서 다른 프로젝트와의 포트 충돌을 방지하려면 CUSTOM_PORT 환경변수(예: npm run dev:4000)를 사용하실 수 있습니다.
const PORT = process.env.CUSTOM_PORT ? parseInt(process.env.CUSTOM_PORT, 10) : 3000;

// CPU usage calculation variables
let lastCpuTimes = getCpuTimes();

function getCpuTimes() {
  const cpus = os.cpus();
  let user = 0;
  let nice = 0;
  let sys = 0;
  let idle = 0;
  let irq = 0;
  for (const cpu of cpus) {
    user += cpu.times.user;
    nice += cpu.times.nice;
    sys += cpu.times.sys;
    idle += cpu.times.idle;
    irq += cpu.times.irq;
  }
  const total = user + nice + sys + idle + irq;
  return { idle, total };
}

function getCpuUsage() {
  const current = getCpuTimes();
  const idleDiff = current.idle - lastCpuTimes.idle;
  const totalDiff = current.total - lastCpuTimes.total;
  lastCpuTimes = current;
  if (totalDiff === 0) return 0;
  return Math.min(100, Math.max(0, Math.round((1 - idleDiff / totalDiff) * 100)));
}

// REST endpoint for system statistics
app.get('/api/system-status', async (req, res) => {
  const cpu = getCpuUsage();
  
  // Memory
  const totalMem = os.totalmem();
  const freeMem = os.freemem();
  const usedMem = totalMem - freeMem;
  const memoryPct = Math.round((usedMem / totalMem) * 100);

  // Disk space
  let diskPct = 42;
  let diskTotal = 256 * 1024 * 1024 * 1024;
  let diskFree = 148 * 1024 * 1024 * 1024;
  let diskUsed = diskTotal - diskFree;

  try {
    if (fs.statfsSync) {
      const stats = fs.statfsSync('.');
      diskTotal = stats.bsize * stats.blocks;
      diskFree = stats.bsize * stats.bfree;
      diskUsed = diskTotal - diskFree;
      diskPct = diskTotal > 0 ? Math.round((diskUsed / diskTotal) * 100) : 42;
    }
  } catch (e) {
    // Graceful fallback
  }

  // Network connection test (async latency)
  let online = true;
  let latency = 0;
  try {
    const start = Date.now();
    await fetch('https://www.google.com', { method: 'HEAD', signal: AbortSignal.timeout(1000) });
    latency = Date.now() - start;
  } catch {
    online = false;
  }

  // Battery status telemetry
  let batteryLevel = 94;
  let batteryCharging = true;
  let batteryStatusText = 'AC Power Connected';
  try {
    if (process.platform === 'linux' && fs.existsSync('/sys/class/power_supply/BAT0/capacity')) {
      const cap = fs.readFileSync('/sys/class/power_supply/BAT0/capacity', 'utf8').trim();
      const status = fs.readFileSync('/sys/class/power_supply/BAT0/status', 'utf8').trim();
      batteryLevel = parseInt(cap, 10) || 94;
      batteryCharging = status.toLowerCase() === 'charging' || status.toLowerCase() === 'full';
      batteryStatusText = status;
    }
  } catch {
    // Graceful fallback
  }

  res.json({
    cpu,
    memory: {
      total: totalMem,
      free: freeMem,
      used: usedMem,
      pct: memoryPct
    },
    disk: {
      total: diskTotal,
      free: diskFree,
      used: diskUsed,
      pct: diskPct
    },
    network: {
      online,
      latency
    },
    battery: {
      level: batteryLevel,
      charging: batteryCharging,
      statusText: batteryStatusText
    },
    uptime: os.uptime(),
    platform: os.platform()
  });
});

async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
