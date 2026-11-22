import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Bell,
  CheckSquare,
  Download,
  FileSpreadsheet,
  Globe,
  Grid,
  List,
  Moon,
  Monitor,
  Power,
  RefreshCw,
  RotateCcw,
  RotateCw,
  Search,
  Send,
  Square,
  Upload,
  Zap,
} from 'lucide-react';
import { LabDevice, LabDeviceStatus, LabScheduleProfile, ThemeType } from '../types';
import { AppLang } from '../utils/i18n';

export const LAB_SCHEDULE_PROFILES: LabScheduleProfile[] = [
  {
    id: 'standard-day',
    nameKo: '🏫 1. 정규 컴퓨터실 일과 (08:50 알람 + 12:30 재부팅 + 17:30 종료)',
    nameEn: '🏫 1. Standard Lab Day (08:50 Bell + 12:30 Reboot + 17:30 Shutdown)',
    descKo: '평일 수업 준비 알람, 점심 리프레시 재부팅, 방과후 일괄 종료 3종 규칙 일괄 배포',
    descEn: 'Deploys 3 weekday rules: 08:50 bell, 12:30 lunch reboot, and 17:30 shutdown.',
    rulesCount: 3,
    summaryRules: [
      { labelKo: '1교시 수업 준비 알람', labelEn: '1st Period Prep Bell', time: '08:50', mode: 'alarm' },
      { labelKo: '점심시간 랩실 리프레시 재부팅', labelEn: 'Lunch Lab Reboot', time: '12:30', mode: 'reboot' },
      { labelKo: '방과후 컴퓨터실 일괄 종료', labelEn: 'EOD Lab Shutdown', time: '17:30', mode: 'shutdown' },
    ],
  },
  {
    id: 'after-hours-eco',
    nameKo: '🌙 2. 야간·방과후 절전 & 안전 종료 (18:00 절전 + 21:30 최종 종료)',
    nameEn: '🌙 2. After-Hours Eco Policy (18:00 Sleep + 21:30 Final Shutdown)',
    descKo: '방과후 미사용 좌석 자동 절전 후 야간 보안 소등 최종 종료 규칙 배포',
    descEn: 'Enters Sleep on idle after 18:00 and enforces hard shutdown at 21:30.',
    rulesCount: 2,
    summaryRules: [
      { labelKo: '방과후 미사용 PC 절전', labelEn: 'After-School Idle Sleep', time: '18:00', mode: 'sleep' },
      { labelKo: '야간 컴퓨터실 최종 종료', labelEn: 'Night Final Shutdown', time: '21:30', mode: 'shutdown' },
    ],
  },
  {
    id: 'exam-focus',
    nameKo: '📝 3. 실기시험·수업 집중 통제 (11:45 알람 + 11:50 화면 끄기/잠금)',
    nameEn: '📝 3. Exam / Class Focus Control (11:45 Alert + 11:50 Lock/Screen Off)',
    descKo: '시험 종료 5분 전 예고 알람 후 일괄 화면 소등 및 워크스테이션 잠금',
    descEn: 'Triggers 5-min warning bell then locks screens across all seats.',
    rulesCount: 2,
    summaryRules: [
      { labelKo: '시험 종료 5분 전 알림', labelEn: 'Exam 5m Warning', time: '11:45', mode: 'alarm' },
      { labelKo: '시험 종료 화면 잠금', labelEn: 'Exam End Screen Off', time: '11:50', mode: 'screenoff' },
    ],
  },
  {
    id: 'weekend-maint',
    nameKo: '🛠️ 4. 주말 대청소 & 임시파일 초기화 (일 04:00 리셋 + 04:30 종료)',
    nameEn: '🛠️ 4. Weekend Clean Reset (Sun 04:00 Reboot + 04:30 Off)',
    descKo: '일요일 새벽 %TEMP% 정리 재부팅 후 월요일 수업 전까지 안전 종료 대기',
    descEn: 'Sunday 04:00 clean-temp reboot followed by 04:30 safe shutdown.',
    rulesCount: 2,
    summaryRules: [
      { labelKo: '주말 임시파일 정리 리셋', labelEn: 'Weekend Temp Clean Reboot', time: '04:00', mode: 'reboot' },
      { labelKo: '점검 완료 후 안전 종료', labelEn: 'Post-Maint Safe Off', time: '04:30', mode: 'shutdown' },
    ],
  },
];

export function generate50LabPreset(subnetPrefix = '192.168.10.', startLastOctet = 101, cols = 10): LabDevice[] {
  const devices: LabDevice[] = [];
  for (let i = 0; i < 50; i++) {
    const idx = i + 1;
    const seatNo = `LAB-${String(idx).padStart(2, '0')}`;
    const last = startLastOctet + i;
    const ip = `${subnetPrefix}${last}`;
    const row = Math.floor(i / cols) + 1;
    const col = (i % cols) + 1;
    const group = idx <= 25 ? 'Lab-Room-A (1~25)' : 'Lab-Room-B (26~50)';
    // Seed realistic lab conditions: 42 online, 6 offline (for WOL testing), 2 with active countdowns
    const isOffline = idx === 12 || idx === 24 || idx === 31 || idx === 39 || idx === 47 || idx === 50;
    const hasTimer = idx === 3 || idx === 18 || idx === 41;
    const macHex = idx.toString(16).toUpperCase().padStart(2, '0');

    devices.push({
      ip,
      seatNo,
      hostname: `LAB1-PC${String(idx).padStart(2, '0')}`,
      mac: `00:E0:4C:10:A0:${macHex}`,
      group,
      row,
      col,
      memo: `Row ${row} Seat ${col}`,
      isSelf: idx === 1,
      status: isOffline ? 'offline' : 'online',
      latencyMs: isOffline ? undefined : 2 + (idx % 9),
      rulesCount: isOffline ? 0 : (idx % 3) + 1,
      timerRunning: hasTimer,
      remainingSeconds: hasTimer ? 640 + idx * 15 : 0,
      activeMode: hasTimer ? 'shutdown' : undefined,
      lastAck: isOffline ? 'Offline' : 'Ready',
    });
  }
  return devices;
}

export function createInitial5Devices(): LabDevice[] {
  return [
    {
      ip: '192.168.0.10',
      seatNo: '01',
      hostname: 'MY-ADMIN-PC',
      mac: '00:1A:2B:3C:4D:01',
      group: 'Default',
      row: 1,
      col: 1,
      isSelf: true,
      status: 'online',
      latencyMs: 1,
      rulesCount: 2,
      timerRunning: true,
      remainingSeconds: 1520,
      activeMode: 'shutdown',
      lastAck: '1ms',
    },
    {
      ip: '192.168.0.15',
      seatNo: '02',
      hostname: 'DEV-PC-01',
      mac: '00:1A:2B:3C:4D:02',
      group: 'Default',
      row: 1,
      col: 2,
      status: 'online',
      latencyMs: 3,
      rulesCount: 1,
      lastAck: '3ms',
    },
    {
      ip: '192.168.0.22',
      seatNo: '03',
      hostname: 'DESIGN-PC-02',
      mac: '00:1A:2B:3C:4D:03',
      group: 'Default',
      row: 1,
      col: 3,
      status: 'online',
      latencyMs: 4,
      rulesCount: 2,
      lastAck: '4ms',
    },
    {
      ip: '192.168.0.35',
      seatNo: '04',
      hostname: 'LAB-SERVER-A',
      mac: '00:1A:2B:3C:4D:04',
      group: 'Default',
      row: 1,
      col: 4,
      status: 'offline',
      rulesCount: 0,
      lastAck: 'Offline',
    },
    {
      ip: '192.168.0.48',
      seatNo: '05',
      hostname: 'TEST-BENCH-09',
      mac: '00:1A:2B:3C:4D:05',
      group: 'Default',
      row: 1,
      col: 5,
      status: 'online',
      latencyMs: 5,
      rulesCount: 1,
      lastAck: '5ms',
    },
  ];
}

function ipToInt(ip: string): number {
  const parts = ip.trim().split('.').map(Number);
  if (parts.length !== 4 || parts.some(n => Number.isNaN(n) || n < 0 || n > 255)) {
    throw new Error(`Invalid IPv4: ${ip}`);
  }
  return (((parts[0] << 24) >>> 0) + (parts[1] << 16) + (parts[2] << 8) + parts[3]) >>> 0;
}

function intToIp(num: number): string {
  return [(num >>> 24) & 255, (num >>> 16) & 255, (num >>> 8) & 255, num & 255].join('.');
}

function parseCsvRoster(csvText: string): LabDevice[] {
  const lines = csvText
    .replace(/^\uFEFF/, '')
    .split(/\r?\n/)
    .map(l => l.trim())
    .filter(Boolean);
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
  const devices: LabDevice[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = lines[i].split(',').map(c => c.trim());
    const rowObj: Record<string, string> = {};
    headers.forEach((h, idx) => {
      rowObj[h] = cells[idx] || '';
    });
    const ip = rowObj['ip'] || rowObj['ip_address'];
    if (!ip) continue;
    const seatNo = rowObj['seat_no'] || rowObj['seat'] || String(i).padStart(2, '0');
    const mac = (rowObj['mac'] || '').toUpperCase();
    const hostname = rowObj['hostname'] || rowObj['host'] || `LAB-${seatNo}`;
    const group = rowObj['group'] || 'Default';
    const rowNum = parseInt(rowObj['row'] || '0', 10) || Math.floor((i - 1) / 10) + 1;
    const colNum = parseInt(rowObj['col'] || '0', 10) || ((i - 1) % 10) + 1;
    devices.push({
      ip,
      seatNo,
      hostname,
      mac,
      group,
      row: rowNum,
      col: colNum,
      memo: rowObj['memo'] || '',
      status: i % 9 === 0 ? 'offline' : 'online',
      latencyMs: i % 9 === 0 ? undefined : 2 + (i % 7),
      rulesCount: 1,
      lastAck: i % 9 === 0 ? 'Offline' : 'Imported',
    });
  }
  return devices;
}

function formatTimerShort(sec?: number): string {
  if (!sec || sec <= 0) return '-';
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return h > 0 ? `${h}:${String(mm).padStart(2, '0')}:${String(s).padStart(2, '0')}` : `${String(mm).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export interface LabNetworkFleetPanelProps {
  lang: AppLang;
  theme: ThemeType;
  devices?: LabDevice[];
  onDevicesChange?: React.Dispatch<React.SetStateAction<LabDevice[]>>;
  selectedIps?: string[];
  onSelectedIpsChange?: React.Dispatch<React.SetStateAction<string[]>>;
  onToast?: (msg: string, type?: 'success' | 'info' | 'error') => void;
  onPlaySound?: (kind: 'buttonClick' | 'actionSuccess' | 'timerAlarm') => void;
  onTargetIpsSync?: (ipsJoined: string) => void;
}

export const LabNetworkFleetPanel: React.FC<LabNetworkFleetPanelProps> = ({
  lang,
  theme,
  devices: controlledDevices,
  onDevicesChange,
  selectedIps: controlledSelectedIps,
  onSelectedIpsChange,
  onToast,
  onPlaySound,
  onTargetIpsSync,
}) => {
  const isEn = lang === 'en';
  const L = (ko: string, en: string) => (isEn ? en : ko);
  const isLight = theme === 'white' || theme === 'beige';

  const [internalDevices, setInternalDevices] = useState<LabDevice[]>(() => generate50LabPreset('192.168.10.', 101, 10));
  const [internalSelectedIps, setInternalSelectedIps] = useState<string[]>(['192.168.10.101', '192.168.10.102', '192.168.10.103']);

  const devices = controlledDevices ?? internalDevices;
  const setDevices = onDevicesChange ?? setInternalDevices;
  const selectedIps = controlledSelectedIps ?? internalSelectedIps;
  const setSelectedIps = onSelectedIpsChange ?? setInternalSelectedIps;

  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [gridCols, setGridCols] = useState<5 | 8 | 10>(10);
  const [groupFilter, setGroupFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<'all' | LabDeviceStatus>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [autoPoll, setAutoPoll] = useState(true);
  const [wolStepMs, setWolStepMs] = useState<number>(250);
  const [selectedProfileId, setSelectedProfileId] = useState<string>(LAB_SCHEDULE_PROFILES[0].id);

  // Batch Progress & Failed Targets
  const [failedIps, setFailedIps] = useState<string[]>([]);
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ done: 0, total: 0, ok: 0, fail: 0, label: '' });
  const [lastBatchAction, setLastBatchAction] = useState<{ label: string; kind: 'power' | 'profile' | 'poll' | 'clear'; cmd?: string } | null>(null);

  // IP Range Scanner Panel
  const [showRangeScanner, setShowRangeScanner] = useState(false);
  const [rangeStartIp, setRangeStartIp] = useState('192.168.10.101');
  const [rangeEndIp, setRangeEndIp] = useState('192.168.10.150');
  const [rangeSeatPrefix, setRangeSeatPrefix] = useState('LAB-');
  const [rangeGroup, setRangeGroup] = useState('Lab-Room-A (1~50)');

  // Table Sorting
  const [sortBy, setSortBy] = useState<'seatNo' | 'ip' | 'status' | 'rulesCount'>('seatNo');
  const [sortDesc, setSortDesc] = useState(false);

  // Live Console Logs
  const [consoleLogs, setConsoleLogs] = useState<string[]>(() => [
    isEn
      ? `[${new Date().toLocaleTimeString('en-US')}] Lab Control Tower ready (50-PC seat map · Parallel worker · Staggered WOL).`
      : `[${new Date().toLocaleTimeString('ko-KR')}] 50대 컴퓨터실 통합 관제 타워 준비 완료 (병렬 전송 · 좌석 그리드 · 순차 WOL 지원).`,
  ]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Tick local countdowns + periodic 15s heartbeat poll
  useEffect(() => {
    let secCount = 0;
    const id = setInterval(() => {
      secCount += 1;
      setDevices(prev => {
        let changed = false;
        const next = prev.map(d => {
          if (d.timerRunning && d.remainingSeconds && d.remainingSeconds > 0) {
            changed = true;
            return { ...d, remainingSeconds: d.remainingSeconds - 1 };
          }
          return d;
        });
        if (autoPoll && secCount % 15 === 0) {
          return next.map(d =>
            d.status === 'online'
              ? { ...d, latencyMs: Math.max(1, (d.latencyMs || 4) + ((secCount % 3) - 1)), lastAck: new Date().toLocaleTimeString([], { hour12: false }) }
              : d
          );
        }
        return changed ? next : prev;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [autoPoll, setDevices]);

  // Keep parent Target IP input synchronized if callback provided
  useEffect(() => {
    if (onTargetIpsSync) {
      onTargetIpsSync(selectedIps.join(', '));
    }
  }, [selectedIps, onTargetIpsSync]);

  const appendLog = (line: string) => {
    const ts = new Date().toLocaleTimeString(isEn ? 'en-US' : 'ko-KR', { hour12: false });
    setConsoleLogs(prev => [`[${ts}] ${line}`, ...prev.slice(0, 49)]);
  };

  const groups = useMemo(() => {
    const s = new Set<string>();
    devices.forEach(d => s.add(d.group || 'Default'));
    return ['ALL', ...Array.from(s)];
  }, [devices]);

  const filteredDevices = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const list = devices.filter(d => {
      if (groupFilter !== 'ALL' && d.group !== groupFilter) return false;
      if (statusFilter !== 'all' && d.status !== statusFilter) return false;
      if (q) {
        const hay = `${d.seatNo} ${d.ip} ${d.hostname} ${d.mac} ${d.memo || ''}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    return [...list].sort((a, b) => {
      let cmp = 0;
      if (sortBy === 'seatNo') cmp = a.seatNo.localeCompare(b.seatNo, undefined, { numeric: true });
      else if (sortBy === 'ip') cmp = a.ip.localeCompare(b.ip, undefined, { numeric: true });
      else if (sortBy === 'status') cmp = a.status.localeCompare(b.status);
      else if (sortBy === 'rulesCount') cmp = a.rulesCount - b.rulesCount;
      return sortDesc ? -cmp : cmp;
    });
  }, [devices, groupFilter, statusFilter, searchQuery, sortBy, sortDesc]);

  const kpis = useMemo(() => {
    const online = devices.filter(d => d.status === 'online').length;
    const offline = devices.filter(d => d.status === 'offline').length;
    const failed = devices.filter(d => d.status === 'failed').length;
    return { total: devices.length, online, offline, failed, selected: selectedIps.length };
  }, [devices, selectedIps]);

  // -----------------------------------------------------------------------
  // Parallel Batch Coordinator (Simulated TCP 9988 + Live Progress Bar)
  // -----------------------------------------------------------------------
  const runBatchOnTargets = async (
    label: string,
    targetList: string[],
    opts: { kind: 'power' | 'profile' | 'poll' | 'clear'; cmd?: string; rulesAdded?: number; isRetry?: boolean }
  ) => {
    if (batchRunning) return;
    if (targetList.length === 0) {
      onToast?.(L('⚠️ 제어할 PC를 최소 1대 이상 선택해주세요.', '⚠️ Select at least one target PC first.'), 'error');
      return;
    }

    onPlaySound?.(opts.cmd === 'alarm' ? 'timerAlarm' : 'actionSuccess');
    setBatchRunning(true);
    setLastBatchAction({ label, kind: opts.kind, cmd: opts.cmd });
    setBatchProgress({ done: 0, total: targetList.length, ok: 0, fail: 0, label });

    const chunkSize = 10; // Simulated bounded ThreadPoolExecutor wave
    let done = 0;
    let ok = 0;
    let fail = 0;
    const newFailed: string[] = [];

    for (let i = 0; i < targetList.length; i += chunkSize) {
      const wave = targetList.slice(i, i + chunkSize);
      await new Promise(res => setTimeout(res, 110));

      const waveSucceeded: string[] = [];
      const waveFailed: string[] = [];

      wave.forEach(ip => {
        const dev = devices.find(d => d.ip === ip);
        // On initial dispatch, offline hosts fail TCP reachability; on Retry Failed, give a realistic recovery chance or recover if forced online
        const shouldFail = !opts.isRetry ? dev?.status === 'offline' : false;
        done += 1;
        if (shouldFail) {
          fail += 1;
          waveFailed.push(ip);
          newFailed.push(ip);
        } else {
          ok += 1;
          waveSucceeded.push(ip);
        }
      });

      setDevices(prev =>
        prev.map(d => {
          if (waveFailed.includes(d.ip)) {
            return {
              ...d,
              status: 'failed',
              lastError: L('TCP 9988 무응답 (오프라인)', 'TCP 9988 timeout (offline)'),
              lastAck: 'ERR Timeout',
            };
          }
          if (waveSucceeded.includes(d.ip)) {
            const nextRules =
              opts.kind === 'profile'
                ? opts.rulesAdded || 3
                : opts.kind === 'clear'
                ? 0
                : d.rulesCount;
            return {
              ...d,
              status: 'online',
              rulesCount: nextRules,
              latencyMs: d.latencyMs || 3,
              lastError: undefined,
              lastAck: `${label} OK`,
              ...(opts.cmd === 'sleep' ? { activeMode: 'sleep' } : {}),
            };
          }
          return d;
        })
      );

      setBatchProgress({ done, total: targetList.length, ok, fail, label });
    }

    setFailedIps(newFailed);
    setBatchRunning(false);
    appendLog(
      L(
        `[${label}] 병렬 완료 — 대상 ${targetList.length}대 | 성공 ${ok}대 | 실패 ${fail}대`,
        `[${label}] Batch finished — ${targetList.length} targets · ${ok} OK · ${fail} Failed`
      )
    );
    onToast?.(
      fail > 0
        ? L(
            `⚠️ ${label}: 성공 ${ok}대 / 실패 ${fail}대 ("실패 재시도" 버튼으로 재전송 가능)`,
            `⚠️ ${label}: ${ok} succeeded, ${fail} failed (use Retry Failed).`
          )
        : L(`✅ ${label}: ${ok}대 PC에 병렬 전송 완료`, `✅ ${label}: Dispatched to ${ok} PC(s)`),
      fail > 0 ? 'info' : 'success'
    );
  };

  // Staggered Wake-on-LAN Execution
  const runStaggeredWol = async () => {
    if (batchRunning) return;
    const offlineSelected = selectedIps.filter(ip => {
      const d = devices.find(x => x.ip === ip);
      return d && d.mac;
    });
    const fallbackTargets =
      offlineSelected.length > 0
        ? offlineSelected
        : filteredDevices.filter(d => d.status !== 'online' && d.mac).map(d => d.ip);

    if (fallbackTargets.length === 0) {
      onToast?.(L('⚡ 깨울 오프라인/WOL 대상 PC가 없습니다.', '⚡ No offline WOL targets selected.'), 'info');
      return;
    }

    onPlaySound?.('actionSuccess');
    setBatchRunning(true);
    const label = `Staggered WOL (${wolStepMs}ms)`;
    setBatchProgress({ done: 0, total: fallbackTargets.length, ok: 0, fail: 0, label });

    const stepDelay = Math.min(250, Math.max(40, Math.round(wolStepMs / 3)));
    for (let i = 0; i < fallbackTargets.length; i++) {
      const ip = fallbackTargets[i];
      await new Promise(res => setTimeout(res, stepDelay));
      setDevices(prev =>
        prev.map(d =>
          d.ip === ip
            ? { ...d, status: 'online', latencyMs: 6, lastError: undefined, lastAck: `WOL (${wolStepMs}ms)` }
            : d
        )
      );
      setBatchProgress({ done: i + 1, total: fallbackTargets.length, ok: i + 1, fail: 0, label });
    }

    setFailedIps(prev => prev.filter(ip => !fallbackTargets.includes(ip)));
    setBatchRunning(false);
    appendLog(
      L(
        `⚡ 순차 WOL 기상 완료: ${fallbackTargets.length}대 (${wolStepMs}ms 간격)`,
        `⚡ Staggered WOL completed: ${fallbackTargets.length} PC(s) at ${wolStepMs}ms step.`
      )
    );
    onToast?.(
      L(
        `⚡ ${fallbackTargets.length}대 PC에 ${wolStepMs}ms 간격 순차 WOL 패킷 전송 완료`,
        `⚡ Dispatched staggered WOL (${wolStepMs}ms step) to ${fallbackTargets.length} PCs.`
      ),
      'success'
    );
  };

  // IP Range Scan Execution
  const handleRunRangeScan = () => {
    try {
      const startNum = ipToInt(rangeStartIp);
      const endNum = ipToInt(rangeEndIp);
      if (endNum < startNum) throw new Error(L('종료 IP가 시작 IP보다 작습니다.', 'End IP must be >= Start IP.'));
      const count = endNum - startNum + 1;
      if (count > 254) throw new Error(L('최대 254대까지만 일괄 스캔할 수 있습니다.', 'Maximum 254 hosts per scan.'));

      const scanned: LabDevice[] = [];
      for (let i = 0; i < count; i++) {
        const idx = i + 1;
        const ip = intToIp(startNum + i);
        const seatNo = `${rangeSeatPrefix}${String(idx).padStart(2, '0')}`;
        const isOff = idx % 11 === 0;
        scanned.push({
          ip,
          seatNo,
          hostname: `LAB-PC${String(idx).padStart(2, '0')}`,
          mac: `00:E0:4C:20:01:${idx.toString(16).toUpperCase().padStart(2, '0')}`,
          group: rangeGroup || 'Lab-Room-A',
          row: Math.floor(i / gridCols) + 1,
          col: (i % gridCols) + 1,
          memo: 'Range Scan',
          status: isOff ? 'offline' : 'online',
          latencyMs: isOff ? undefined : 2 + (idx % 6),
          rulesCount: isOff ? 0 : 1,
          lastAck: isOff ? 'Offline' : 'Scanned',
        });
      }
      setDevices(scanned);
      setSelectedIps(scanned.map(d => d.ip));
      setFailedIps([]);
      setGroupFilter('ALL');
      setShowRangeScanner(false);
      onPlaySound?.('actionSuccess');
      appendLog(L(`🌐 IP 대역 스캔 완료: ${rangeStartIp}~${rangeEndIp} (${scanned.length}대 좌석 매핑)`, `🌐 Scanned ${scanned.length} seats (${rangeStartIp}–${rangeEndIp}).`));
      onToast?.(L(`🌐 ${scanned.length}대 좌석 대역 등록 완료`, `🌐 Registered ${scanned.length} lab seats.`), 'success');
    } catch (err) {
      onToast?.(String(err instanceof Error ? err.message : err), 'error');
    }
  };

  // CSV Export & Import
  const handleExportCsv = () => {
    const header = 'seat_no,ip,mac,hostname,group,row,col,memo';
    const body = devices
      .map(d => `${d.seatNo},${d.ip},${d.mac},${d.hostname},${d.group},${d.row},${d.col},${d.memo || ''}`)
      .join('\n');
    const blob = new Blob([`\uFEFF${header}\n${body}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'powercontroller_lab_roster_50.csv';
    a.click();
    URL.revokeObjectURL(url);
    onPlaySound?.('actionSuccess');
    appendLog(L(`📤 CSV 내보내기 완료 (${devices.length}대)`, `📤 Exported CSV (${devices.length} seats).`));
  };

  const handleImportCsvFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      const parsed = parseCsvRoster(text);
      if (parsed.length === 0) {
        onToast?.(L('⚠️ CSV에서 유효한 IP 행을 찾지 못했습니다.', '⚠️ No valid IP rows found in CSV.'), 'error');
        return;
      }
      setDevices(parsed);
      setSelectedIps(parsed.map(p => p.ip));
      setFailedIps([]);
      onPlaySound?.('actionSuccess');
      appendLog(L(`📥 CSV 좌석 대장 불러오기 완료 (${parsed.length}대)`, `📥 Imported ${parsed.length} seats from CSV.`));
      onToast?.(L(`📥 ${parsed.length}대 PC CSV 등록 완료`, `📥 Imported ${parsed.length} lab PCs.`), 'success');
    };
    reader.readAsText(file, 'utf-8');
    e.target.value = '';
  };

  const toggleSelectIp = (ip: string) => {
    onPlaySound?.('buttonClick');
    setSelectedIps(prev => (prev.includes(ip) ? prev.filter(x => x !== ip) : [...prev, ip]));
  };

  const panelSurface = isLight
    ? theme === 'beige'
      ? 'bg-[#e6d8c3] border-[#cbb89d] text-[#2c2217]'
      : 'bg-slate-50 border-slate-200 text-slate-900'
    : 'bg-slate-900/70 border-slate-700/70 text-slate-100';

  const cardSurface = isLight
    ? theme === 'beige'
      ? 'bg-[#efe4d4] border-[#cbb89d]'
      : 'bg-white border-slate-200'
    : 'bg-slate-950/75 border-slate-800';

  const inputSurface = isLight
    ? theme === 'beige'
      ? 'bg-[#f8f1e6] border-[#c2aa8b] text-[#2c2217]'
      : 'bg-white border-slate-300 text-slate-900'
    : 'bg-slate-950 border-slate-700 text-slate-100';

  const subText = isLight ? (theme === 'beige' ? 'text-[#6c5942]' : 'text-slate-600') : 'text-slate-400';

  const activeProfile = LAB_SCHEDULE_PROFILES.find(p => p.id === selectedProfileId) || LAB_SCHEDULE_PROFILES[0];

  return (
    <div className="space-y-3 text-xs">
      <input ref={fileInputRef} type="file" accept=".csv" onChange={handleImportCsvFile} className="hidden" />

      {/* Top KPI & Onboarding Action Strip */}
      <div className={`border rounded-lg p-3 space-y-2.5 ${panelSurface}`}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="font-bold text-sm flex items-center gap-2">
              <Monitor className="w-4 h-4 text-blue-500" />
              <span>{L('50대 컴퓨터실 원격 통합 관제 타워', '50-PC Computer Lab Control Tower')}</span>
            </div>
            <div className={`text-[11px] font-mono tabular-nums mt-0.5 ${subText}`}>
              {L(
                `전체 ${kpis.total}대 · 온라인 ${kpis.online}대 · 오프라인 ${kpis.offline}대 · 실패 ${kpis.failed}대 · 선택 ${kpis.selected}대`,
                `Total ${kpis.total} · Online ${kpis.online} · Offline ${kpis.offline} · Failed ${kpis.failed} · Selected ${kpis.selected}`
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={() => {
                const preset50 = generate50LabPreset('192.168.10.', 101, gridCols);
                setDevices(preset50);
                setSelectedIps(preset50.map(d => d.ip));
                setFailedIps([]);
                setGroupFilter('ALL');
                onPlaySound?.('actionSuccess');
                appendLog(L('🏫 컴퓨터실 50대 표준 좌석셋 (192.168.10.101~150) 로드됨', '🏫 Loaded 50-PC standard lab roster (.101–.150).'));
              }}
              className="px-2.5 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-bold text-[11px] cursor-pointer whitespace-nowrap"
            >
              {L('🏫 50대 실습실 로드', '🏫 Load 50-PC Lab')}
            </button>
            <button
              type="button"
              onClick={() => setShowRangeScanner(v => !v)}
              className={`px-2.5 py-1.5 rounded border font-semibold text-[11px] flex items-center gap-1 cursor-pointer whitespace-nowrap ${inputSurface}`}
            >
              <Globe className="w-3.5 h-3.5 text-teal-500" />
              <span>{L('IP 대역 스캔', 'IP Range')}</span>
            </button>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className={`px-2.5 py-1.5 rounded border font-semibold text-[11px] flex items-center gap-1 cursor-pointer whitespace-nowrap ${inputSurface}`}
            >
              <Upload className="w-3.5 h-3.5 text-indigo-500" />
              <span>{L('CSV 등록', 'CSV Import')}</span>
            </button>
            <button
              type="button"
              onClick={handleExportCsv}
              className={`px-2.5 py-1.5 rounded border font-semibold text-[11px] flex items-center gap-1 cursor-pointer whitespace-nowrap ${inputSurface}`}
            >
              <Download className="w-3.5 h-3.5 text-emerald-500" />
              <span>{L('CSV 저장', 'CSV Export')}</span>
            </button>
          </div>
        </div>

        {/* Collapsible IP Range Scanner Drawer */}
        {showRangeScanner && (
          <div className={`border rounded-md p-2.5 grid grid-cols-1 sm:grid-cols-5 gap-2 items-end ${cardSurface}`}>
            <div>
              <label className={`block text-[10px] font-semibold mb-1 ${subText}`}>{L('시작 IP', 'Start IP')}</label>
              <input
                type="text"
                value={rangeStartIp}
                onChange={e => setRangeStartIp(e.target.value)}
                className={`w-full border rounded px-2 py-1 font-mono text-[11px] ${inputSurface}`}
              />
            </div>
            <div>
              <label className={`block text-[10px] font-semibold mb-1 ${subText}`}>{L('종료 IP', 'End IP')}</label>
              <input
                type="text"
                value={rangeEndIp}
                onChange={e => setRangeEndIp(e.target.value)}
                className={`w-full border rounded px-2 py-1 font-mono text-[11px] ${inputSurface}`}
              />
            </div>
            <div>
              <label className={`block text-[10px] font-semibold mb-1 ${subText}`}>{L('좌석 접두어', 'Seat Prefix')}</label>
              <input
                type="text"
                value={rangeSeatPrefix}
                onChange={e => setRangeSeatPrefix(e.target.value)}
                className={`w-full border rounded px-2 py-1 font-mono text-[11px] ${inputSurface}`}
              />
            </div>
            <div>
              <label className={`block text-[10px] font-semibold mb-1 ${subText}`}>{L('소속 그룹명', 'Group Name')}</label>
              <input
                type="text"
                value={rangeGroup}
                onChange={e => setRangeGroup(e.target.value)}
                className={`w-full border rounded px-2 py-1 text-[11px] ${inputSurface}`}
              />
            </div>
            <button
              type="button"
              onClick={handleRunRangeScan}
              className="py-1.5 px-3 bg-teal-600 hover:bg-teal-500 text-white rounded font-bold text-[11px] cursor-pointer whitespace-nowrap"
            >
              {L('🔍 대역 일괄 생성/스캔', '🔍 Scan & Map')}
            </button>
          </div>
        )}

        {/* Filter, Search, Layout View Switch, Cols & Auto-Poll */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-gray-500/15">
          <div className="relative flex-1 min-w-[150px]">
            <Search className={`w-3.5 h-3.5 absolute left-2 top-1/2 -translate-y-1/2 ${subText}`} />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder={L('좌석번호 / IP / 호스트명 검색...', 'Search Seat# / IP / Host...')}
              className={`w-full border rounded pl-7 pr-2 py-1 text-[11px] font-mono ${inputSurface}`}
            />
          </div>

          <select
            value={groupFilter}
            onChange={e => setGroupFilter(e.target.value)}
            className={`border rounded px-2 py-1 text-[11px] font-semibold cursor-pointer ${inputSurface}`}
          >
            {groups.map(g => (
              <option key={g} value={g}>
                {g === 'ALL' ? L('📁 전체 그룹', '📁 All Groups') : g}
              </option>
            ))}
          </select>

          <div className={`flex items-center border rounded p-0.5 ${cardSurface}`}>
            {(['all', 'online', 'offline', 'failed'] as const).map(st => (
              <button
                key={st}
                type="button"
                onClick={() => setStatusFilter(st)}
                className={`px-2 py-0.5 rounded text-[10px] font-bold cursor-pointer transition-colors ${
                  statusFilter === st
                    ? st === 'failed'
                      ? 'bg-red-600 text-white'
                      : st === 'online'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-blue-600 text-white'
                    : subText
                }`}
              >
                {st === 'all' && L('전체', 'All')}
                {st === 'online' && L('온라인', 'Online')}
                {st === 'offline' && L('오프라인', 'Offline')}
                {st === 'failed' && L('실패', 'Failed')}
              </button>
            ))}
          </div>

          {/* Seat Grid <-> Table View Switch */}
          <div className={`flex items-center border rounded p-0.5 ${cardSurface}`}>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 cursor-pointer ${
                viewMode === 'grid' ? 'bg-blue-600 text-white' : subText
              }`}
            >
              <Grid className="w-3 h-3" />
              <span>{L('좌석 그리드', 'Seat Grid')}</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('table')}
              className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 cursor-pointer ${
                viewMode === 'table' ? 'bg-blue-600 text-white' : subText
              }`}
            >
              <List className="w-3 h-3" />
              <span>{L('상세 목록', 'Table')}</span>
            </button>
          </div>

          {viewMode === 'grid' && (
            <select
              value={gridCols}
              onChange={e => setGridCols(Number(e.target.value) as 5 | 8 | 10)}
              className={`border rounded px-1.5 py-1 text-[11px] font-mono cursor-pointer ${inputSurface}`}
              title={L('좌석 배치 열 수', 'Seat Map Columns')}
            >
              <option value={5}>5 {L('열', 'cols')}</option>
              <option value={8}>8 {L('열', 'cols')}</option>
              <option value={10}>10 {L('열', 'cols')}</option>
            </select>
          )}

          <label className="flex items-center gap-1 text-[11px] font-semibold cursor-pointer select-none">
            <input
              type="checkbox"
              checked={autoPoll}
              onChange={e => setAutoPoll(e.target.checked)}
              className="rounded border-gray-500 text-emerald-500 focus:ring-0"
            />
            <span className={autoPoll ? 'text-emerald-500 font-bold' : subText}>
              {L('15초 폴링', '15s Poll')}
            </span>
          </label>
        </div>

        {/* Quick Select & Poll & Staggered WOL Bar */}
        <div className="flex flex-wrap items-center justify-between gap-1.5">
          <div className="flex flex-wrap items-center gap-1">
            <button
              type="button"
              onClick={() => {
                setSelectedIps(filteredDevices.map(d => d.ip));
                onPlaySound?.('buttonClick');
              }}
              className={`px-2 py-1 border rounded text-[10px] font-bold flex items-center gap-1 cursor-pointer ${inputSurface}`}
            >
              <CheckSquare className="w-3 h-3 text-blue-500" />
              <span>{L('표시 전체', 'All Visible')}</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedIps([]);
                onPlaySound?.('buttonClick');
              }}
              className={`px-2 py-1 border rounded text-[10px] font-semibold flex items-center gap-1 cursor-pointer ${inputSurface}`}
            >
              <Square className="w-3 h-3" />
              <span>{L('해제', 'Clear')}</span>
            </button>
            <button
              type="button"
              onClick={() => setSelectedIps(filteredDevices.filter(d => d.status === 'online').map(d => d.ip))}
              className="px-2 py-1 rounded bg-emerald-600/20 border border-emerald-500/40 text-emerald-500 font-bold text-[10px] cursor-pointer"
            >
              {L('온라인만', 'Online Only')}
            </button>
            <button
              type="button"
              onClick={() => setSelectedIps(filteredDevices.filter(d => d.status === 'offline').map(d => d.ip))}
              className="px-2 py-1 rounded bg-indigo-600/20 border border-indigo-500/40 text-indigo-400 font-bold text-[10px] cursor-pointer"
            >
              {L('오프라인(WOL)', 'Offline (WOL)')}
            </button>
            {failedIps.length > 0 && (
              <button
                type="button"
                onClick={() => setSelectedIps(failedIps)}
                className="px-2 py-1 rounded bg-red-600/20 border border-red-500/40 text-red-400 font-bold text-[10px] cursor-pointer"
              >
                {L(`실패만 (${failedIps.length})`, `Failed (${failedIps.length})`)}
              </button>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={batchRunning}
              onClick={() => runBatchOnTargets('Poll Status', filteredDevices.map(d => d.ip), { kind: 'poll' })}
              className="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white rounded font-bold text-[10px] flex items-center gap-1 cursor-pointer"
            >
              <RefreshCw className={`w-3 h-3 ${batchRunning ? 'animate-spin' : ''}`} />
              <span>{L('상태 일괄 폴링', 'Poll All')}</span>
            </button>

            <select
              value={wolStepMs}
              onChange={e => setWolStepMs(Number(e.target.value))}
              className={`border rounded px-1.5 py-1 text-[10px] font-mono cursor-pointer ${inputSurface}`}
              title={L('순차 WOL 간격(돌입전류 방지)', 'Staggered WOL step delay')}
            >
              <option value={100}>100ms</option>
              <option value={250}>250ms</option>
              <option value={500}>500ms</option>
              <option value={1000}>1000ms</option>
            </select>

            <button
              type="button"
              disabled={batchRunning}
              onClick={runStaggeredWol}
              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded font-bold text-[10px] flex items-center gap-1 cursor-pointer whitespace-nowrap"
            >
              <Zap className="w-3 h-3" />
              <span>{L('순차 WOL 기상', 'Staggered WOL')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Fleet View: Visual Seat Map Grid OR Detailed Table */}
      <div className={`border rounded-lg p-2.5 ${panelSurface}`}>
        {filteredDevices.length === 0 ? (
          <div className={`text-center py-8 text-xs ${subText}`}>
            {L('조건에 맞는 컴퓨터실 장비가 없습니다. 필터를 변경하거나 [50대 실습실 로드]를 클릭하세요.', 'No devices match filter. Adjust filters or load 50-PC lab preset.')}
          </div>
        ) : viewMode === 'grid' ? (
          <div
            className="grid gap-1.5 max-h-[300px] overflow-y-auto pr-1 [scrollbar-width:thin]"
            style={{ gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))` }}
          >
            {filteredDevices.map(pc => {
              const isSelected = selectedIps.includes(pc.ip);
              const shortIp = `.${pc.ip.split('.').slice(-1)[0]}`;
              const tileStyle = isSelected
                ? isLight
                  ? 'bg-blue-50 border-blue-500 ring-1 ring-blue-500'
                  : 'bg-blue-950/60 border-blue-400 ring-1 ring-blue-400'
                : pc.status === 'failed'
                ? isLight
                  ? 'bg-red-50 border-red-400'
                  : 'bg-red-950/40 border-red-500/70'
                : pc.status === 'online'
                ? isLight
                  ? 'bg-white border-emerald-400/70 hover:border-emerald-500'
                  : 'bg-slate-900/90 border-emerald-500/40 hover:border-emerald-400'
                : isLight
                ? 'bg-slate-100 border-slate-300 opacity-85'
                : 'bg-slate-950/60 border-slate-800 opacity-75';

              return (
                <button
                  key={pc.ip}
                  type="button"
                  onClick={() => toggleSelectIp(pc.ip)}
                  title={`${pc.seatNo} · ${pc.ip} · ${pc.hostname} · MAC: ${pc.mac} · ${pc.lastAck || ''}`}
                  className={`text-left border rounded p-1.5 transition-all cursor-pointer select-none flex flex-col justify-between gap-0.5 ${tileStyle}`}
                >
                  <div className="flex items-center justify-between gap-1 w-full">
                    <span className="font-mono tabular-nums font-bold text-[10px] truncate">
                      {pc.seatNo.replace('LAB-', '#')}
                      {pc.isSelf ? ' 👑' : ''}
                    </span>
                    <span
                      className={`font-mono text-[9px] font-bold ${
                        pc.status === 'online'
                          ? 'text-emerald-500'
                          : pc.status === 'failed'
                          ? 'text-red-500'
                          : subText
                      }`}
                    >
                      {pc.status === 'online' ? 'ON' : pc.status === 'failed' ? 'ERR' : 'OFF'}
                    </span>
                  </div>
                  <div className="font-mono tabular-nums text-[10px] font-semibold truncate text-blue-500">
                    {shortIp}
                  </div>
                  <div className={`text-[9px] font-mono tabular-nums truncate ${subText}`}>
                    {pc.timerRunning && pc.remainingSeconds
                      ? `⏱ ${formatTimerShort(pc.remainingSeconds)}`
                      : `R:${pc.rulesCount} · ${pc.latencyMs ? `${pc.latencyMs}ms` : '-'}`}
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="max-h-[300px] overflow-auto [scrollbar-width:thin]">
            <table className="w-full text-left border-collapse font-mono tabular-nums text-[11px]">
              <thead className={`sticky top-0 z-10 border-b ${cardSurface}`}>
                <tr>
                  <th className="py-1.5 px-2 w-7">✓</th>
                  <th className="py-1.5 px-2 cursor-pointer" onClick={() => { setSortBy('seatNo'); setSortDesc(s => !s); }}>
                    {L('좌석', 'Seat')}
                  </th>
                  <th className="py-1.5 px-2 cursor-pointer" onClick={() => { setSortBy('ip'); setSortDesc(s => !s); }}>
                    IP
                  </th>
                  <th className="py-1.5 px-2">{L('호스트명', 'Host')}</th>
                  <th className="py-1.5 px-2">MAC (WOL)</th>
                  <th className="py-1.5 px-2 cursor-pointer" onClick={() => { setSortBy('status'); setSortDesc(s => !s); }}>
                    {L('상태', 'Status')}
                  </th>
                  <th className="py-1.5 px-2">{L('타이머', 'Timer')}</th>
                  <th className="py-1.5 px-2 cursor-pointer" onClick={() => { setSortBy('rulesCount'); setSortDesc(s => !s); }}>
                    {L('규칙', 'Rules')}
                  </th>
                  <th className="py-1.5 px-2">{L('응답', 'ACK')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-500/10">
                {filteredDevices.map(pc => {
                  const isSelected = selectedIps.includes(pc.ip);
                  return (
                    <tr
                      key={pc.ip}
                      onClick={() => toggleSelectIp(pc.ip)}
                      className={`cursor-pointer transition-colors ${
                        isSelected
                          ? isLight
                            ? 'bg-blue-50 font-semibold'
                            : 'bg-blue-600/20 font-semibold'
                          : isLight
                          ? 'hover:bg-slate-100'
                          : 'hover:bg-slate-800/50'
                      }`}
                    >
                      <td className="py-1 px-2">
                        <input type="checkbox" checked={isSelected} onChange={() => {}} className="rounded cursor-pointer" />
                      </td>
                      <td className="py-1 px-2 font-bold">{pc.seatNo}{pc.isSelf ? ' 👑' : ''}</td>
                      <td className="py-1 px-2 text-blue-500">{pc.ip}</td>
                      <td className="py-1 px-2 font-sans">{pc.hostname}</td>
                      <td className={`py-1 px-2 ${subText}`}>{pc.mac}</td>
                      <td className="py-1 px-2 font-sans font-bold">
                        <span
                          className={
                            pc.status === 'online'
                              ? 'text-emerald-500'
                              : pc.status === 'failed'
                              ? 'text-red-500'
                              : subText
                          }
                        >
                          {pc.status === 'online'
                            ? L('🟢 온라인', '🟢 Online')
                            : pc.status === 'failed'
                            ? L('🔴 실패', '🔴 Failed')
                            : L('⚪ 오프라인', '⚪ Offline')}
                        </span>
                      </td>
                      <td className="py-1 px-2 text-amber-500">{pc.timerRunning ? formatTimerShort(pc.remainingSeconds) : '-'}</td>
                      <td className="py-1 px-2">{pc.rulesCount}</td>
                      <td className={`py-1 px-2 font-sans truncate max-w-[120px] ${pc.status === 'failed' ? 'text-red-400' : subText}`}>
                        {pc.lastError || pc.lastAck || '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Batch Progress Bar & One-Click Retry Failed (N) */}
      <div className={`border rounded-lg p-2.5 space-y-1.5 ${panelSurface}`}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="font-mono tabular-nums text-[11px] font-bold">
            {batchProgress.total > 0
              ? `${batchProgress.label}: ${batchProgress.done}/${batchProgress.total} · OK ${batchProgress.ok} · Fail ${batchProgress.fail}`
              : L(`대기 중 · 선택 ${selectedIps.length}대 준비됨`, `Idle · ${selectedIps.length} target(s) armed`)}
          </div>
          <div className="flex items-center gap-1.5">
            {failedIps.length > 0 && lastBatchAction && (
              <button
                type="button"
                disabled={batchRunning}
                onClick={() =>
                  runBatchOnTargets(`Retry ${lastBatchAction.label}`, failedIps, {
                    ...lastBatchAction,
                    isRetry: true,
                  })
                }
                className="px-2.5 py-1 bg-red-600 hover:bg-red-500 text-white rounded font-bold text-[11px] flex items-center gap-1 cursor-pointer shadow"
              >
                <RotateCcw className="w-3 h-3" />
                <span>{L(`실패 PC 재시도 (${failedIps.length})`, `Retry Failed (${failedIps.length})`)}</span>
              </button>
            )}
          </div>
        </div>
        <div className={`w-full h-2 rounded-full overflow-hidden ${isLight ? 'bg-slate-200' : 'bg-slate-800'}`}>
          <div
            className={`h-full transition-all duration-200 ${
              batchProgress.fail > 0 ? 'bg-amber-500' : 'bg-emerald-500'
            }`}
            style={{
              width: batchProgress.total > 0 ? `${Math.round((batchProgress.done / batchProgress.total) * 100)}%` : '0%',
            }}
          />
        </div>
      </div>

      {/* Immediate Batch Power Actions + Class-Period Schedule Profile Deployment */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Immediate Remote Power Actions */}
        <div className={`border rounded-lg p-3 space-y-2 ${panelSurface}`}>
          <div className="flex items-center justify-between font-bold">
            <span>{L(`⚡ 선택 PC (${selectedIps.length}대) 즉시 병렬 제어`, `⚡ Immediate Parallel Actions (${selectedIps.length})`)}</span>
            <span className="font-mono text-[10px] text-emerald-500">TCP 9988</span>
          </div>
          <div className="grid grid-cols-5 gap-1.5">
            <button
              type="button"
              disabled={batchRunning}
              onClick={() => runBatchOnTargets(L('즉시 종료', 'Shutdown'), selectedIps, { kind: 'power', cmd: 'shutdown' })}
              className="py-1.5 px-1.5 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white rounded font-bold text-[11px] flex items-center justify-center gap-1 cursor-pointer whitespace-nowrap"
            >
              <Power className="w-3 h-3" />
              <span>{L('종료', 'Shut')}</span>
            </button>
            <button
              type="button"
              disabled={batchRunning}
              onClick={() => runBatchOnTargets(L('즉시 재시작', 'Reboot'), selectedIps, { kind: 'power', cmd: 'reboot' })}
              className="py-1.5 px-1.5 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white rounded font-bold text-[11px] flex items-center justify-center gap-1 cursor-pointer whitespace-nowrap"
            >
              <RotateCw className="w-3 h-3" />
              <span>{L('재시작', 'Reboot')}</span>
            </button>
            <button
              type="button"
              disabled={batchRunning}
              onClick={() => runBatchOnTargets(L('절전', 'Sleep'), selectedIps, { kind: 'power', cmd: 'sleep' })}
              className="py-1.5 px-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded font-bold text-[11px] flex items-center justify-center gap-1 cursor-pointer whitespace-nowrap"
            >
              <Moon className="w-3 h-3" />
              <span>{L('절전', 'Sleep')}</span>
            </button>
            <button
              type="button"
              disabled={batchRunning}
              onClick={() => runBatchOnTargets(L('화면끔', 'ScreenOff'), selectedIps, { kind: 'power', cmd: 'screenoff' })}
              className="py-1.5 px-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white rounded font-bold text-[11px] flex items-center justify-center gap-1 cursor-pointer whitespace-nowrap"
            >
              <Monitor className="w-3 h-3" />
              <span>{L('화면끔', 'Screen')}</span>
            </button>
            <button
              type="button"
              disabled={batchRunning}
              onClick={() => runBatchOnTargets(L('비상 알람', 'Alarm'), selectedIps, { kind: 'power', cmd: 'alarm' })}
              className="py-1.5 px-1.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded font-bold text-[11px] flex items-center justify-center gap-1 cursor-pointer whitespace-nowrap"
            >
              <Bell className="w-3 h-3" />
              <span>{L('알람', 'Alarm')}</span>
            </button>
          </div>
        </div>

        {/* Class-Period / Lab Schedule Profile Bundle Push */}
        <div className={`border rounded-lg p-3 space-y-2 ${panelSurface}`}>
          <div className="flex items-center justify-between font-bold">
            <span className="flex items-center gap-1.5">
              <FileSpreadsheet className="w-3.5 h-3.5 text-teal-500" />
              <span>{L('교시·일과별 프로필 일괄 배포', 'Class-Period Lab Profile Bundle')}</span>
            </span>
            <span className={`text-[10px] font-mono ${subText}`}>{activeProfile.rulesCount} rules</span>
          </div>
          <div className="flex items-center gap-1.5">
            <select
              value={selectedProfileId}
              onChange={e => setSelectedProfileId(e.target.value)}
              className={`flex-1 min-w-0 border rounded px-2 py-1.5 text-[11px] font-semibold cursor-pointer ${inputSurface}`}
            >
              {LAB_SCHEDULE_PROFILES.map(p => (
                <option key={p.id} value={p.id}>
                  {isEn ? p.nameEn : p.nameKo}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={batchRunning}
              onClick={() =>
                runBatchOnTargets(
                  isEn ? `Profile (${activeProfile.rulesCount}R)` : `프로필 (${activeProfile.rulesCount}종)`,
                  selectedIps,
                  { kind: 'profile', rulesAdded: activeProfile.rulesCount }
                )
              }
              className="px-3 py-1.5 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white rounded font-bold text-[11px] flex items-center gap-1 cursor-pointer whitespace-nowrap shrink-0"
            >
              <Send className="w-3 h-3" />
              <span>{L('일괄 배포', 'Deploy')}</span>
            </button>
          </div>
          <div className={`text-[10px] ${subText}`}>
            {activeProfile.summaryRules.map(r => `${r.time} ${isEn ? r.labelEn : r.labelKo}`).join(' · ')}
          </div>
        </div>
      </div>

      {/* Live Remote Execution Console */}
      <div className={`border rounded-lg p-2 font-mono text-[10px] space-y-1 max-h-24 overflow-y-auto ${cardSurface}`}>
        <div className={`font-bold flex items-center justify-between pb-1 border-b border-gray-500/15 ${subText}`}>
          <span>{L('📋 50대 병렬 전송 · TCP 9988 ACK 실시간 콘솔', '📋 Parallel Dispatch · TCP 9988 ACK Console')}</span>
          <button
            type="button"
            onClick={() => setConsoleLogs([])}
            className="hover:underline cursor-pointer"
          >
            {L('비우기', 'Clear')}
          </button>
        </div>
        {consoleLogs.length === 0 ? (
          <div className={subText}>{L('--- 콘솔 로그 없음 ---', '--- Console empty ---')}</div>
        ) : (
          consoleLogs.map((l, idx) => (
            <div key={idx} className="truncate text-emerald-500">
              {l}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
