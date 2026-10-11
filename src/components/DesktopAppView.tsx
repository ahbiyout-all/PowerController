import React, { useState, useEffect, useRef } from 'react';
import {
  Power,
  RotateCw,
  Moon,
  Monitor,
  LogOut,
  Bell,
  Play,
  RotateCcw,
  Square,
  Settings,
  Calendar,
  Clock,
  FileText,
  Trash2,
  Plus,
  ShieldCheck,
  Cpu,
  Wifi,
  HardDrive,
  CheckCircle,
  AlertTriangle,
  Lock,
  BatteryCharging,
  Battery,
  BatteryFull,
  BatteryMedium,
  BatteryLow,
  Zap,
  Maximize2,
  Minimize2,
  X,
  ExternalLink,
  ChevronUp,
  ChevronDown,
  Sparkles,
  Download,
  Volume2,
  VolumeX,
  Volume1,
  Check
} from 'lucide-react';
import { APP_VERSION, SoundTheme } from '../types';
import { soundEngine, SOUND_THEMES } from '../utils/soundEngine';
import { UpdateModal } from './GitHubUpdateBanner';
import BatteryHistoryChart from './BatteryHistoryChart';

export type DesktopWindowType = 'main' | 'network' | 'injector';

interface DesktopAppViewProps {
  onSwitchToWeb?: () => void;
  onOpenLicense?: () => void;
  isWebAvailable?: boolean;
  battery?: {
    level: number;
    charging: boolean;
    statusText?: string;
  };
  isPowerSavingActive?: boolean;
  soundTheme?: SoundTheme;
  onSoundThemeChange?: (theme: SoundTheme) => void;
  soundVolume?: number;
  onSoundVolumeChange?: (volume: number) => void;
  hourlyChime?: boolean;
  onHourlyChimeChange?: (enabled: boolean) => void;
  soundFeedbackEnabled?: boolean;
  onSoundFeedbackChange?: (enabled: boolean) => void;
}

interface ScheduleRuleItem {
  id: string;
  name: string;
  mode: 'shutdown' | 'restart' | 'sleep' | 'screenoff' | 'logout' | 'alarm';
  time: string;
  days: string[];
  enabled: boolean;
  forceClose: boolean;
}

export const DesktopAppView: React.FC<DesktopAppViewProps> = ({
  onSwitchToWeb,
  onOpenLicense,
  isWebAvailable = true,
  battery,
  isPowerSavingActive = false,
  soundTheme: propSoundTheme,
  onSoundThemeChange,
  soundVolume: propSoundVolume,
  onSoundVolumeChange,
  hourlyChime: propHourlyChime,
  onHourlyChimeChange,
  soundFeedbackEnabled: propSoundFeedbackEnabled,
  onSoundFeedbackChange
}) => {
  // Active desktop program
  const [activeApp, setActiveApp] = useState<DesktopWindowType>('main');

  // Window frame states
  const [isWindowMaximized, setIsWindowMaximized] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  // Main PowerController.exe states
  const [activeTab, setActiveTab] = useState<'control' | 'scheduler' | 'history'>('control');
  const [powerMode, setPowerMode] = useState<'shutdown' | 'restart' | 'sleep' | 'screenoff' | 'logout' | 'alarm'>('shutdown');
  const [runType, setRunType] = useState<'timer' | 'schedule'>('timer');
  
  // Timer spinbox inputs
  const [inputH, setInputH] = useState(0);
  const [inputM, setInputM] = useState(30);
  const [inputS, setInputS] = useState(0);

  // Timer run countdown
  const [remainingSeconds, setRemainingSeconds] = useState(30 * 60);
  const [isTimerRunning, setIsTimerRunning] = useState(false);

  // 2-column checkboxes
  const [isPinned, setIsPinned] = useState(false);
  const [autoStart, setAutoStart] = useState(true);
  const [bootToTray, setBootToTray] = useState(false);
  const [minimizeToTray, setMinimizeToTray] = useState(true);
  const [forceClose, setForceClose] = useState(true);
  const [networkReceive, setNetworkReceive] = useState(true);
  const [powerSavingToggle, setPowerSavingToggle] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('power_saving_mode');
      return saved !== null ? saved === 'true' : true;
    } catch {
      return true;
    }
  });

  // Idle Auto-Lock Desktop state & refs
  const [idleLockEnabled, setIdleLockEnabled] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('power_idle_lock_enabled');
      return saved !== null ? saved === 'true' : false;
    } catch {
      return false;
    }
  });

  const [idleLockMinutes, setIdleLockMinutes] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('power_idle_lock_minutes');
      return saved ? parseInt(saved, 10) : 5;
    } catch {
      return 5;
    }
  });

  const [isDesktopLocked, setIsDesktopLocked] = useState<boolean>(false);
  const lastUserActivityRef = useRef<number>(Date.now());

  // Settings popup inside desktop
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showSchedulerPopup, setShowSchedulerPopup] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showToast, setShowToast] = useState<string | null>(null);

  // Sound Engine States & Integration
  const [currentSoundTheme, setCurrentSoundTheme] = useState<SoundTheme>(() => {
    if (propSoundTheme) return propSoundTheme;
    try {
      const saved = localStorage.getItem('power_sound_theme');
      return (saved as SoundTheme) || 'classic';
    } catch {
      return 'classic';
    }
  });

  const [currentSoundVolume, setCurrentSoundVolume] = useState<number>(() => {
    if (propSoundVolume !== undefined) return propSoundVolume;
    return soundEngine.getVolume();
  });

  const [currentHourlyChime, setCurrentHourlyChime] = useState<boolean>(() => {
    if (propHourlyChime !== undefined) return propHourlyChime;
    try {
      const saved = localStorage.getItem('power_hourly_chime');
      return saved !== null ? saved === 'true' : true;
    } catch {
      return true;
    }
  });

  const [soundFeedbackEnabled, setSoundFeedbackEnabled] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('power_sound_feedback');
      return saved !== null ? saved === 'true' : true;
    } catch {
      return true;
    }
  });

  // Pull-down selection state for sound audition test
  const [selectedSoundTestTrigger, setSelectedSoundTestTrigger] = useState<
    'preview' | 'warningTick' | 'hourlyChime' | 'timerAlarm' | 'actionSuccess'
  >('preview');

  // Power Mode UI Display format: 'dropdown' (clean, compact) vs 'grid' (expanded buttons)
  const [powerModeDisplayMode, setPowerModeDisplayMode] = useState<'dropdown' | 'grid'>(() => {
    try {
      const saved = localStorage.getItem('desktop_power_mode_display');
      return (saved as 'dropdown' | 'grid') || 'dropdown';
    } catch {
      return 'dropdown';
    }
  });

  // Window 2 Remote Action Pulldown selection
  const [selectedRemoteAction, setSelectedRemoteAction] = useState<string>('shutdown');

  // Sync with prop changes if passed from App.tsx
  useEffect(() => {
    if (propSoundTheme && propSoundTheme !== currentSoundTheme) {
      setCurrentSoundTheme(propSoundTheme);
    }
  }, [propSoundTheme]);

  useEffect(() => {
    if (propSoundVolume !== undefined && propSoundVolume !== currentSoundVolume) {
      setCurrentSoundVolume(propSoundVolume);
      soundEngine.setVolume(propSoundVolume);
    }
  }, [propSoundVolume]);

  useEffect(() => {
    if (propHourlyChime !== undefined && propHourlyChime !== currentHourlyChime) {
      setCurrentHourlyChime(propHourlyChime);
    }
  }, [propHourlyChime]);

  useEffect(() => {
    if (propSoundFeedbackEnabled !== undefined && propSoundFeedbackEnabled !== soundFeedbackEnabled) {
      setSoundFeedbackEnabled(propSoundFeedbackEnabled);
    }
  }, [propSoundFeedbackEnabled]);

  // AudioContext unlock on first user gesture (mouse click or key down)
  useEffect(() => {
    const handleGesture = () => {
      soundEngine.unlock();
    };
    window.addEventListener('click', handleGesture, { once: true });
    window.addEventListener('keydown', handleGesture, { once: true });
    return () => {
      window.removeEventListener('click', handleGesture);
      window.removeEventListener('keydown', handleGesture);
    };
  }, []);

  // Hourly Chime Effect in Desktop App
  useEffect(() => {
    if (!currentHourlyChime) return;
    const interval = setInterval(() => {
      const now = new Date();
      if (now.getMinutes() === 0 && now.getSeconds() === 0) {
        soundEngine.play(currentSoundTheme, 'hourlyChime');
        showInAppToast(`🔔 정각 알림 (${now.getHours()}시 정각)`);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [currentHourlyChime, currentSoundTheme]);

  // System Idle Auto-Lock in Desktop App View
  useEffect(() => {
    const handleUserActivity = () => {
      lastUserActivityRef.current = Date.now();
    };

    window.addEventListener('mousemove', handleUserActivity);
    window.addEventListener('mousedown', handleUserActivity);
    window.addEventListener('keydown', handleUserActivity);
    window.addEventListener('touchstart', handleUserActivity);
    window.addEventListener('scroll', handleUserActivity);

    const idleInterval = setInterval(() => {
      if (!idleLockEnabled || !isTimerRunning || isDesktopLocked) return;
      const elapsed = Date.now() - lastUserActivityRef.current;
      const threshold = idleLockMinutes * 60 * 1000;
      if (elapsed >= threshold) {
        setIsDesktopLocked(true);
        soundEngine.play(currentSoundTheme, 'warningTick');
        showInAppToast(`🔒 유휴 상태 감지(${idleLockMinutes}분): 데스크톱 세션을 안전하게 잠갔습니다.`);
      }
    }, 1000);

    return () => {
      window.removeEventListener('mousemove', handleUserActivity);
      window.removeEventListener('mousedown', handleUserActivity);
      window.removeEventListener('keydown', handleUserActivity);
      window.removeEventListener('touchstart', handleUserActivity);
      window.removeEventListener('scroll', handleUserActivity);
      clearInterval(idleInterval);
    };
  }, [idleLockEnabled, idleLockMinutes, isTimerRunning, isDesktopLocked, currentSoundTheme]);

  // Keydown unlock listener in Desktop App View
  useEffect(() => {
    if (!isDesktopLocked) return;
    const handleUnlockKey = (e: KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Escape') {
        setIsDesktopLocked(false);
        lastUserActivityRef.current = Date.now();
        soundEngine.play(currentSoundTheme, 'actionSuccess');
        showInAppToast('🔓 데스크톱 세션 잠금이 정상 해제되었습니다.');
      }
    };
    window.addEventListener('keydown', handleUnlockKey);
    return () => window.removeEventListener('keydown', handleUnlockKey);
  }, [isDesktopLocked, currentSoundTheme]);

  const playSoundEffect = (
    trigger: 'buttonClick' | 'actionSuccess' | 'warningTick' | 'timerAlarm' | 'hourlyChime' | 'preview',
    overrideTheme?: SoundTheme
  ) => {
    if (!soundFeedbackEnabled && trigger === 'buttonClick') return;
    soundEngine.play(overrideTheme || currentSoundTheme, trigger);
  };

  const handleSelectSoundTheme = (themeId: SoundTheme) => {
    setCurrentSoundTheme(themeId);
    onSoundThemeChange?.(themeId);
    try {
      localStorage.setItem('power_sound_theme', themeId);
    } catch {}
    soundEngine.play(themeId, 'preview');
    const matched = SOUND_THEMES.find(t => t.id === themeId);
    showInAppToast(`[${matched?.nameKo || themeId}] 알림음 테마가 적용되었습니다.`);
  };

  const handleVolumeChange = (vol: number) => {
    const clamped = Math.min(100, Math.max(0, vol));
    setCurrentSoundVolume(clamped);
    soundEngine.setVolume(clamped);
    onSoundVolumeChange?.(clamped);
  };

  const [prevSoundVolume, setPrevSoundVolume] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('power_sound_prev_volume');
      return saved !== null ? Math.max(10, parseInt(saved, 10)) : (currentSoundVolume > 0 ? currentSoundVolume : 80);
    } catch {
      return 80;
    }
  });

  const handleToggleMuteAllDesktop = () => {
    if (currentSoundVolume > 0) {
      const volToSave = currentSoundVolume;
      setPrevSoundVolume(volToSave);
      try {
        localStorage.setItem('power_sound_prev_volume', String(volToSave));
      } catch {}
      handleVolumeChange(0);
      showInAppToast('🔇 모든 효과음 및 알림이 음소거되었습니다 (볼륨 0%).');
    } else {
      const restoreVol = prevSoundVolume > 0 ? prevSoundVolume : 80;
      handleVolumeChange(restoreVol);
      showInAppToast(`🔊 사운드 볼륨이 ${restoreVol}%로 원복되었습니다.`);
    }
  };

  const handleHourlyChimeToggle = (enabled: boolean) => {
    setCurrentHourlyChime(enabled);
    onHourlyChimeChange?.(enabled);
    try {
      localStorage.setItem('power_hourly_chime', enabled ? 'true' : 'false');
    } catch {}
    if (enabled) {
      soundEngine.play(currentSoundTheme, 'hourlyChime');
      showInAppToast('매시 정각 시계탑 차임벨이 활성화되었습니다.');
    } else {
      showInAppToast('정각 차임벨이 비활성화되었습니다.');
    }
  };

  // Schedule rules
  const [rules, setRules] = useState<ScheduleRuleItem[]>([
    { id: '1', name: '🏢 정시 퇴근 자동 종료', mode: 'shutdown', time: '18:30', days: ['월', '화', '수', '목', '금'], enabled: true, forceClose: true },
    { id: '2', name: '🌙 야간 심야 자동 종료', mode: 'shutdown', time: '23:30', days: ['매일'], enabled: true, forceClose: true },
    { id: '3', name: '☕ 점심시간 절전 모드', mode: 'sleep', time: '12:00', days: ['월', '화', '수', '목', '금'], enabled: false, forceClose: false },
    { id: '4', name: '🔄 월요일 아침 정기 리부팅', mode: 'restart', time: '08:30', days: ['월'], enabled: true, forceClose: true }
  ]);

  // New rule form
  const [newRuleName, setNewRuleName] = useState('야간 자동 종료');
  const [newRuleTime, setNewRuleTime] = useState('23:00');
  const [newRuleMode, setNewRuleMode] = useState<'shutdown' | 'restart' | 'sleep' | 'screenoff' | 'logout' | 'alarm'>('shutdown');

  // Logs
  const [logs, setLogs] = useState<string[]>([
    `[2026-09-29 19:30:00] [PowerCoreNative.dll] C 네이티브 모듈 로드 완료 (초정밀 대기 타이머 및 절전 락 가동)`,
    `[2026-09-29 19:30:00] [NetBeaconEngine.dll] Winsock2 논블로킹 UDP 비콘 리스너 시작 (포트 9986, 512 슬롯 링버퍼)`,
    `[2026-09-29 19:30:00] [FirewallNative.dll] Windows 방화벽 COM 규칙 일괄 검증 완료 (0.05초 트랜잭션)`,
    `[2026-09-29 19:30:00] [SysPowerHook.dll] Windows 세션 알림 훅 등록 완료 (화면 잠금 및 배터리 감시 활성)`,
    `[2026-09-29 19:30:00] [ScheduleCrypto.dll] HMAC-SHA256 디지털 서명 및 암호화 봉투 엔진 준비 완료`,
    `[2026-09-29 19:30:00] 네트워크 수신 서버 시작: 포트 9988에서 원격 스케줄 규칙 대기 중...`,
    `[2026-09-29 19:30:01] 로컬 설정 파일 로드 성공: %APPDATA%\\PowerController\\power_timer_settings.json`
  ]);

  // Network Scheduler states
  const [networkTargetIps, setNetworkTargetIps] = useState<string>('192.168.0.10, 192.168.0.15');
  const [detectedPcs, setDetectedPcs] = useState([
    { ip: '192.168.0.5', host: 'ADMIN-DESKTOP', isSelf: true, tokenSet: true, status: '대기 중 (Online)' },
    { ip: '192.168.0.10', host: 'RESEARCH-LAB-01', isSelf: false, tokenSet: true, status: '대기 중 (Online)' },
    { ip: '192.168.0.15', host: 'DESIGN-WORK-02', isSelf: false, tokenSet: false, status: '대기 중 (Online)' },
    { ip: '192.168.0.22', host: 'MEETING-ROOM-PC', isSelf: false, tokenSet: true, status: '대기 중 (Online)' }
  ]);
  const [selectedPresetIndex, setSelectedPresetIndex] = useState(0);

  // Countdown effect
  useEffect(() => {
    let interval: any = null;
    if (isTimerRunning && remainingSeconds > 0) {
      interval = setInterval(() => {
        setRemainingSeconds(prev => {
          if (prev <= 1) {
            setIsTimerRunning(false);
            triggerActionDone();
            return 0;
          }
          const nextVal = prev - 1;
          // Play warning tick on last 10 seconds or exactly 30s/60s
          if ((nextVal <= 10 && nextVal > 0) || nextVal === 30 || nextVal === 60) {
            playSoundEffect('warningTick');
          }
          return nextVal;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning, remainingSeconds, currentSoundTheme, soundFeedbackEnabled]);

  const triggerActionDone = () => {
    const timestamp = new Date().toLocaleTimeString('ko-KR');
    setLogs(prev => [
      `[${timestamp}] ⚡ [타이머 실행] 모드 '${powerMode}' 명령이 성공적으로 실행되었습니다. (강제 닫기: ${forceClose ? '/f' : '없음'})`,
      ...prev
    ]);
    if (powerMode === 'alarm') {
      soundEngine.play(currentSoundTheme, 'timerAlarm');
    } else {
      soundEngine.play(currentSoundTheme, 'actionSuccess');
    }
    showInAppToast(`⚡ [완료] ${powerMode} 동작이 실행되었습니다!`);
  };

  const showInAppToast = (msg: string) => {
    setShowToast(msg);
    setTimeout(() => setShowToast(null), 3000);
  };

  const formatDigitalTime = (totalSec: number) => {
    const h = Math.floor(totalSec / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const startTimer = () => {
    if (runType === 'timer') {
      const total = inputH * 3600 + inputM * 60 + inputS;
      if (total <= 0) {
        showInAppToast('⚠️ 타이머 시간을 1초 이상 입력해 주세요.');
        playSoundEffect('buttonClick');
        return;
      }
      setRemainingSeconds(total);
    }
    setIsTimerRunning(true);
    playSoundEffect('actionSuccess');
    const timestamp = new Date().toLocaleTimeString('ko-KR');
    setLogs(prev => [
      `[${timestamp}] ▶ 타이머 시작: [모드: ${powerMode}] [남은시간: ${formatDigitalTime(remainingSeconds)}] [강제종료: ${forceClose ? '/f' : '미적용'}]`,
      ...prev
    ]);
    showInAppToast('▶ 타이머가 시작되었습니다.');
  };

  const stopTimer = () => {
    setIsTimerRunning(false);
    playSoundEffect('buttonClick');
    const timestamp = new Date().toLocaleTimeString('ko-KR');
    setLogs(prev => [
      `[${timestamp}] ⏹ 타이머 일시 정지/중지됨`,
      ...prev
    ]);
    showInAppToast('⏹ 타이머가 정지되었습니다.');
  };

  const resetTimer = () => {
    setIsTimerRunning(false);
    playSoundEffect('buttonClick');
    const total = inputH * 3600 + inputM * 60 + inputS;
    setRemainingSeconds(total > 0 ? total : 30 * 60);
    showInAppToast('🔄 타이머가 초기화되었습니다.');
  };

  const addPresetTime = (sec: number) => {
    playSoundEffect('buttonClick');
    setRemainingSeconds(prev => prev + sec);
    showInAppToast(`+${sec >= 3600 ? `${sec / 3600}시간` : `${sec / 60}분`} 추가되었습니다.`);
  };

  const addScheduleRule = () => {
    if (!newRuleName.trim()) return;
    playSoundEffect('actionSuccess');
    const newRule: ScheduleRuleItem = {
      id: Date.now().toString(),
      name: newRuleName,
      mode: newRuleMode,
      time: newRuleTime,
      days: ['매일'],
      enabled: true,
      forceClose: true
    };
    setRules(prev => [...prev, newRule]);
    setNewRuleName('');
    showInAppToast(`📅 '${newRule.name}' 스케줄이 등록되었습니다.`);
    setLogs(prev => [
      `[${new Date().toLocaleTimeString('ko-KR')}] 📅 신규 스케줄 등록: ${newRule.name} (${newRule.time})`,
      ...prev
    ]);
  };

  const deleteScheduleRule = (id: string) => {
    playSoundEffect('buttonClick');
    setRules(prev => prev.filter(r => r.id !== id));
    showInAppToast('🗑️ 스케줄 규칙이 삭제되었습니다.');
  };

  const toggleRuleEnabled = (id: string) => {
    setRules(prev => prev.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r));
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans select-none antialiased">
      {/* Top Application Control Toolbar (Desktop OS Environment Simulation) */}
      <header className="bg-slate-900/90 border-b border-slate-800 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs shadow-md">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-600/20 border border-blue-500/40 rounded text-blue-400 font-bold">
            <Monitor className="w-3.5 h-3.5" />
            <span>Windows Desktop Native View (Tkinter GUI 미러링)</span>
          </div>
          <span className="text-slate-400 hidden sm:inline">|</span>
          <span className="text-slate-400 hidden md:inline">단독 실행형 Windows C/Python 애플리케이션 화면</span>
        </div>

        {/* Program Switcher Tabs */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-md border border-slate-800">
          <button
            onClick={() => {
              setActiveApp('main');
              playSoundEffect('buttonClick');
            }}
            className={`px-3 py-1 rounded font-medium transition-colors flex items-center gap-1.5 ${
              activeApp === 'main'
                ? 'bg-blue-600 text-white shadow-sm font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Power className="w-3 h-3" />
            <span>PowerController.exe</span>
          </button>
          <button
            onClick={() => {
              setActiveApp('network');
              playSoundEffect('buttonClick');
            }}
            className={`px-3 py-1 rounded font-medium transition-colors flex items-center gap-1.5 ${
              activeApp === 'network'
                ? 'bg-blue-600 text-white shadow-sm font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Wifi className="w-3 h-3" />
            <span>PowerNetworkScheduler.exe</span>
          </button>
          <button
            onClick={() => {
              setActiveApp('injector');
              playSoundEffect('buttonClick');
            }}
            className={`px-3 py-1 rounded font-medium transition-colors flex items-center gap-1.5 ${
              activeApp === 'injector'
                ? 'bg-blue-600 text-white shadow-sm font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <ShieldCheck className="w-3 h-3" />
            <span>ApplySharedSchedules.exe</span>
          </button>
        </div>

        {/* Battery Status Indicator */}
        {battery && (
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-950/80 border border-slate-800 rounded text-slate-200 shadow-inner"
            title={`배터리 상태: ${battery.level}% (${battery.charging ? '충전 중' : '배터리 사용 중'}${battery.statusText ? ` - ${battery.statusText}` : ''})`}
          >
            <div className="relative flex items-center">
              {battery.charging ? (
                <BatteryCharging className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
              ) : battery.level <= 20 ? (
                <BatteryLow className="w-3.5 h-3.5 text-rose-400" />
              ) : battery.level <= 60 ? (
                <BatteryMedium className="w-3.5 h-3.5 text-amber-400" />
              ) : (
                <BatteryFull className="w-3.5 h-3.5 text-emerald-400" />
              )}
            </div>
            <span className="font-mono font-bold text-xs">{battery.level}%</span>
            <span className={`text-[10px] px-1 py-0.2 rounded font-semibold ${
              battery.charging
                ? 'bg-emerald-500/20 text-emerald-400'
                : battery.level <= 20
                ? 'bg-rose-500/20 text-rose-400'
                : 'bg-slate-800 text-slate-300'
            }`}>
              {battery.charging ? '충전중' : '배터리'}
            </span>
            {isPowerSavingActive && (
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-1 py-0.2 rounded font-bold flex items-center gap-0.5 animate-pulse">
                🍃 절전 중
              </span>
            )}
          </div>
        )}

        {/* Sound Status & Quick Controller in Desktop Toolbar */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => {
              playSoundEffect('buttonClick');
              setShowSettingsModal(true);
            }}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-950/80 hover:bg-slate-800 border border-slate-800 rounded text-slate-200 text-xs transition-colors cursor-pointer shadow-inner"
            title={`알림 효과음 테마: ${SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameKo || '클래식 벨'} (볼륨 ${currentSoundVolume}%) - 클릭 시 환경설정 열기`}
          >
            {currentSoundVolume === 0 ? (
              <VolumeX className="w-3.5 h-3.5 text-rose-400" />
            ) : currentSoundVolume < 50 ? (
              <Volume1 className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
            )}
            <span className="font-semibold text-emerald-300 hidden sm:inline">
              {SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameKo || '클래식 벨'}
            </span>
            <span className="font-mono text-[11px] text-slate-400 font-bold">
              {currentSoundVolume}%
            </span>
          </button>

          <button
            onClick={handleToggleMuteAllDesktop}
            className={`px-2 py-1 rounded text-xs font-bold transition-all cursor-pointer flex items-center gap-1 border shadow-sm ${
              currentSoundVolume === 0
                ? 'bg-rose-500/25 text-rose-300 border-rose-500/50 hover:bg-rose-500/35 animate-pulse'
                : 'bg-slate-950/80 hover:bg-slate-800 text-slate-300 border-slate-800'
            }`}
            title={
              currentSoundVolume === 0
                ? `음소거 해제 (${prevSoundVolume}% 복원)`
                : '모든 사운드 효과음 및 알림 즉시 음소거 (0%)'
            }
          >
            <VolumeX className="w-3.5 h-3.5 text-rose-400" />
            <span>{currentSoundVolume === 0 ? '음소거중 (0%)' : '음소거'}</span>
          </button>
        </div>

        {/* Web Switcher, Update Button & License Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowUpdateModal(true)}
            className="px-2.5 py-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded shadow flex items-center gap-1.5 transition-all text-xs cursor-pointer"
            title="업데이트 알림 팝업 및 최신 릴리스 정보 확인"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-spin" />
            <span>🚀 업데이트 확인</span>
          </button>
          {onOpenLicense && (
            <button
              onClick={onOpenLicense}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 flex items-center gap-1 transition-colors text-xs"
            >
              <FileText className="w-3 h-3 text-emerald-400" />
              <span>약관/라이선스 (한/영)</span>
            </button>
          )}
          {isWebAvailable && onSwitchToWeb && (
            <button
              onClick={onSwitchToWeb}
              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded shadow transition-colors flex items-center gap-1 text-xs"
            >
              <span>🌐 모던 웹 대시보드로 보기</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Desktop Workspace Area */}
      <main className="flex-1 p-3 sm:p-6 flex items-center justify-center bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black overflow-y-auto">
        {/* ========================================================================= */}
        {/* WINDOW 1: PowerController.exe (Main Desktop Native Tkinter App)           */}
        {/* ========================================================================= */}
        {activeApp === 'main' && (
          <div
            className={`w-full max-w-[540px] bg-[#1e1e24] border border-[#3f3f46] rounded shadow-2xl overflow-hidden flex flex-col text-[#f3f4f6] transition-all duration-200 ${
              isWindowMaximized ? 'fixed inset-3 max-w-none z-40' : ''
            }`}
            style={{ fontFamily: "'Malgun Gothic', 'Segoe UI', Arial, sans-serif" }}
          >
            {/* Windows OS Title Bar */}
            <div className="bg-[#18181b] border-b border-[#27272a] px-3 py-2 flex items-center justify-between text-xs select-none">
              <div className="flex items-center gap-2 font-bold text-slate-200">
                <div className="w-5 h-5 rounded-md overflow-hidden ring-1 ring-cyan-500/40 shadow-sm flex items-center justify-center bg-slate-950 flex-shrink-0">
                  <img src="/PowerController.png" alt="App Logo" className="w-full h-full object-cover scale-105" />
                </div>
                <span>PowerController v{APP_VERSION} - PC 자동 전원 관리</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                {/* Dedicated Mute All Button in Title Bar */}
                <button
                  onClick={handleToggleMuteAllDesktop}
                  className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer flex items-center gap-1 border ${
                    currentSoundVolume === 0
                      ? 'bg-rose-500/20 text-rose-300 border-rose-500/50 hover:bg-rose-500/30 animate-pulse'
                      : 'bg-[#27272a] text-slate-300 border-slate-700 hover:bg-slate-700'
                  }`}
                  title={
                    currentSoundVolume === 0
                      ? `음소거 해제 (${prevSoundVolume}% 복원)`
                      : '모든 사운드 즉시 음소거 (0%)'
                  }
                >
                  <VolumeX className="w-3 h-3 text-rose-400" />
                  <span>{currentSoundVolume === 0 ? '음소거중' : '음소거'}</span>
                </button>

                <div className="flex items-center gap-1 border-l border-slate-700 pl-1.5">
                  <button
                    onClick={() => setIsMinimized(!isMinimized)}
                    className="w-7 h-5 flex items-center justify-center hover:bg-[#27272a] hover:text-white rounded"
                    title="최소화"
                  >
                    <span className="mb-2 font-bold text-xs">—</span>
                  </button>
                <button
                  onClick={() => setIsWindowMaximized(!isWindowMaximized)}
                  className="w-7 h-5 flex items-center justify-center hover:bg-[#27272a] hover:text-white rounded"
                  title="최대화"
                >
                  <span className="text-[10px]">□</span>
                </button>
                <button
                  onClick={() => showInAppToast('트레이로 최소화되었습니다. (Windows 백그라운드 상주)')}
                  className="w-7 h-5 flex items-center justify-center hover:bg-red-600 hover:text-white rounded transition-colors"
                  title="닫기 (트레이 보관)"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

            {/* Native Creative DLL Status Bar Badge */}
            <div className="bg-[#121216] px-3 py-1.5 border-b border-[#27272a] flex items-center justify-between text-[11px] text-slate-400">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="font-semibold text-emerald-400">5-Tier 순수 창작 C/C++ DLL 가동 중</span>
              </div>
              <div className="flex items-center gap-2 text-[10px]">
                <span className="bg-[#27272a] px-1.5 py-0.5 rounded text-slate-300">PowerCoreNative</span>
                <span className="bg-[#27272a] px-1.5 py-0.5 rounded text-slate-300">NetBeacon</span>
                <span className="bg-[#27272a] px-1.5 py-0.5 rounded text-slate-300">FirewallNative</span>
                <span className="bg-[#27272a] px-1.5 py-0.5 rounded text-slate-300">SysPowerHook</span>
                <span className="bg-[#27272a] px-1.5 py-0.5 rounded text-slate-300">ScheduleCrypto</span>
              </div>
            </div>

            {/* In-app Toast message */}
            {showToast && (
              <div className="bg-blue-600 text-white px-3 py-1.5 text-xs font-bold text-center animate-fade-in">
                {showToast}
              </div>
            )}

            {/* Window Content Container */}
            <div className="p-4 space-y-3 text-[13px]">
              {/* 2-Column Symmetric Checkboxes (정확한 Tkinter 레이아웃) */}
              <div className="bg-[#18181b] border border-[#27272a] p-2.5 rounded space-y-1.5">
                {/* Row 1 */}
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-200">
                    <input
                      type="checkbox"
                      checked={isPinned}
                      onChange={e => setIsPinned(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>📌 상단 고정</span>
                  </label>
                  <button
                    onClick={() => {
                      setActiveTab('scheduler');
                      showInAppToast('스케줄러 탭으로 전환되었습니다.');
                    }}
                    className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold transition-colors"
                  >
                    🖥️ 스케줄러 팝업창 열기
                  </button>
                </div>

                {/* Row 2 */}
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-200">
                    <input
                      type="checkbox"
                      checked={autoStart}
                      onChange={e => setAutoStart(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>⚙️ 시작 시 자동 실행</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-200">
                    <input
                      type="checkbox"
                      checked={bootToTray}
                      onChange={e => setBootToTray(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>📥 부팅 시 트레이</span>
                  </label>
                </div>

                {/* Row 3 */}
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-200">
                    <input
                      type="checkbox"
                      checked={minimizeToTray}
                      onChange={e => setMinimizeToTray(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>📁 최소화 시 트레이</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer font-bold text-emerald-400" title="저장되지 않은 작업 강제 닫기">
                    <input
                      type="checkbox"
                      checked={forceClose}
                      onChange={e => setForceClose(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-emerald-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>⚡ 강제 닫기 (/f)</span>
                  </label>
                </div>

                {/* Row 4 */}
                <div className="flex items-center justify-between pt-0.5 border-t border-[#27272a]">
                  <label className="flex items-center gap-2 cursor-pointer font-bold text-blue-400">
                    <input
                      type="checkbox"
                      checked={networkReceive}
                      onChange={e => setNetworkReceive(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>📡 원격 예약 수신 허용 (포트 9988)</span>
                  </label>
                  <span className="text-[11px] text-slate-400">보안 토큰 활성</span>
                </div>
              </div>

              {/* Settings Toggle Button */}
              <button
                onClick={() => {
                  playSoundEffect('buttonClick');
                  setShowSettingsModal(true);
                }}
                className="w-full py-2 bg-[#2b2b36] hover:bg-[#323240] text-slate-200 font-bold rounded border border-[#3f3f46] flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                <Settings className="w-4 h-4 text-blue-400" />
                <span>⚙️ 설정 (Settings) ...</span>
              </button>

              {/* 3 Tab Navigation Header Bar */}
              <div className="flex items-center gap-1 border-b border-[#3f3f46] pb-1">
                <button
                  onClick={() => {
                    setActiveTab('control');
                    playSoundEffect('buttonClick');
                  }}
                  className={`flex-1 py-1.5 rounded text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                    activeTab === 'control'
                      ? 'bg-blue-600 text-white shadow'
                      : 'bg-[#2b2b36] text-slate-300 hover:bg-[#323240]'
                  }`}
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span>⏱ 간편 제어</span>
                </button>
                <button
                  onClick={() => {
                    setActiveTab('scheduler');
                    playSoundEffect('buttonClick');
                  }}
                  className={`flex-1 py-1.5 rounded text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                    activeTab === 'scheduler'
                      ? 'bg-blue-600 text-white shadow'
                      : 'bg-[#2b2b36] text-slate-300 hover:bg-[#323240]'
                  }`}
                >
                  <Calendar className="w-3.5 h-3.5" />
                  <span>📅 스케줄러</span>
                </button>
                <button
                  onClick={() => {
                    setActiveTab('history');
                    playSoundEffect('buttonClick');
                  }}
                  className={`flex-1 py-1.5 rounded text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                    activeTab === 'history'
                      ? 'bg-blue-600 text-white shadow'
                      : 'bg-[#2b2b36] text-slate-300 hover:bg-[#323240]'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>📋 동작 기록</span>
                </button>
              </div>

              {/* ============================================================= */}
              {/* TAB 1: Control Tab (간편 제어)                                */}
              {/* ============================================================= */}
              {activeTab === 'control' && (
                <div className="space-y-3">
                  {/* Power Mode: Clean Dropdown/Pulldown Selector vs Grid Toggle */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] text-slate-300 font-semibold">
                      <div className="flex items-center gap-1.5">
                        <span>⚡ 전원 동작 선택:</span>
                        <span className="font-bold text-blue-400">
                          {powerMode === 'shutdown' && '🛑 시스템 종료'}
                          {powerMode === 'restart' && '🔄 다시 시작'}
                          {powerMode === 'sleep' && '🌙 절전 모드'}
                          {powerMode === 'screenoff' && '📺 화면 끄기'}
                          {powerMode === 'logout' && '🚪 로그아웃'}
                          {powerMode === 'alarm' && '🔔 알람 알림'}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          const next = powerModeDisplayMode === 'dropdown' ? 'grid' : 'dropdown';
                          setPowerModeDisplayMode(next);
                          try { localStorage.setItem('desktop_power_mode_display', next); } catch {}
                          playSoundEffect('buttonClick');
                        }}
                        className="text-[10px] text-slate-400 hover:text-slate-200 underline cursor-pointer transition-colors"
                        title={powerModeDisplayMode === 'dropdown' ? '모든 버튼 그리드로 펼치기' : '드롭다운으로 화면을 깔끔하게 접기'}
                      >
                        {powerModeDisplayMode === 'dropdown' ? '🔲 버튼 펼치기' : '📋 풀다운 깔끔 접기'}
                      </button>
                    </div>

                    {powerModeDisplayMode === 'dropdown' ? (
                      <div className="relative">
                        <select
                          value={powerMode}
                          onChange={(e) => {
                            setPowerMode(e.target.value as any);
                            playSoundEffect('buttonClick');
                            const labels: Record<string, string> = {
                              shutdown: '시스템 종료',
                              restart: '다시 시작',
                              sleep: '절전 모드',
                              screenoff: '화면 끄기',
                              logout: '로그아웃',
                              alarm: '알람 알림',
                            };
                            showInAppToast(`⚡ 전원 동작: [${labels[e.target.value] || e.target.value}] 설정 완료`);
                          }}
                          className="w-full bg-[#24242e] border border-[#3f3f46] hover:border-blue-500/70 rounded px-3 py-2 text-xs font-bold text-slate-100 appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer pl-8 pr-8 shadow-inner"
                        >
                          <option value="shutdown">🛑 1. 시스템 종료 (Shutdown) - 모든 앱을 닫고 PC 전원을 완전히 끕니다</option>
                          <option value="restart">🔄 2. 다시 시작 (Restart) - 운영체제를 안전하게 재부팅합니다</option>
                          <option value="sleep">🌙 3. 절전 모드 (Sleep) - 작업 상태를 RAM에 유지하고 저전력 대기로 전환</option>
                          <option value="screenoff">📺 4. 화면 끄기 (Screen Off) - 백그라운드 유지 상태에서 모니터만 절전</option>
                          <option value="logout">🚪 5. 로그아웃 (Sign Out) - 현재 계정 세션을 안전하게 종료합니다</option>
                          <option value="alarm">🔔 6. 알람 알림 (Alarm Only) - 전원 차단 없이 알림음과 팝업만 발생</option>
                        </select>
                        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-sm pointer-events-none">
                          {powerMode === 'shutdown' && '🛑'}
                          {powerMode === 'restart' && '🔄'}
                          {powerMode === 'sleep' && '🌙'}
                          {powerMode === 'screenoff' && '📺'}
                          {powerMode === 'logout' && '🚪'}
                          {powerMode === 'alarm' && '🔔'}
                        </span>
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-1.5">
                        {[
                          { id: 'shutdown', label: '종료', icon: Power, color: 'bg-red-600 text-white' },
                          { id: 'restart', label: '재시작', icon: RotateCw, color: 'bg-orange-600 text-white' },
                          { id: 'sleep', label: '절전', icon: Moon, color: 'bg-indigo-600 text-white' },
                          { id: 'screenoff', label: '화면끔', icon: Monitor, color: 'bg-purple-600 text-white' },
                          { id: 'logout', label: '로그아웃', icon: LogOut, color: 'bg-slate-700 text-white' },
                          { id: 'alarm', label: '알람', icon: Bell, color: 'bg-yellow-600 text-white' }
                        ].map(mode => {
                          const isSelected = powerMode === mode.id;
                          return (
                            <button
                              key={mode.id}
                              onClick={() => {
                                setPowerMode(mode.id as any);
                                playSoundEffect('buttonClick');
                              }}
                              className={`py-2 px-2 rounded font-bold text-xs flex items-center justify-center gap-1.5 border transition-all cursor-pointer ${
                                isSelected
                                  ? `${mode.color} border-transparent shadow`
                                  : 'bg-[#2b2b36] hover:bg-[#353544] text-slate-200 border-[#3f3f46]'
                              }`}
                            >
                              <mode.icon className="w-3.5 h-3.5" />
                              <span>{mode.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Run Type: Timer vs Fixed Schedule */}
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => {
                        setRunType('timer');
                        playSoundEffect('buttonClick');
                      }}
                      className={`py-1.5 rounded font-bold text-xs transition-colors cursor-pointer ${
                        runType === 'timer'
                          ? 'bg-blue-600 text-white'
                          : 'bg-[#2b2b36] text-slate-300 hover:bg-[#323240]'
                      }`}
                    >
                      ⏳ 시간 타이머 (후)
                    </button>
                    <button
                      onClick={() => {
                        setRunType('schedule');
                        playSoundEffect('buttonClick');
                      }}
                      className={`py-1.5 rounded font-bold text-xs transition-colors cursor-pointer ${
                        runType === 'schedule'
                          ? 'bg-blue-600 text-white'
                          : 'bg-[#2b2b36] text-slate-300 hover:bg-[#323240]'
                      }`}
                    >
                      ⏰ 특정 시각 예약 (정시)
                    </button>
                  </div>

                  {/* Big Digital Display Counter (Tkinter Courier Font Display) */}
                  <div className="bg-[#18181b] border border-[#27272a] rounded py-4 px-3 text-center shadow-inner">
                    <div className="text-[11px] text-slate-400 font-medium mb-1">
                      {isTimerRunning ? '⚡ 카운트다운 진행 중...' : '대기 상태 (시작 대기)'}
                    </div>
                    <div
                      className="text-4xl sm:text-5xl font-mono font-black tracking-wider text-blue-400"
                      style={{ fontFamily: "'Courier New', Courier, monospace" }}
                    >
                      {formatDigitalTime(remainingSeconds)}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      {forceClose && (
                        <span className="text-emerald-400 font-bold">⚡ 실행 중인 앱 강제 종료 (/f) 활성</span>
                      )}
                    </div>
                  </div>

                  {/* Spinbox Inputs (H / M / S) */}
                  <div className="bg-[#18181b] border border-[#27272a] p-3 rounded">
                    <div className="text-[11px] text-slate-400 font-semibold mb-2">
                      [타이머] 지정된 시간/분/초 후 동작을 수행합니다.
                    </div>
                    <div className="flex items-center justify-center gap-4">
                      {/* Hour */}
                      <div className="flex flex-col items-center">
                        <span className="text-[11px] text-slate-400 mb-1">시 (H)</span>
                        <div className="flex items-center border border-[#3f3f46] rounded bg-[#2b2b36]">
                          <input
                            type="number"
                            min="0"
                            max="99"
                            value={inputH}
                            onChange={e => setInputH(Math.max(0, parseInt(e.target.value) || 0))}
                            className="w-12 text-center bg-transparent text-slate-100 font-bold py-1 text-sm focus:outline-none"
                          />
                          <div className="flex flex-col border-l border-[#3f3f46]">
                            <button
                              onClick={() => setInputH(prev => prev + 1)}
                              className="px-1 hover:bg-[#3f3f46] text-slate-300"
                            >
                              <ChevronUp className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => setInputH(prev => Math.max(0, prev - 1))}
                              className="px-1 hover:bg-[#3f3f46] text-slate-300"
                            >
                              <ChevronDown className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Minute */}
                      <div className="flex flex-col items-center">
                        <span className="text-[11px] text-slate-400 mb-1">분 (M)</span>
                        <div className="flex items-center border border-[#3f3f46] rounded bg-[#2b2b36]">
                          <input
                            type="number"
                            min="0"
                            max="59"
                            value={inputM}
                            onChange={e => setInputM(Math.max(0, parseInt(e.target.value) || 0))}
                            className="w-12 text-center bg-transparent text-slate-100 font-bold py-1 text-sm focus:outline-none"
                          />
                          <div className="flex flex-col border-l border-[#3f3f46]">
                            <button
                              onClick={() => setInputM(prev => prev + 1)}
                              className="px-1 hover:bg-[#3f3f46] text-slate-300"
                            >
                              <ChevronUp className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => setInputM(prev => Math.max(0, prev - 1))}
                              className="px-1 hover:bg-[#3f3f46] text-slate-300"
                            >
                              <ChevronDown className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Second */}
                      <div className="flex flex-col items-center">
                        <span className="text-[11px] text-slate-400 mb-1">초 (S)</span>
                        <div className="flex items-center border border-[#3f3f46] rounded bg-[#2b2b36]">
                          <input
                            type="number"
                            min="0"
                            max="59"
                            value={inputS}
                            onChange={e => setInputS(Math.max(0, parseInt(e.target.value) || 0))}
                            className="w-12 text-center bg-transparent text-slate-100 font-bold py-1 text-sm focus:outline-none"
                          />
                          <div className="flex flex-col border-l border-[#3f3f46]">
                            <button
                              onClick={() => setInputS(prev => prev + 1)}
                              className="px-1 hover:bg-[#3f3f46] text-slate-300"
                            >
                              <ChevronUp className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => setInputS(prev => Math.max(0, prev - 1))}
                              className="px-1 hover:bg-[#3f3f46] text-slate-300"
                            >
                              <ChevronDown className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 60-Minute Battery Consumption & Prediction Chart (Recharts) */}
                    <div className="mt-3">
                      <BatteryHistoryChart
                        currentBattery={battery}
                        timerState={isTimerRunning ? 'running' : 'idle'}
                        secondsRemaining={remainingSeconds}
                        lang="ko"
                        theme="dark"
                      />
                    </div>

                    {/* Quick +Preset Pull-down & Fast Buttons */}
                    <div className="mt-3 pt-2 border-t border-[#27272a] space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold">
                        <span>⏱️ 시간 프리셋 (풀다운 / 빠른 선택):</span>
                        <span className="text-[10px] text-blue-400 font-mono">단축 제어</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <div className="relative flex-1">
                          <select
                            defaultValue=""
                            onChange={(e) => {
                              const val = e.target.value;
                              if (!val) return;
                              if (val.startsWith('add:')) {
                                const sec = parseInt(val.split(':')[1], 10);
                                addPresetTime(sec);
                              } else if (val.startsWith('set:')) {
                                const sec = parseInt(val.split(':')[1], 10);
                                const h = Math.floor(sec / 3600);
                                const m = Math.floor((sec % 3600) / 60);
                                setInputH(h);
                                setInputM(m);
                                setInputS(0);
                                setRemainingSeconds(sec);
                                playSoundEffect('buttonClick');
                                showInAppToast(`⚡ ${sec >= 3600 ? `${sec / 3600}시간` : `${sec / 60}분`} 프리셋이 즉시 설정되었습니다.`);
                              }
                              e.target.value = '';
                            }}
                            className="w-full bg-[#2b2b36] border border-[#3f3f46] hover:border-blue-500/70 rounded px-2.5 py-1 text-xs text-slate-200 appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer pr-7 font-medium"
                          >
                            <option value="">⏱️ 자주 쓰는 시간 프리셋 풀다운...</option>
                            <optgroup label="➕ 시간 추가 (현재 시간에 누적)">
                              <option value="add:300">+5분 추가</option>
                              <option value="add:600">+10분 추가</option>
                              <option value="add:900">+15분 추가</option>
                              <option value="add:1800">+30분 추가</option>
                              <option value="add:2700">+45분 추가</option>
                              <option value="add:3600">+1시간 추가</option>
                              <option value="add:7200">+2시간 추가</option>
                            </optgroup>
                            <optgroup label="⚡ 즉시 지정 (지정 시간으로 타이머 리셋)">
                              <option value="set:1800">⚡ 30분 빠른 타이머 설정</option>
                              <option value="set:3600">⚡ 1시간 빠른 타이머 설정</option>
                              <option value="set:7200">⚡ 2시간 빠른 타이머 설정</option>
                              <option value="set:10800">⚡ 3시간 빠른 타이머 설정</option>
                            </optgroup>
                          </select>
                          <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
                        </div>
                        <button
                          onClick={() => addPresetTime(10 * 60)}
                          className="px-2 py-1 bg-[#2b2b36] hover:bg-[#353544] rounded text-xs font-bold text-slate-200 cursor-pointer shrink-0"
                        >
                          +10분
                        </button>
                        <button
                          onClick={() => addPresetTime(30 * 60)}
                          className="px-2 py-1 bg-[#2b2b36] hover:bg-[#353544] rounded text-xs font-bold text-slate-200 cursor-pointer shrink-0"
                        >
                          +30분
                        </button>
                        <button
                          onClick={() => addPresetTime(60 * 60)}
                          className="px-2 py-1 bg-[#2b2b36] hover:bg-[#353544] rounded text-xs font-bold text-slate-200 cursor-pointer shrink-0"
                        >
                          +1시간
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Execution Control Action Buttons */}
                  <div className="flex items-center gap-2 pt-1">
                    {!isTimerRunning ? (
                      <button
                        onClick={startTimer}
                        className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded flex items-center justify-center gap-2 shadow-md transition-colors"
                      >
                        <Play className="w-4 h-4 fill-white" />
                        <span>▶ 타이머 시작</span>
                      </button>
                    ) : (
                      <button
                        onClick={stopTimer}
                        className="flex-1 py-2.5 bg-red-600 hover:bg-red-500 text-white font-bold rounded flex items-center justify-center gap-2 shadow-md transition-colors"
                      >
                        <Square className="w-4 h-4 fill-white" />
                        <span>⏹ 타이머 중지</span>
                      </button>
                    )}
                    <button
                      onClick={resetTimer}
                      className="px-4 py-2.5 bg-[#374151] hover:bg-[#4b5563] text-slate-100 font-bold rounded flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <RotateCcw className="w-4 h-4" />
                      <span>🔄 리셋</span>
                    </button>
                  </div>
                </div>
              )}

              {/* ============================================================= */}
              {/* TAB 2: Scheduler Tab (고급 스케줄러)                          */}
              {/* ============================================================= */}
              {activeTab === 'scheduler' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">📅 예약된 전원 제어 규칙 목록</span>
                    <span className="text-[11px] text-blue-400 font-semibold">{rules.length}개 활성</span>
                  </div>

                  {/* Rules List Container */}
                  <div className="bg-[#18181b] border border-[#27272a] rounded p-2 max-h-56 overflow-y-auto space-y-1.5">
                    {rules.map(rule => (
                      <div
                        key={rule.id}
                        className="bg-[#2b2b36] border border-[#3f3f46] p-2 rounded flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={rule.enabled}
                            onChange={() => toggleRuleEnabled(rule.id)}
                            className="rounded bg-[#18181b] border-[#4b5563] text-blue-600 w-4 h-4 cursor-pointer"
                          />
                          <div>
                            <div className="font-bold text-slate-100 flex items-center gap-1.5">
                              <span>{rule.name}</span>
                              <span className="px-1.5 py-0.2 text-[10px] bg-red-600/30 text-red-300 rounded font-bold">
                                {rule.mode}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400">
                              ⏰ {rule.time} | 📅 {rule.days.join(', ')} | ⚡ /f 강제 종료
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => deleteScheduleRule(rule.id)}
                          className="text-slate-400 hover:text-red-400 p-1"
                          title="삭제"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Quick Add Rule Form */}
                  <div className="bg-[#18181b] border border-[#27272a] p-3 rounded space-y-2">
                    <div className="text-xs font-bold text-slate-200">➕ 새 스케줄 규칙 등록</div>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="규칙 제목"
                        value={newRuleName}
                        onChange={e => setNewRuleName(e.target.value)}
                        className="bg-[#2b2b36] border border-[#3f3f46] rounded px-2.5 py-1 text-xs text-white"
                      />
                      <input
                        type="time"
                        value={newRuleTime}
                        onChange={e => setNewRuleTime(e.target.value)}
                        className="bg-[#2b2b36] border border-[#3f3f46] rounded px-2.5 py-1 text-xs text-white"
                      />
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <select
                        value={newRuleMode}
                        onChange={e => setNewRuleMode(e.target.value as any)}
                        className="bg-[#2b2b36] border border-[#3f3f46] rounded px-2 py-1 text-xs text-white"
                      >
                        <option value="shutdown">종료 (Shutdown)</option>
                        <option value="restart">재시작 (Restart)</option>
                        <option value="sleep">절전 (Sleep)</option>
                        <option value="screenoff">화면끔 (Screen Off)</option>
                        <option value="logout">로그아웃 (Logout)</option>
                        <option value="alarm">알람 (Alarm)</option>
                      </select>
                      <button
                        onClick={addScheduleRule}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold transition-colors"
                      >
                        + 등록하기
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* ============================================================= */}
              {/* TAB 3: History Tab (동작 기록)                                */}
              {/* ============================================================= */}
              {activeTab === 'history' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200 text-xs">📋 시스템 전원 제어 및 타이머 동작 기록</span>
                    <button
                      onClick={() => {
                        setLogs([`[${new Date().toLocaleTimeString('ko-KR')}] 로그가 초기화되었습니다.`]);
                        showInAppToast('로그가 초기화되었습니다.');
                      }}
                      className="px-2 py-0.5 bg-red-600/20 border border-red-500/40 hover:bg-red-600/40 text-red-300 rounded text-[11px] font-bold"
                    >
                      🗑️ 로그 초기화
                    </button>
                  </div>
                  <div
                    className="bg-[#18181b] border border-[#27272a] rounded p-3 text-[11px] font-mono text-slate-300 h-64 overflow-y-auto space-y-1"
                    style={{ fontFamily: "'Consolas', monospace" }}
                  >
                    {logs.map((log, i) => (
                      <div key={i} className="leading-relaxed border-b border-slate-900/60 pb-0.5">
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Footer Information & CISNET Branding (main.py footer_frame 100% 동일) */}
              <div className="pt-2.5 border-t border-[#27272a] text-center text-[11px] text-slate-400 space-y-1">
                <div className="flex items-center justify-center gap-2 flex-wrap">
                  <a
                    href="http://www.cisnet.co.kr/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-slate-200 transition-colors cursor-pointer"
                  >
                    소속: http://www.cisnet.co.kr/
                  </a>
                  <span>|</span>
                  <span>개발자: AhBiYout</span>
                  <span>|</span>
                  <span className="text-blue-400 font-bold">v{APP_VERSION}</span>
                </div>
                <div className="flex items-center justify-center gap-2 flex-wrap">
                  <a
                    href="https://ahbiyoutvibe.blogspot.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 underline hover:text-blue-300 transition-colors cursor-pointer"
                  >
                    구글블로그: https://ahbiyoutvibe.blogspot.com/
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* WINDOW 2: PowerNetworkScheduler.exe (Standalone Commander Tower)          */}
        {/* ========================================================================= */}
        {activeApp === 'network' && (
          <div
            className="w-full max-w-[620px] bg-[#1e1e24] border border-[#3f3f46] rounded shadow-2xl overflow-hidden flex flex-col text-[#f3f4f6]"
            style={{ fontFamily: "'Malgun Gothic', 'Segoe UI', Arial, sans-serif" }}
          >
            {/* Window Title Bar */}
            <div className="bg-[#18181b] border-b border-[#27272a] px-3 py-2 flex items-center justify-between text-xs select-none">
              <div className="flex items-center gap-2 font-bold text-slate-200">
                <div className="w-4 h-4 rounded bg-blue-600 flex items-center justify-center text-white text-[10px] font-black">
                  N
                </div>
                <span>PowerNetworkScheduler v{APP_VERSION} - 사내 원격 통합 제어 타워</span>
              </div>
              <div className="flex items-center gap-1 text-slate-400">
                <span className="text-[11px] text-emerald-400 font-bold mr-2">● UDP 9986 감시 중</span>
                <button className="w-7 h-5 flex items-center justify-center hover:bg-[#27272a] rounded">
                  <span className="text-[10px]">□</span>
                </button>
                <button
                  onClick={() => setActiveApp('main')}
                  className="w-7 h-5 flex items-center justify-center hover:bg-red-600 hover:text-white rounded"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="p-4 space-y-3.5 text-xs">
              {/* Section 1: Administrator Recovery Key & Token */}
              <div className="bg-[#18181b] border border-[#27272a] p-3 rounded space-y-2">
                <div className="flex items-center justify-between font-bold">
                  <span className="text-slate-200">🔑 관리자 보안 인증 & 비상 복구 키 (ScheduleCrypto)</span>
                  <span className="text-[10px] text-emerald-400 font-mono">HMAC-SHA256 암호화</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="password"
                    defaultValue="PowerRescue#2026!Admin"
                    placeholder="마스터 복구 키"
                    className="bg-[#2b2b36] border border-[#3f3f46] px-2.5 py-1 rounded text-white font-mono"
                  />
                  <input
                    type="text"
                    defaultValue="CisnetMasterToken2026"
                    placeholder="사내 보안 인증 토큰"
                    className="bg-[#2b2b36] border border-[#3f3f46] px-2.5 py-1 rounded text-white font-mono"
                  />
                </div>
              </div>

              {/* Section 2: Online PC Discovery Monitoring */}
              <div className="bg-[#18181b] border border-[#27272a] p-3 rounded space-y-2">
                <div className="flex items-center justify-between font-bold">
                  <span className="text-slate-200">💻 사내망 탐지 PC 모니터링 목록 (NetBeaconEngine 0.0% CPU)</span>
                  <span className="text-blue-400 font-bold">{detectedPcs.length}대 감지</span>
                </div>
                <div className="bg-[#2b2b36] border border-[#3f3f46] rounded p-2 max-h-36 overflow-y-auto space-y-1">
                  {detectedPcs.map((pc, idx) => (
                    <div
                      key={idx}
                      className={`p-1.5 rounded flex items-center justify-between text-xs ${
                        pc.isSelf ? 'bg-blue-950/40 border border-blue-500/30' : 'hover:bg-[#353544]'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                        <span className="font-bold text-slate-100">{pc.ip}</span>
                        <span className="text-slate-400 font-mono">({pc.host})</span>
                        {pc.isSelf && (
                          <span className="px-1.5 py-0.2 bg-amber-500/20 text-amber-300 border border-amber-500/40 rounded text-[10px] font-bold">
                            👑 관리자 PC
                          </span>
                        )}
                      </div>
                      <span className="text-slate-400 text-[11px]">{pc.status}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 3: Popular 10 Presets Dropdown */}
              <div className="bg-[#18181b] border border-[#27272a] p-3 rounded space-y-2">
                <div className="font-bold text-slate-200">🎯 10대 자주 쓰는 전원 시나리오 프리셋</div>
                <select
                  value={selectedPresetIndex}
                  onChange={e => setSelectedPresetIndex(parseInt(e.target.value))}
                  className="w-full bg-[#2b2b36] border border-[#3f3f46] rounded p-1.5 text-xs text-white"
                >
                  <option value={0}>🏢 1. 정시 퇴근 자동 종료 (월~금 18:30)</option>
                  <option value={1}>🌙 2. 야간 심야 자동 종료 (매일 23:30)</option>
                  <option value={2}>☕ 3. 점심시간 절전 모드 (월~금 12:00)</option>
                  <option value={3}>🔄 4. 월요일 아침 정기 리부팅 (월 08:30)</option>
                  <option value={4}>💾 5. 금요일 퇴근 전 백업 알림 (금 18:00)</option>
                  <option value={5}>⚡ 6. 1시간 후 빠른 종료 (현재 + 1시간)</option>
                  <option value={6}>💤 7. 30분 무작업 시 절전 (유휴 절전)</option>
                  <option value={7}>📺 8. 모니터 화면 즉시 끄기 (화면 절전)</option>
                  <option value={8}>⏰ 9. 정기 시스템 점검 리셋 (일 04:00)</option>
                  <option value={9}>🚨 10. 긴급 정지 비상 알람</option>
                </select>
              </div>

              {/* Section 4: Target IP & Unified Remote Action Pulldown */}
              <div className="bg-[#18181b] border border-[#27272a] p-3 rounded space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200">🎯 대상 PC 지정 (풀다운 빠른 선택 및 직접 입력)</span>
                  <span className="text-[10px] text-blue-400 font-mono">단일 & 그룹 IP</span>
                </div>

                {/* Pulldown PC Selector */}
                <div className="relative">
                  <select
                    defaultValue=""
                    onChange={(e) => {
                      if (!e.target.value) return;
                      setNetworkTargetIps(e.target.value);
                      playSoundEffect('buttonClick');
                      showInAppToast(`🎯 대상 PC [${e.target.value}]가 즉시 지정되었습니다.`);
                      e.target.value = '';
                    }}
                    className="w-full bg-[#24242e] border border-[#3f3f46] hover:border-blue-500/70 rounded px-2.5 py-1.5 text-xs text-slate-200 font-medium appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer pr-8 shadow-inner"
                  >
                    <option value="">💻 감지된 사내 PC 풀다운 선택 (클릭 시 자동 입력)...</option>
                    <optgroup label="📡 실시간 탐지된 활성 PC">
                      {detectedPcs.map((pc, idx) => (
                        <option key={idx} value={pc.ip}>
                          {pc.ip} ({pc.host}) - {pc.status} {pc.isSelf ? '[👑 관리자 본인 PC]' : ''}
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="📢 사내 그룹 및 브로드캐스트">
                      <option value="192.168.1.255">📢 사내 전체 서브넷 브로드캐스트 (192.168.1.255)</option>
                      <option value="192.168.1.101, 192.168.1.102, 192.168.1.103">🏢 개발팀 전체 PC (101, 102, 103)</option>
                      <option value="192.168.1.104, 192.168.1.105">📊 기획/디자인팀 PC (104, 105)</option>
                    </optgroup>
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>

                <input
                  type="text"
                  value={networkTargetIps}
                  onChange={e => setNetworkTargetIps(e.target.value)}
                  placeholder="대상 IP 직접 입력 (쉼표로 복수 지정 가능)"
                  className="w-full bg-[#2b2b36] border border-[#3f3f46] px-2.5 py-1.5 rounded text-white text-xs font-mono"
                />
                
                {/* Unified Remote Command Pulldown & Execution */}
                <div className="space-y-1.5 pt-1 border-t border-[#27272a]">
                  <div className="flex items-center justify-between text-[11px] text-slate-300 font-semibold">
                    <span>⚡ 원격 실행 명령 풀다운 (통합 제어):</span>
                    <span className="text-[10px] text-emerald-400 font-mono">Clean Pulldown</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <select
                        value={selectedRemoteAction}
                        onChange={(e) => setSelectedRemoteAction(e.target.value)}
                        className="w-full bg-[#24242e] border border-[#3f3f46] hover:border-blue-500/70 rounded px-2.5 py-2 text-xs text-slate-100 font-bold appearance-none cursor-pointer pr-8 shadow-inner"
                      >
                        <option value="shutdown">🛑 1. 대상 PC 즉시 전원 종료 (Power Off)</option>
                        <option value="restart">🔄 2. 대상 PC 즉시 시스템 다시 시작 (Reboot)</option>
                        <option value="sleep">🌙 3. 대상 PC 절전 모드 전환 (Sleep)</option>
                        <option value="screenoff">📺 4. 대상 PC 화면 끄기 (Screen Off)</option>
                        <option value="sync">📡 5. 선택한 스케줄 규칙 원격 일괄 동기화 (TCP 9988)</option>
                        <option value="alarm">🚨 6. 사내 대상 PC 긴급 비상 알람 송출 (Alarm)</option>
                      </select>
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                    <button
                      onClick={() => {
                        playSoundEffect('actionSuccess');
                        const actionLabels: Record<string, string> = {
                          shutdown: `🛑 대상 PC [${networkTargetIps}] 즉시 종료 명령을 송출했습니다.`,
                          restart: `🔄 대상 PC [${networkTargetIps}] 즉시 다시 시작 명령을 송출했습니다.`,
                          sleep: `🌙 대상 PC [${networkTargetIps}] 절전 모드 명령을 송출했습니다.`,
                          screenoff: `📺 대상 PC [${networkTargetIps}] 화면 끄기 명령을 송출했습니다.`,
                          sync: `📡 대상 PC [${networkTargetIps}]로 스케줄 규칙을 일괄 동기화했습니다. (TCP 9988)`,
                          alarm: `🚨 대상 PC [${networkTargetIps}]에 긴급 알람을 전송했습니다.`,
                        };
                        showInAppToast(actionLabels[selectedRemoteAction] || '원격 명령이 전송되었습니다.');
                      }}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold text-xs shadow flex items-center gap-1.5 cursor-pointer whitespace-nowrap shrink-0 transition-colors"
                    >
                      <Play className="w-3.5 h-3.5 fill-white" />
                      <span>전송 실행</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* WINDOW 3: ApplySharedSchedules.exe (One-Click Offline Schedule Injector)   */}
        {/* ========================================================================= */}
        {activeApp === 'injector' && (
          <div
            className="w-full max-w-[500px] bg-[#1e1e24] border border-[#3f3f46] rounded shadow-2xl overflow-hidden flex flex-col text-[#f3f4f6]"
            style={{ fontFamily: "'Malgun Gothic', 'Segoe UI', Arial, sans-serif" }}
          >
            {/* Window Title Bar */}
            <div className="bg-[#18181b] border-b border-[#27272a] px-3 py-2 flex items-center justify-between text-xs select-none">
              <div className="flex items-center gap-2 font-bold text-slate-200">
                <div className="w-4 h-4 rounded bg-emerald-600 flex items-center justify-center text-white text-[10px] font-black">
                  I
                </div>
                <span>ApplySharedSchedules v{APP_VERSION} - 스케줄 원클릭 주입기</span>
              </div>
              <button
                onClick={() => {
                  setActiveApp('main');
                  playSoundEffect('buttonClick');
                }}
                className="w-7 h-5 flex items-center justify-center hover:bg-red-600 hover:text-white rounded cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="p-4 space-y-3.5 text-xs">
              <div className="bg-emerald-950/30 border border-emerald-500/40 p-3 rounded space-y-1">
                <div className="font-bold text-emerald-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  <span>ScheduleCrypto HMAC-SHA256 무결성 검증 완료</span>
                </div>
                <div className="text-[11px] text-slate-300">
                  본 실행 파일에는 관리자 인증 서명과 함께 사내 표준 전원 스케줄이 암호화 봉투 형태로 임베딩되어 있습니다.
                </div>
              </div>

              {/* Embedded Schedule Preview */}
              <div className="bg-[#18181b] border border-[#27272a] p-3 rounded space-y-2">
                <div className="font-bold text-slate-200">📦 주입 대상 스케줄 규칙 (미리보기)</div>
                <div className="bg-[#2b2b36] p-2 rounded text-[11px] font-mono text-slate-300 space-y-1">
                  <div>• [규칙 1] 🏢 정시 퇴근 자동 종료 (18:30 월~금)</div>
                  <div>• [규칙 2] 🌙 야간 심야 자동 종료 (23:30 매일)</div>
                  <div>• [규칙 3] 🔄 월요일 아침 정기 리부팅 (08:30 월)</div>
                </div>
              </div>

              {/* Target Location Detection */}
              <div className="bg-[#18181b] border border-[#27272a] p-3 rounded space-y-1 text-[11px]">
                <div className="font-bold text-slate-200">🎯 자동 탐지된 대상 경로</div>
                <div className="text-blue-400 font-mono break-all">
                  %APPDATA%\PowerController\power_scheduler_rules.json
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => {
                  playSoundEffect('actionSuccess');
                  showInAppToast('🚀 스케줄이 안전하게 주입 및 동기화되었습니다! (무결성 100% 검증)');
                }}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded flex items-center justify-center gap-2 shadow transition-colors text-sm cursor-pointer"
              >
                <HardDrive className="w-4 h-4" />
                <span>🚀 스케줄 원클릭 즉시 주입 및 적용</span>
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Settings Modal (Tkinter Settings Style) */}
      {showSettingsModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="w-full max-w-[480px] bg-[#1e1e24] border border-[#3f3f46] rounded shadow-2xl overflow-hidden text-xs">
            <div className="bg-[#18181b] border-b border-[#27272a] px-3 py-2 flex items-center justify-between font-bold text-slate-200">
              <span>⚙️ PowerController 환경설정 (Settings)</span>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="hover:bg-red-600 p-1 rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="p-4 space-y-3 max-h-[75vh] overflow-y-auto">
              <div className="bg-[#18181b] p-3 rounded space-y-2 border border-[#27272a]">
                <span className="font-bold text-slate-200">1. 부팅 및 트레이 동작</span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={autoStart} onChange={e => setAutoStart(e.target.checked)} />
                  <span>Windows 시작 시 자동 실행 (레지스트리 Run 키)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={bootToTray} onChange={e => setBootToTray(e.target.checked)} />
                  <span>부팅 시 화면 표시 없이 트레이로 바로 숨기기</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={minimizeToTray} onChange={e => setMinimizeToTray(e.target.checked)} />
                  <span>최소화 버튼 클릭 시 작업표시줄 대신 트레이로 숨김</span>
                </label>
              </div>

              <div className="bg-[#18181b] p-3 rounded space-y-2 border border-[#27272a]">
                <span className="font-bold text-slate-200">2. 강제 닫기 플래그 (/f)</span>
                <label className="flex items-center gap-2 cursor-pointer text-emerald-400 font-bold">
                  <input type="checkbox" checked={forceClose} onChange={e => setForceClose(e.target.checked)} />
                  <span>전원 명령 시 저장되지 않은 프로그램 강제 종료 (/f) 기본 활성화</span>
                </label>
                <div className="text-[11px] text-slate-400">
                  컴퓨터 종료 시 메모장 등 저장 대화상자로 인한 전원 차단 중단 방지.
                </div>
              </div>

              <div className="bg-[#18181b] p-3 rounded space-y-2 border border-[#27272a]">
                <span className="font-bold text-slate-200">3. 네트워크 원격 보안</span>
                <label className="flex items-center gap-2 cursor-pointer text-blue-400 font-bold">
                  <input type="checkbox" checked={networkReceive} onChange={e => setNetworkReceive(e.target.checked)} />
                  <span>TCP 9988 포트 원격 스케줄 수신 활성화</span>
                </label>
                <div className="flex items-center gap-2 pt-1">
                  <span className="text-slate-400">네트워크 보안 토큰:</span>
                  <input
                    type="password"
                    defaultValue="MySecretToken#123"
                    className="bg-[#2b2b36] border border-[#3f3f46] px-2 py-1 rounded text-white font-mono flex-1 text-xs"
                  />
                </div>
              </div>

              {/* 4. Sound & Alert Themes (Pixabay Sound Effects & Web Audio Mixer) */}
              <div className="bg-[#18181b] p-3 rounded space-y-3 border border-[#27272a]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-bold text-emerald-400">
                    <Volume2 className="w-4 h-4 text-emerald-400" />
                    <span>4. 알림 효과음 사운드 뱅크 (Pixabay 선별 & Web Audio)</span>
                  </div>
                  <span className="text-[10px] text-emerald-300/90 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 font-mono">
                    현재: {SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameKo || '클래식 벨'}
                  </span>
                </div>

                {/* Master Volume Controller & Quick Presets */}
                <div className="bg-[#24242e] p-2.5 rounded border border-[#373744] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-semibold flex items-center gap-1.5">
                      {currentSoundVolume === 0 ? (
                        <VolumeX className="w-4 h-4 text-rose-400" />
                      ) : currentSoundVolume < 50 ? (
                        <Volume1 className="w-4 h-4 text-amber-400" />
                      ) : (
                        <Volume2 className="w-4 h-4 text-emerald-400" />
                      )}
                      <span>마스터 볼륨 (Master Volume)</span>
                    </span>
                    <span className="font-mono font-bold text-emerald-400 text-sm">
                      {currentSoundVolume}%
                    </span>
                  </div>

                  <div className="flex items-center gap-2.5">
                    <button
                      type="button"
                      onClick={() => {
                        const newVol = currentSoundVolume === 0 ? 80 : 0;
                        handleVolumeChange(newVol);
                        if (newVol > 0) playSoundEffect('buttonClick');
                      }}
                      className="px-2 py-1 bg-[#2b2b36] hover:bg-[#383848] text-slate-300 hover:text-white rounded text-[11px] font-bold border border-[#3f3f46] transition-colors cursor-pointer"
                    >
                      {currentSoundVolume === 0 ? '🔊 음소거 해제' : '🔇 음소거'}
                    </button>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={currentSoundVolume}
                      onChange={(e) => handleVolumeChange(parseInt(e.target.value))}
                      className="flex-1 accent-emerald-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                    />
                  </div>

                  {/* Quick Volume Preset Buttons */}
                  <div className="flex items-center justify-between gap-1 pt-1 border-t border-[#373744]">
                    <span className="text-[10px] text-slate-400 font-medium">빠른 볼륨 설정:</span>
                    <div className="flex items-center gap-1">
                      {[0, 30, 50, 80, 100].map((v) => (
                        <button
                          key={v}
                          type="button"
                          onClick={() => {
                            handleVolumeChange(v);
                            if (v > 0) playSoundEffect('buttonClick');
                          }}
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold transition-colors cursor-pointer ${
                            currentSoundVolume === v
                              ? 'bg-emerald-600 text-white'
                              : 'bg-[#2b2b36] hover:bg-[#383848] text-slate-300'
                          }`}
                        >
                          {v === 0 ? '0%' : `${v}%`}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 1. Sound Theme Pull-down Selection */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-slate-300 font-semibold">
                    <span>알림음 테마 선택 (드롭다운 / 풀다운):</span>
                    <span className="text-[10px] text-emerald-400 font-mono">
                      ✓ {SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameKo}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <select
                        value={currentSoundTheme}
                        onChange={(e) => handleSelectSoundTheme(e.target.value as SoundTheme)}
                        className="w-full bg-[#24242e] border border-[#3f3f46] hover:border-emerald-500/70 rounded px-3 py-2 text-xs font-bold text-slate-100 appearance-none focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer pl-8 pr-8 shadow-inner"
                      >
                        {SOUND_THEMES.map((th) => (
                          <option key={th.id} value={th.id} className="bg-[#1e1e24] text-slate-100 py-1 font-medium">
                            {th.icon} {th.nameKo} ({th.nameEn}) - {th.descKo}
                          </option>
                        ))}
                      </select>
                      <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-sm pointer-events-none">
                        {SOUND_THEMES.find(t => t.id === currentSoundTheme)?.icon || '🔔'}
                      </span>
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        playSoundEffect('timerAlarm');
                        showInAppToast(`[${SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameKo}] 알림음 사운드 테스트 재생`);
                      }}
                      className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold transition-colors flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow shrink-0"
                      title="선택된 알림음 사운드 즉시 테스트 재생"
                    >
                      <Play className="w-3 h-3 fill-white" />
                      <span>Play Test (테스트 재생)</span>
                    </button>
                  </div>
                  <div className="text-[10px] text-slate-400 pl-1">
                    ℹ️ {SOUND_THEMES.find(t => t.id === currentSoundTheme)?.descKo}
                  </div>
                </div>

                {/* 2. Situational Sound Audition Test Pull-down */}
                <div className="bg-[#24242e] p-2.5 rounded border border-[#373744] space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                    <span>상황별 효과음 테스트 풀다운:</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <select
                        value={selectedSoundTestTrigger}
                        onChange={(e) => setSelectedSoundTestTrigger(e.target.value as any)}
                        className="w-full bg-[#1e1e24] border border-[#3f3f46] hover:border-blue-500/70 rounded px-3 py-2 text-xs text-slate-200 appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer pr-8 font-medium shadow-inner"
                      >
                        <option value="preview" className="bg-[#1e1e24]">🔔 1. 테마 대표 시그니처 톤 (미리듣기)</option>
                        <option value="warningTick" className="bg-[#1e1e24]">⏱️ 2. 10초 카운트다운 틱 경고음 (Tick)</option>
                        <option value="hourlyChime" className="bg-[#1e1e24]">🏛️ 3. 매시 정각 시계탑 차임벨 (00분 정각)</option>
                        <option value="timerAlarm" className="bg-[#1e1e24]">🚨 4. 타이머 만료 알람 경보음 (Alarm)</option>
                        <option value="actionSuccess" className="bg-[#1e1e24]">✨ 5. 전원 명령 완료 및 스케줄 등록 성공음</option>
                      </select>
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        playSoundEffect(selectedSoundTestTrigger);
                        const labels: Record<string, string> = {
                          preview: '테마 대표 시그니처 톤',
                          warningTick: '10초 카운트다운 틱 경고음',
                          hourlyChime: '정각 시계탑 차임벨',
                          timerAlarm: '타이머 만료 알람 경보음',
                          actionSuccess: '명령 실행 및 성공음'
                        };
                        showInAppToast(`🔊 [${labels[selectedSoundTestTrigger] || selectedSoundTestTrigger}] 재생`);
                      }}
                      className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-bold transition-colors flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow shrink-0"
                    >
                      <Play className="w-3 h-3 fill-white" />
                      <span>테스트 재생</span>
                    </button>
                  </div>
                </div>

                {/* Additional Audio Toggles */}
                <div className="space-y-1.5 pt-1 border-t border-[#27272a]">
                  <label className="flex items-center justify-between cursor-pointer py-1 text-slate-300 hover:text-white">
                    <span className="text-xs">🔔 매시 정각 시계탑 차임벨 (00분 00초) 알림</span>
                    <input
                      type="checkbox"
                      checked={currentHourlyChime}
                      onChange={(e) => handleHourlyChimeToggle(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-emerald-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                  </label>
                  <label className="flex items-center justify-between cursor-pointer py-1 text-slate-300 hover:text-white">
                    <span className="text-xs">🖱️ 버튼 클릭 및 조작 인터랙션 효과음</span>
                    <input
                      type="checkbox"
                      checked={soundFeedbackEnabled}
                      onChange={(e) => {
                        setSoundFeedbackEnabled(e.target.checked);
                        onSoundFeedbackChange?.(e.target.checked);
                        try {
                          localStorage.setItem('power_sound_feedback', e.target.checked ? 'true' : 'false');
                        } catch {}
                        if (e.target.checked) playSoundEffect('buttonClick');
                      }}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-emerald-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                  </label>
                </div>
              </div>

              {/* 5. Smart Power Saving Mode (<20% battery auto dimming) */}
              <div className="bg-[#18181b] p-3 rounded space-y-2 border border-[#27272a]">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                    🍃 5. 스마트 절전 모드 (배터리 20% 이하 감지)
                  </span>
                  <label className="flex items-center gap-1.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={powerSavingToggle}
                      onChange={(e) => {
                        setPowerSavingToggle(e.target.checked);
                        try {
                          localStorage.setItem('power_saving_mode', e.target.checked ? 'true' : 'false');
                        } catch {}
                        showInAppToast(e.target.checked ? '스마트 절전 모드가 활성화되었습니다.' : '스마트 절전 모드가 비활성화되었습니다.');
                      }}
                      className="sr-only peer"
                    />
                    <div className="relative w-7 h-4 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-600"></div>
                  </label>
                </div>
                <div className="text-[11px] text-slate-300 leading-relaxed">
                  배터리 잔량이 20% 이하로 떨어지면 플로팅 위젯의 투명도를 자동으로 낮추고 배경 애니메이션을 어둡게 감쇠하여 배터리 방전을 지연시킵니다.
                </div>
              </div>

              {/* 6. Auto-Lock Desktop Session on Idle (Timer Running) */}
              <div className="bg-[#18181b] p-3 rounded space-y-2 border border-[#27272a]">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-blue-400 flex items-center gap-1.5">
                    🔒 6. 타이머 가동 중 자동 화면 잠금 (Auto-Lock Desktop)
                  </span>
                  <label className="flex items-center gap-1.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={idleLockEnabled}
                      onChange={(e) => {
                        setIdleLockEnabled(e.target.checked);
                        try {
                          localStorage.setItem('power_idle_lock_enabled', e.target.checked ? 'true' : 'false');
                        } catch {}
                        showInAppToast(e.target.checked ? '유휴 상태 자동 화면 잠금이 활성화되었습니다.' : '유휴 상태 자동 화면 잠금이 비활성화되었습니다.');
                      }}
                      className="sr-only peer"
                    />
                    <div className="relative w-7 h-4 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                <div className="text-[11px] text-slate-300 leading-relaxed">
                  타이머 가동 중 지정된 시간 동안 마우스/키보드 입력이 없으면 Windows 데스크톱 세션을 자동으로 잠급니다(Win + L).
                </div>
                <div className="flex items-center justify-between gap-2 pt-1 border-t border-[#27272a]">
                  <span className="text-slate-400 text-xs">유휴 감지 시간:</span>
                  <select
                    value={idleLockMinutes}
                    onChange={(e) => {
                      const m = parseInt(e.target.value, 10);
                      setIdleLockMinutes(m);
                      try {
                        localStorage.setItem('power_idle_lock_minutes', m.toString());
                      } catch {}
                    }}
                    disabled={!idleLockEnabled}
                    className={`bg-[#24242e] text-slate-200 text-xs font-semibold rounded px-2.5 py-1 border border-[#3f3f46] focus:outline-none focus:border-blue-500 cursor-pointer ${!idleLockEnabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <option value="1">1분 (1 min)</option>
                    <option value="2">2분 (2 mins)</option>
                    <option value="3">3분 (3 mins)</option>
                    <option value="5">5분 (5 mins - 기본)</option>
                    <option value="10">10분 (10 mins)</option>
                    <option value="15">15분 (15 mins)</option>
                    <option value="30">30분 (30 mins)</option>
                  </select>
                </div>
              </div>

              {/* 7. Real-time Update Section */}
              <div className="bg-gradient-to-r from-blue-950/40 to-indigo-950/40 p-3 rounded space-y-2 border border-blue-500/30">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-blue-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                    7. GitHub 실시간 업데이트 & 버전 정보
                  </span>
                  <span className="font-mono font-bold text-blue-400">v{APP_VERSION}</span>
                </div>
                <div className="text-[11px] text-slate-300 leading-relaxed">
                  GitHub 공식 저장소의 최신 버전 태그와 배포 인스톨러(.exe)를 실시간으로 비교하고 업데이트합니다.
                </div>
                <button
                  onClick={() => {
                    setShowSettingsModal(false);
                    setShowUpdateModal(true);
                  }}
                  className="w-full py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded shadow transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>🚀 업데이트 알림 팝업창 열기 & 최신 확인</span>
                </button>
              </div>
            </div>
            <div className="bg-[#18181b] border-t border-[#27272a] px-3 py-2 flex items-center justify-end gap-2">
              <button
                onClick={() => {
                  setShowSettingsModal(false);
                  showInAppToast('환경설정이 안전하게 저장되었습니다.');
                }}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded text-xs"
              >
                확인 (적용)
              </button>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="px-3 py-1.5 bg-[#2b2b36] hover:bg-[#323240] text-slate-300 rounded text-xs"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Full-screen Desktop Session Lock Screen Overlay in Desktop View */}
      {isDesktopLocked && (
        <div className="fixed inset-0 z-[99999] bg-slate-950/90 backdrop-blur-md flex flex-col items-center justify-center p-6 text-white select-none">
          <div className="relative z-10 flex flex-col items-center text-center max-w-sm w-full p-8 rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <Lock className="w-8 h-8 animate-pulse" />
            </div>
            <div className="text-3xl font-mono font-bold text-slate-100">
              {new Date().toLocaleTimeString()}
            </div>
            <div className="px-3 py-1 bg-amber-500/20 border border-amber-500/40 rounded-full text-amber-300 text-xs font-bold">
              🔒 데스크톱 세션 잠김 (Idle Auto-Lock)
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              타이머 가동 중 {idleLockMinutes}분 동안 활동이 없어 화면이 자동으로 잠겼습니다.
            </p>
            <button
              onClick={() => {
                setIsDesktopLocked(false);
                lastUserActivityRef.current = Date.now();
                soundEngine.play(currentSoundTheme, 'actionSuccess');
                showInAppToast('🔓 데스크톱 세션 잠금이 정상 해제되었습니다.');
              }}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg shadow cursor-pointer transition-colors text-xs flex items-center justify-center gap-2"
            >
              <span>🔓 잠금 해제 (클릭 또는 Enter)</span>
            </button>
          </div>
        </div>
      )}

      {/* Global Real-time Update Modal */}
      <UpdateModal
        isOpen={showUpdateModal}
        onClose={() => setShowUpdateModal(false)}
        lang="ko"
      />
    </div>
  );
};

export default DesktopAppView;
