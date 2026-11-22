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
import { APP_VERSION, LabDevice, SoundTheme, ThemeType } from '../types';
import { soundEngine, SOUND_THEMES } from '../utils/soundEngine';
import { UpdateModal } from './GitHubUpdateBanner';
import BatteryHistoryChart from './BatteryHistoryChart';
import { LabNetworkFleetPanel, generate50LabPreset } from './LabNetworkFleetPanel';
import {
  AppLang,
  getInitialLanguage,
  saveLanguagePreference,
  clearLanguagePreference
} from '../utils/i18n';

export type DesktopWindowType = 'main' | 'network' | 'injector' | 'devices';

interface DesktopAppViewProps {
  onSwitchToWeb?: () => void;
  onOpenLicense?: () => void;
  isWebAvailable?: boolean;
  lang?: AppLang;
  onLangChange?: (lang: AppLang) => void;
  langSource?: 'auto' | 'manual';
  onResetLangAuto?: () => void;
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
  theme?: ThemeType;
  onThemeChange?: (theme: ThemeType) => void;
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
  lang: propLang,
  onLangChange,
  langSource: propLangSource,
  onResetLangAuto,
  battery,
  isPowerSavingActive = false,
  soundTheme: propSoundTheme,
  onSoundThemeChange,
  soundVolume: propSoundVolume,
  onSoundVolumeChange,
  hourlyChime: propHourlyChime,
  onHourlyChimeChange,
  soundFeedbackEnabled: propSoundFeedbackEnabled,
  onSoundFeedbackChange,
  theme: propTheme,
  onThemeChange
}) => {
  const [currentLang, setCurrentLang] = useState<AppLang>(() => propLang || getInitialLanguage().lang);
  const [internalLangSource, setInternalLangSource] = useState<'auto' | 'manual'>(() => propLangSource || getInitialLanguage().source);

  useEffect(() => {
    if (propLang && propLang !== currentLang) {
      setCurrentLang(propLang);
    }
  }, [propLang]);

  useEffect(() => {
    if (propLangSource && propLangSource !== internalLangSource) {
      setInternalLangSource(propLangSource);
    }
  }, [propLangSource]);

  const isEn = currentLang === 'en';
  const L = (ko: string, en: string) => (isEn ? en : ko);

  const handleDesktopLangSwitch = (nextLang: AppLang) => {
    setCurrentLang(nextLang);
    setInternalLangSource('manual');
    saveLanguagePreference(nextLang);
    onLangChange?.(nextLang);
    showInAppToast(nextLang === 'en' ? 'Language switched to English (EN).' : '언어가 한국어(KO)로 변경되었습니다.');
  };

  const handleDesktopLangAutoReset = () => {
    if (onResetLangAuto) {
      onResetLangAuto();
      setInternalLangSource('auto');
      return;
    }
    const detected = clearLanguagePreference();
    setCurrentLang(detected);
    setInternalLangSource('auto');
    onLangChange?.(detected);
    showInAppToast(
      detected === 'en'
        ? 'Browser language auto-detected: English (EN)'
        : '브라우저 기본 언어로 자동 감지됨: 한국어 (KO)'
    );
  };

  const [currentTheme, setCurrentTheme] = useState<ThemeType>(() => {
    if (propTheme) return propTheme;
    try {
      const saved = localStorage.getItem('power_theme');
      return (saved as ThemeType) || 'beige';
    } catch {
      return 'beige';
    }
  });

  useEffect(() => {
    if (propTheme && propTheme !== currentTheme) {
      setCurrentTheme(propTheme);
    }
  }, [propTheme]);

  const isLight = currentTheme === 'white' || currentTheme === 'beige';
  const isDark = currentTheme === 'dark';
  const isGray = currentTheme === 'gray';
  const isWhite = currentTheme === 'white';
  const isBeige = currentTheme === 'beige';

  const windowBg = isDark ? 'bg-[#181a24] text-[#e1e4ed] border-[#2d3142]' 
    : isGray ? 'bg-[#334155] text-[#f8fafc] border-[#475569]'
    : isWhite ? 'bg-[#ffffff] text-[#0f172a] border-[#cbd5e1]'
    : 'bg-[#faf6ee] text-[#2c2217] border-[#c8bcaa]';

  const titleBarBg = isDark ? 'bg-[#11131a] border-[#2b2f3d] text-gray-100'
    : isGray ? 'bg-[#1e293b] border-[#475569] text-white'
    : isWhite ? 'bg-[#f1f5f9] border-[#cbd5e1] text-[#0f172a]'
    : 'bg-[#ebe2d4] border-[#c8bcaa] text-[#2c2217]';

  const panelBg = isDark ? 'bg-[#18181b] border-[#27272a] text-slate-200'
    : isGray ? 'bg-[#1e293b] border-[#475569] text-slate-100'
    : isWhite ? 'bg-[#f8fafc] border-[#cbd5e1] text-[#0f172a]'
    : 'bg-[#eee7da] border-[#c8bcaa] text-[#2c2217]';

  const cardBg = isDark ? 'bg-[#24242e] border-[#3f3f46] text-slate-100'
    : isGray ? 'bg-[#273142] border-[#475569] text-slate-100'
    : isWhite ? 'bg-white border-[#cbd5e1] text-[#0f172a]'
    : 'bg-white border-[#c8bcaa] text-[#2c2217]';

  const primaryText = isDark ? 'text-slate-100'
    : isGray ? 'text-slate-100'
    : isWhite ? 'text-[#0f172a]'
    : 'text-[#2c2217]';

  const secondaryText = isDark ? 'text-slate-400'
    : isGray ? 'text-slate-300'
    : isWhite ? 'text-slate-600'
    : 'text-[#5c4d38]';

  const inputFieldBg = isDark ? 'bg-[#2b2b36] border-[#3f3f46] text-white'
    : isGray ? 'bg-[#1e293b] border-[#475569] text-white'
    : isWhite ? 'bg-white border-[#cbd5e1] text-[#0f172a]'
    : 'bg-white border-[#c8bcaa] text-[#2c2217]';

  const subtleBtnBg = isDark ? 'bg-[#2b2b36] hover:bg-[#353544] text-slate-200 border-[#3f3f46]'
    : isGray ? 'bg-[#273142] hover:bg-[#344156] text-slate-100 border-[#475569]'
    : isWhite ? 'bg-slate-200/80 hover:bg-slate-300/80 text-slate-800 border-[#cbd5e1]'
    : 'bg-[#e8ded0] hover:bg-[#ded1c0] text-[#3d3222] border-[#c8bcaa]';

  const subtleDivider = isDark ? 'border-[#27272a]'
    : isGray ? 'border-[#475569]'
    : isWhite ? 'border-[#cbd5e1]'
    : 'border-[#c8bcaa]';
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
        showInAppToast(L(`🔔 정각 알림 (${now.getHours()}시 정각)`, `🔔 Hourly Chime (${now.getHours()}:00)`));
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [currentHourlyChime, currentSoundTheme, isEn]);

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
        showInAppToast(
          L(
            `🔒 유휴 상태 감지(${idleLockMinutes}분): 데스크톱 세션을 안전하게 잠갔습니다.`,
            `🔒 Idle timeout (${idleLockMinutes}m): Desktop session locked safely.`
          )
        );
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
  }, [idleLockEnabled, idleLockMinutes, isTimerRunning, isDesktopLocked, currentSoundTheme, isEn]);

  // Keydown unlock listener in Desktop App View
  useEffect(() => {
    if (!isDesktopLocked) return;
    const handleUnlockKey = (e: KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Escape') {
        setIsDesktopLocked(false);
        lastUserActivityRef.current = Date.now();
        soundEngine.play(currentSoundTheme, 'actionSuccess');
        showInAppToast(L('🔓 데스크톱 세션 잠금이 정상 해제되었습니다.', '🔓 Desktop session unlocked successfully.'));
      }
    };
    window.addEventListener('keydown', handleUnlockKey);
    return () => window.removeEventListener('keydown', handleUnlockKey);
  }, [isDesktopLocked, currentSoundTheme, isEn]);

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
    const matchedName = isEn ? matched?.nameEn : matched?.nameKo;
    showInAppToast(
      L(`[${matchedName || themeId}] 알림음 테마가 적용되었습니다.`, `Alert sound theme applied: [${matchedName || themeId}]`)
    );
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
      showInAppToast(L('🔇 모든 효과음 및 알림이 음소거되었습니다 (볼륨 0%).', '🔇 All sounds and alerts muted (0%).'));
    } else {
      const restoreVol = prevSoundVolume > 0 ? prevSoundVolume : 80;
      handleVolumeChange(restoreVol);
      showInAppToast(L(`🔊 사운드 볼륨이 ${restoreVol}%로 원복되었습니다.`, `🔊 Sound volume restored to ${restoreVol}%.`));
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
      showInAppToast(L('매시 정각 시계탑 차임벨이 활성화되었습니다.', 'Hourly clock tower chime enabled.'));
    } else {
      showInAppToast(L('정각 차임벨이 비활성화되었습니다.', 'Hourly chime disabled.'));
    }
  };

  // Schedule rules (bilingual defaults synced to active language)
  const buildDefaultRules = (targetLang: AppLang): ScheduleRuleItem[] =>
    targetLang === 'en'
      ? [
          { id: '1', name: '🏢 Weekday End-of-Day Auto Shutdown', mode: 'shutdown', time: '18:30', days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], enabled: true, forceClose: true },
          { id: '2', name: '🌙 Late Night Auto Shutdown', mode: 'shutdown', time: '23:30', days: ['Daily'], enabled: true, forceClose: true },
          { id: '3', name: '☕ Lunch Break Sleep Mode', mode: 'sleep', time: '12:00', days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], enabled: false, forceClose: false },
          { id: '4', name: '🔄 Monday Morning Scheduled Reboot', mode: 'restart', time: '08:30', days: ['Mon'], enabled: true, forceClose: true }
        ]
      : [
          { id: '1', name: '🏢 정시 퇴근 자동 종료', mode: 'shutdown', time: '18:30', days: ['월', '화', '수', '목', '금'], enabled: true, forceClose: true },
          { id: '2', name: '🌙 야간 심야 자동 종료', mode: 'shutdown', time: '23:30', days: ['매일'], enabled: true, forceClose: true },
          { id: '3', name: '☕ 점심시간 절전 모드', mode: 'sleep', time: '12:00', days: ['월', '화', '수', '목', '금'], enabled: false, forceClose: false },
          { id: '4', name: '🔄 월요일 아침 정기 리부팅', mode: 'restart', time: '08:30', days: ['월'], enabled: true, forceClose: true }
        ];

  const [rules, setRules] = useState<ScheduleRuleItem[]>(() => buildDefaultRules(currentLang));

  // New rule form
  const [newRuleName, setNewRuleName] = useState(() => (currentLang === 'en' ? 'Night Auto Shutdown' : '야간 자동 종료'));
  const [newRuleTime, setNewRuleTime] = useState('23:00');
  const [newRuleMode, setNewRuleMode] = useState<'shutdown' | 'restart' | 'sleep' | 'screenoff' | 'logout' | 'alarm'>('shutdown');

  const buildDefaultLogs = (targetLang: AppLang): string[] =>
    targetLang === 'en'
      ? [
          `[2026-09-29 19:30:00] [PowerCoreNative.dll] Native C module loaded (precision timer & sleep guard active)`,
          `[2026-09-29 19:30:00] [NetBeaconEngine.dll] Winsock2 non-blocking UDP beacon listener started (port 9986, 512-slot ring buffer)`,
          `[2026-09-29 19:30:00] [FirewallNative.dll] Windows Firewall COM rule verification completed (0.05s transaction)`,
          `[2026-09-29 19:30:00] [SysPowerHook.dll] Windows session notification hooks registered (lock & battery monitor active)`,
          `[2026-09-29 19:30:00] [ScheduleCrypto.dll] HMAC-SHA256 signature & encrypted envelope engine ready`,
          `[2026-09-29 19:30:00] Remote receiver server active: listening on TCP port 9988 for remote schedule rules...`,
          `[2026-09-29 19:30:01] Local config loaded: %APPDATA%\\PowerController\\power_timer_settings.json`
        ]
      : [
          `[2026-09-29 19:30:00] [PowerCoreNative.dll] C 네이티브 모듈 로드 완료 (초정밀 대기 타이머 및 절전 락 가동)`,
          `[2026-09-29 19:30:00] [NetBeaconEngine.dll] Winsock2 논블로킹 UDP 비콘 리스너 시작 (포트 9986, 512 슬롯 링버퍼)`,
          `[2026-09-29 19:30:00] [FirewallNative.dll] Windows 방화벽 COM 규칙 일괄 검증 완료 (0.05초 트랜잭션)`,
          `[2026-09-29 19:30:00] [SysPowerHook.dll] Windows 세션 알림 훅 등록 완료 (화면 잠금 및 배터리 감시 활성)`,
          `[2026-09-29 19:30:00] [ScheduleCrypto.dll] HMAC-SHA256 디지털 서명 및 암호화 봉투 엔진 준비 완료`,
          `[2026-09-29 19:30:00] 네트워크 수신 서버 시작: 포트 9988에서 원격 스케줄 규칙 대기 중...`,
          `[2026-09-29 19:30:01] 로컬 설정 파일 로드 성공: %APPDATA%\\PowerController\\power_timer_settings.json`
        ];

  // Logs
  const [logs, setLogs] = useState<string[]>(() => buildDefaultLogs(currentLang));

  // Network Scheduler / 50-PC Lab Fleet states
  const [labDevices, setLabDevices] = useState<LabDevice[]>(() => generate50LabPreset('192.168.10.', 101, 10));
  const [selectedDeviceIPs, setSelectedDeviceIPs] = useState<string[]>(['192.168.10.101', '192.168.10.102', '192.168.10.103']);
  const [remoteControlLogs, setRemoteControlLogs] = useState<string[]>(() => [
    currentLang === 'en'
      ? `[${new Date().toLocaleTimeString('en-US')}] [NetBeaconEngine] Remote control panel ready (awaiting command dispatch)`
      : `[${new Date().toLocaleTimeString('ko-KR')}] [NetBeaconEngine] 원격 제어판 초기화 완료 (선택된 디바이스 대상 명령 송출 대기 중)`
  ]);

  // Synchronize default preset rules & default log strings when language changes
  useEffect(() => {
    setRules(prev => {
      const defaults = buildDefaultRules(currentLang);
      const isDefaultIds = prev.length === 4 && prev.every((r, idx) => r.id === String(idx + 1));
      return isDefaultIds ? defaults : prev;
    });
    setNewRuleName(prev =>
      prev === '야간 자동 종료' || prev === 'Night Auto Shutdown'
        ? currentLang === 'en'
          ? 'Night Auto Shutdown'
          : '야간 자동 종료'
        : prev
    );
    setLogs(prev => {
      if (prev.length === 7 && prev[0].includes('PowerCoreNative.dll')) {
        return buildDefaultLogs(currentLang);
      }
      return prev;
    });
    setRemoteControlLogs(prev => {
      if (prev.length === 1 && prev[0].includes('[NetBeaconEngine]')) {
        return [
          currentLang === 'en'
            ? `[${new Date().toLocaleTimeString('en-US')}] [NetBeaconEngine] Remote control panel ready (awaiting command dispatch)`
            : `[${new Date().toLocaleTimeString('ko-KR')}] [NetBeaconEngine] 원격 제어판 초기화 완료 (선택된 디바이스 대상 명령 송출 대기 중)`
        ];
      }
      return prev;
    });
  }, [currentLang]);

  // Countdown effect (pure interval decrement; audio & completion handled outside state updater)
  const prevDesktopSecRef = useRef<number>(remainingSeconds);
  useEffect(() => {
    if (!isTimerRunning) {
      prevDesktopSecRef.current = remainingSeconds;
      return;
    }
    prevDesktopSecRef.current = remainingSeconds;
    const interval = setInterval(() => {
      setRemainingSeconds(prev => (prev <= 1 ? 0 : prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [isTimerRunning]);

  useEffect(() => {
    if (!isTimerRunning) {
      prevDesktopSecRef.current = remainingSeconds;
      return;
    }
    const prevSec = prevDesktopSecRef.current;
    if (remainingSeconds === prevSec) return;
    prevDesktopSecRef.current = remainingSeconds;

    if (remainingSeconds <= 0) {
      setIsTimerRunning(false);
      triggerActionDone();
      return;
    }
    if ((remainingSeconds <= 10 && remainingSeconds > 0) || remainingSeconds === 30 || remainingSeconds === 60) {
      playSoundEffect('warningTick');
    }
  }, [isTimerRunning, remainingSeconds, currentSoundTheme, soundFeedbackEnabled, powerMode, forceClose, isEn]);

  const triggerActionDone = () => {
    const timestamp = new Date().toLocaleTimeString(isEn ? 'en-US' : 'ko-KR');
    setLogs(prev => [
      isEn
        ? `[${timestamp}] ⚡ [Timer Executed] Mode '${powerMode}' executed cleanly. (Force Close: ${forceClose ? '/f' : 'off'})`
        : `[${timestamp}] ⚡ [타이머 실행] 모드 '${powerMode}' 명령이 성공적으로 실행되었습니다. (강제 닫기: ${forceClose ? '/f' : '없음'})`,
      ...prev
    ]);
    if (powerMode === 'alarm') {
      soundEngine.play(currentSoundTheme, 'timerAlarm');
    } else {
      soundEngine.play(currentSoundTheme, 'actionSuccess');
    }
    showInAppToast(L(`⚡ [완료] ${powerMode} 동작이 실행되었습니다!`, `⚡ [Completed] Action '${powerMode}' executed!`));
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
    let targetTotal = remainingSeconds;
    let scheduleLabel = '';

    if (runType === 'timer') {
      const total = inputH * 3600 + inputM * 60 + inputS;
      if (total <= 0) {
        showInAppToast(L('⚠️ 타이머 시간을 1초 이상 입력해 주세요.', '⚠️ Please enter at least 1 second.'));
        playSoundEffect('buttonClick');
        return;
      }
      targetTotal = total;
      setRemainingSeconds(total);
    } else {
      if (inputH < 0 || inputH > 23 || inputM < 0 || inputM > 59) {
        showInAppToast(L('⚠️ 시는 0~23, 분은 0~59 사이로 입력해 주세요.', '⚠️ Enter hours 0-23 and minutes 0-59.'));
        playSoundEffect('buttonClick');
        return;
      }
      const now = new Date();
      const targetTime = new Date(now);
      targetTime.setHours(inputH, inputM, 0, 0);
      if (targetTime.getTime() <= now.getTime()) {
        targetTime.setDate(targetTime.getDate() + 1);
      }
      targetTotal = Math.max(1, Math.floor((targetTime.getTime() - now.getTime()) / 1000));
      scheduleLabel = targetTime.toLocaleTimeString(isEn ? 'en-US' : 'ko-KR', { hour: '2-digit', minute: '2-digit' });
      setRemainingSeconds(targetTotal);
    }

    setIsTimerRunning(true);
    playSoundEffect('actionSuccess');
    const timestamp = new Date().toLocaleTimeString(isEn ? 'en-US' : 'ko-KR');
    setLogs(prev => [
      runType === 'schedule'
        ? isEn
          ? `[${timestamp}] ⏰ Schedule Started: [Target: ${scheduleLabel}] [Mode: ${powerMode}] [Countdown: ${formatDigitalTime(targetTotal)}] [Force: ${forceClose ? '/f' : 'off'}]`
          : `[${timestamp}] ⏰ 정시 예약 시작: [목표: ${scheduleLabel}] [모드: ${powerMode}] [남은시간: ${formatDigitalTime(targetTotal)}] [강제종료: ${forceClose ? '/f' : '미적용'}]`
        : isEn
        ? `[${timestamp}] ▶ Timer Started: [Mode: ${powerMode}] [Remaining: ${formatDigitalTime(targetTotal)}] [Force: ${forceClose ? '/f' : 'off'}]`
        : `[${timestamp}] ▶ 타이머 시작: [모드: ${powerMode}] [남은시간: ${formatDigitalTime(targetTotal)}] [강제종료: ${forceClose ? '/f' : '미적용'}]`,
      ...prev
    ]);
    showInAppToast(
      runType === 'schedule'
        ? L(`⏰ ${scheduleLabel} 예약 타이머가 시작되었습니다.`, `⏰ Scheduled for ${scheduleLabel}.`)
        : L('▶ 타이머가 시작되었습니다.', '▶ Timer started.')
    );
  };

  const stopTimer = () => {
    setIsTimerRunning(false);
    playSoundEffect('buttonClick');
    const timestamp = new Date().toLocaleTimeString(isEn ? 'en-US' : 'ko-KR');
    setLogs(prev => [
      isEn ? `[${timestamp}] ⏹ Timer paused/stopped` : `[${timestamp}] ⏹ 타이머 일시 정지/중지됨`,
      ...prev
    ]);
    showInAppToast(L('⏹ 타이머가 정지되었습니다.', '⏹ Timer stopped.'));
  };

  const resetTimer = () => {
    setIsTimerRunning(false);
    playSoundEffect('buttonClick');
    const total = inputH * 3600 + inputM * 60 + inputS;
    setRemainingSeconds(total > 0 ? total : 30 * 60);
    showInAppToast(L('🔄 타이머가 초기화되었습니다.', '🔄 Timer reset.'));
  };

  const addPresetTime = (sec: number) => {
    playSoundEffect('buttonClick');
    setRemainingSeconds(prev => prev + sec);
    showInAppToast(
      isEn
        ? `Added +${sec >= 3600 ? `${sec / 3600}h` : `${sec / 60}m`}.`
        : `+${sec >= 3600 ? `${sec / 3600}시간` : `${sec / 60}분`} 추가되었습니다.`
    );
  };

  const addScheduleRule = () => {
    if (!newRuleName.trim()) return;
    playSoundEffect('actionSuccess');
    const newRule: ScheduleRuleItem = {
      id: Date.now().toString(),
      name: newRuleName,
      mode: newRuleMode,
      time: newRuleTime,
      days: [L('매일', 'Daily')],
      enabled: true,
      forceClose: true
    };
    setRules(prev => [...prev, newRule]);
    setNewRuleName('');
    showInAppToast(L(`📅 '${newRule.name}' 스케줄이 등록되었습니다.`, `📅 Rule '${newRule.name}' registered.`));
    setLogs(prev => [
      isEn
        ? `[${new Date().toLocaleTimeString('en-US')}] 📅 New schedule rule added: ${newRule.name} (${newRule.time})`
        : `[${new Date().toLocaleTimeString('ko-KR')}] 📅 신규 스케줄 등록: ${newRule.name} (${newRule.time})`,
      ...prev
    ]);
  };

  const deleteScheduleRule = (id: string) => {
    playSoundEffect('buttonClick');
    setRules(prev => prev.filter(r => r.id !== id));
    showInAppToast(L('🗑️ 스케줄 규칙이 삭제되었습니다.', '🗑️ Schedule rule deleted.'));
  };

  const toggleRuleEnabled = (id: string) => {
    setRules(prev => prev.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r));
  };

  const desktopBg = isDark ? 'bg-slate-950 text-slate-100'
    : isGray ? 'bg-slate-900 text-slate-100'
    : isWhite ? 'bg-slate-100 text-[#0f172a]'
    : 'bg-[#f5f0e6] text-[#2c2217]';

  return (
    <div className={`min-h-screen ${desktopBg} flex flex-col font-sans select-none antialiased`}>
      {/* Top Application Control Toolbar (Desktop OS Environment Simulation) */}
      <header className={`border-b px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs shadow-md ${titleBarBg}`}>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-600/20 border border-blue-500/40 rounded text-blue-400 font-bold whitespace-nowrap">
            <Monitor className="w-3.5 h-3.5" />
            <span>{L('Windows Desktop Native View (Tkinter GUI 미러링)', 'Windows Desktop Native View (Tkinter Mirror)')}</span>
          </div>
          <span className="text-slate-400 hidden sm:inline">|</span>
          <span className="text-slate-400 hidden xl:inline">
            {L('단독 실행형 Windows C/Python 애플리케이션 화면', 'Standalone Windows C/Python Application')}
          </span>
        </div>

        {/* Program Switcher Tabs */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-md border border-slate-800 flex-wrap">
          <button
            onClick={() => {
              setActiveApp('main');
              playSoundEffect('buttonClick');
            }}
            className={`px-3 py-1 rounded font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
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
            className={`px-3 py-1 rounded font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
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
              setActiveApp('devices');
              playSoundEffect('buttonClick');
            }}
            className={`px-3 py-1 rounded font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              activeApp === 'devices'
                ? 'bg-blue-600 text-white shadow-sm font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Cpu className="w-3 h-3 text-emerald-400" />
            <span>DeviceController.exe</span>
          </button>
          <button
            onClick={() => {
              setActiveApp('injector');
              playSoundEffect('buttonClick');
            }}
            className={`px-3 py-1 rounded font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
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
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-950/80 border border-slate-800 rounded text-slate-200 shadow-inner whitespace-nowrap"
            title={
              isEn
                ? `Battery: ${battery.level}% (${battery.charging ? 'Charging' : 'On Battery'})`
                : `배터리 상태: ${battery.level}% (${battery.charging ? '충전 중' : '배터리 사용 중'})`
            }
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
            <span className="font-mono font-bold text-xs tabular-nums">{battery.level}%</span>
            <span className={`text-[10px] px-1 py-0.2 rounded font-semibold ${
              battery.charging
                ? 'bg-emerald-500/20 text-emerald-400'
                : battery.level <= 20
                ? 'bg-rose-500/20 text-rose-400'
                : 'bg-slate-800 text-slate-300'
            }`}>
              {battery.charging ? L('충전중', 'Charging') : L('배터리', 'Battery')}
            </span>
            {isPowerSavingActive && (
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-1 py-0.2 rounded font-bold flex items-center gap-0.5 animate-pulse">
                {L('🍃 절전 중', '🍃 Eco')}
              </span>
            )}
          </div>
        )}

        {/* Language Auto/Manual Toggle & Sound Controller */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {/* Manual Language Switcher (with Auto indicator) */}
          <div
            className="flex items-center bg-slate-950/90 border border-slate-800 rounded p-0.5 shadow-inner"
            title={
              internalLangSource === 'auto'
                ? L('브라우저 기본 언어 자동 감지됨 (클릭하여 수동 변경)', 'Auto-detected from browser locale (click to toggle)')
                : L('수동 선택된 언어', 'Manually selected language')
            }
          >
            <button
              type="button"
              onClick={() => handleDesktopLangSwitch('ko')}
              className={`px-2 py-0.5 rounded text-[11px] font-bold transition-colors cursor-pointer whitespace-nowrap ${
                currentLang === 'ko' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              KO
            </button>
            <button
              type="button"
              onClick={() => handleDesktopLangSwitch('en')}
              className={`px-2 py-0.5 rounded text-[11px] font-bold transition-colors cursor-pointer whitespace-nowrap ${
                currentLang === 'en' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              EN
            </button>
            <span className="px-1.5 text-[10px] text-slate-400 font-mono whitespace-nowrap">
              {internalLangSource === 'auto' ? 'Auto' : 'Manual'}
            </span>
          </div>

          <button
            onClick={() => {
              playSoundEffect('buttonClick');
              setShowSettingsModal(true);
            }}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-950/80 hover:bg-slate-800 border border-slate-800 rounded text-slate-200 text-xs transition-colors cursor-pointer shadow-inner whitespace-nowrap"
            title={L('알림음 테마 및 환경설정 열기', 'Open Sound & App Settings')}
          >
            {currentSoundVolume === 0 ? (
              <VolumeX className="w-3.5 h-3.5 text-rose-400" />
            ) : currentSoundVolume < 50 ? (
              <Volume1 className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
            )}
            <span className="font-semibold text-emerald-300 hidden sm:inline">
              {(isEn
                ? SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameEn
                : SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameKo) || L('클래식 벨', 'Classic Bell')}
            </span>
            <span className="font-mono text-[11px] text-slate-400 font-bold tabular-nums">
              {currentSoundVolume}%
            </span>
          </button>

          <button
            onClick={handleToggleMuteAllDesktop}
            className={`px-2 py-1 rounded text-xs font-bold transition-all cursor-pointer flex items-center gap-1 border shadow-sm whitespace-nowrap ${
              currentSoundVolume === 0
                ? 'bg-rose-500/25 text-rose-300 border-rose-500/50 hover:bg-rose-500/35 animate-pulse'
                : 'bg-slate-950/80 hover:bg-slate-800 text-slate-300 border-slate-800'
            }`}
            title={
              currentSoundVolume === 0
                ? L(`음소거 해제 (${prevSoundVolume}% 복원)`, `Unmute (${prevSoundVolume}%)`)
                : L('모든 효과음 즉시 음소거 (0%)', 'Mute all sounds (0%)')
            }
          >
            <VolumeX className="w-3.5 h-3.5 text-rose-400" />
            <span>{currentSoundVolume === 0 ? L('음소거중 (0%)', 'Muted (0%)') : L('음소거', 'Mute')}</span>
          </button>
        </div>

        {/* Web Switcher, Update Button & License Button */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowUpdateModal(true)}
            className="px-2.5 py-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded shadow flex items-center gap-1.5 transition-all text-xs cursor-pointer whitespace-nowrap"
            title={L('업데이트 알림 팝업 및 최신 릴리스 정보 확인', 'Check updates & release notes')}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>{L('🚀 업데이트 확인', '🚀 Updates')}</span>
          </button>
          {onOpenLicense && (
            <button
              onClick={onOpenLicense}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 flex items-center gap-1 transition-colors text-xs cursor-pointer whitespace-nowrap"
            >
              <FileText className="w-3 h-3 text-emerald-400" />
              <span>{L('약관/라이선스 (한/영)', 'License (KO/EN)')}</span>
            </button>
          )}
          {isWebAvailable && onSwitchToWeb && (
            <button
              onClick={onSwitchToWeb}
              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded shadow transition-colors flex items-center gap-1 text-xs cursor-pointer whitespace-nowrap"
            >
              <span>{L('🌐 모던 웹 대시보드로 보기', '🌐 Open Web Dashboard')}</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Desktop Workspace Area */}
      <main className={`flex-1 p-3 sm:p-6 flex items-center justify-center overflow-y-auto ${desktopBg}`}>
        {/* ========================================================================= */}
        {/* WINDOW 1: PowerController.exe (Main Desktop Native Tkinter App)           */}
        {/* ========================================================================= */}
        {activeApp === 'main' && (
          <div
            className={`w-full max-w-[540px] rounded shadow-2xl overflow-hidden flex flex-col transition-all duration-200 border ${windowBg} ${
              isWindowMaximized ? 'fixed inset-3 max-w-none z-40 overflow-y-auto' : ''
            }`}
            style={{ fontFamily: "'Malgun Gothic', 'Segoe UI', Arial, sans-serif" }}
          >
            {/* Windows OS Title Bar */}
            <div className={`border-b px-3 py-2 flex items-center justify-between text-xs select-none ${titleBarBg}`}>
              <div className={`flex items-center gap-2 font-bold ${primaryText}`}>
                <div className="w-5 h-5 rounded-md overflow-hidden ring-1 ring-cyan-500/40 shadow-sm flex items-center justify-center bg-slate-950 flex-shrink-0">
                  <img src="/PowerController.png" alt="App Logo" className="w-full h-full object-cover scale-105" />
                </div>
                <span>{L(`PowerController v${APP_VERSION} - PC 자동 전원 관리`, `PowerController v${APP_VERSION} - PC Power Manager`)}</span>
              </div>
              <div className={`flex items-center gap-2 ${secondaryText}`}>
                {/* Dedicated Mute All Button in Title Bar */}
                <button
                  onClick={handleToggleMuteAllDesktop}
                  className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer flex items-center gap-1 border whitespace-nowrap ${
                    currentSoundVolume === 0
                      ? 'bg-rose-500/20 text-rose-400 border-rose-500/50 hover:bg-rose-500/30 animate-pulse'
                      : subtleBtnBg
                  }`}
                  title={
                    currentSoundVolume === 0
                      ? L(`음소거 해제 (${prevSoundVolume}% 복원)`, `Unmute (${prevSoundVolume}%)`)
                      : L('모든 사운드 즉시 음소거 (0%)', 'Mute all sounds (0%)')
                  }
                >
                  <VolumeX className="w-3 h-3 text-rose-400" />
                  <span>{currentSoundVolume === 0 ? L('음소거중', 'Muted') : L('음소거', 'Mute')}</span>
                </button>

                <div className={`flex items-center gap-1 border-l pl-1.5 ${subtleDivider}`}>
                  <button
                    onClick={() => setIsMinimized(!isMinimized)}
                    className={`w-7 h-5 flex items-center justify-center rounded ${isLight ? 'hover:bg-black/10' : 'hover:bg-[#27272a] hover:text-white'}`}
                    title={L('최소화', 'Minimize')}
                  >
                    <span className="mb-2 font-bold text-xs">—</span>
                  </button>
                <button
                  onClick={() => setIsWindowMaximized(!isWindowMaximized)}
                  className={`w-7 h-5 flex items-center justify-center rounded ${isLight ? 'hover:bg-black/10' : 'hover:bg-[#27272a] hover:text-white'}`}
                  title={L('최대화', 'Maximize')}
                >
                  <span className="text-[10px]">□</span>
                </button>
                <button
                  onClick={() => showInAppToast(L('트레이로 최소화되었습니다. (Windows 백그라운드 상주)', 'Minimized to system tray (background service active).'))}
                  className="w-7 h-5 flex items-center justify-center hover:bg-red-600 hover:text-white rounded transition-colors"
                  title={L('닫기 (트레이 보관)', 'Close to Tray')}
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

            {/* Native Creative DLL Status Bar Badge */}
            <div className={`px-3 py-1.5 border-b flex items-center justify-between text-[11px] ${panelBg}`}>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className={`font-semibold ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                  {L('5-Tier 순수 창작 C/C++ DLL 가동 중', '5-Tier Custom C/C++ DLLs Active')}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[10px] hidden sm:flex">
                <span className={`px-1.5 py-0.5 rounded border ${cardBg}`}>PowerCoreNative</span>
                <span className={`px-1.5 py-0.5 rounded border ${cardBg}`}>NetBeacon</span>
                <span className={`px-1.5 py-0.5 rounded border ${cardBg}`}>FirewallNative</span>
                <span className={`px-1.5 py-0.5 rounded border ${cardBg}`}>SysPowerHook</span>
                <span className={`px-1.5 py-0.5 rounded border ${cardBg}`}>ScheduleCrypto</span>
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
              <div className={`border p-2.5 rounded space-y-1.5 ${panelBg}`}>
                {/* Row 1 */}
                <div className="flex items-center justify-between">
                  <label className={`flex items-center gap-2 cursor-pointer font-bold ${primaryText}`}>
                    <input
                      type="checkbox"
                      checked={isPinned}
                      onChange={e => setIsPinned(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>{L('📌 상단 고정', '📌 Always on Top')}</span>
                  </label>
                  <button
                    onClick={() => {
                      setActiveTab('scheduler');
                      showInAppToast(L('스케줄러 탭으로 전환되었습니다.', 'Switched to Scheduler tab.'));
                    }}
                    className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold transition-colors cursor-pointer whitespace-nowrap"
                  >
                    {L('🖥️ 스케줄러 팝업창 열기', '🖥️ Open Task Scheduler')}
                  </button>
                </div>

                {/* Row 2 */}
                <div className="flex items-center justify-between">
                  <label className={`flex items-center gap-2 cursor-pointer font-bold ${primaryText}`}>
                    <input
                      type="checkbox"
                      checked={autoStart}
                      onChange={e => setAutoStart(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>{L('⚙️ 시작 시 자동 실행', '⚙️ Run on Startup')}</span>
                  </label>
                  <label className={`flex items-center gap-2 cursor-pointer font-bold ${primaryText}`}>
                    <input
                      type="checkbox"
                      checked={bootToTray}
                      onChange={e => setBootToTray(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>{L('📥 부팅 시 트레이', '📥 Boot to Tray')}</span>
                  </label>
                </div>

                {/* Row 3 */}
                <div className="flex items-center justify-between">
                  <label className={`flex items-center gap-2 cursor-pointer font-bold ${primaryText}`}>
                    <input
                      type="checkbox"
                      checked={minimizeToTray}
                      onChange={e => setMinimizeToTray(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>{L('📁 최소화 시 트레이', '📁 Minimize to Tray')}</span>
                  </label>
                  <label className={`flex items-center gap-2 cursor-pointer font-bold ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`} title={L('저장되지 않은 작업 강제 닫기', 'Force close unsaved apps')}>
                    <input
                      type="checkbox"
                      checked={forceClose}
                      onChange={e => setForceClose(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-emerald-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>{L('⚡ 강제 닫기 (/f)', '⚡ Force Close (/f)')}</span>
                  </label>
                </div>

                {/* Row 4 */}
                <div className={`flex items-center justify-between pt-0.5 border-t ${subtleDivider}`}>
                  <label className={`flex items-center gap-2 cursor-pointer font-bold ${isLight ? 'text-blue-700' : 'text-blue-400'}`}>
                    <input
                      type="checkbox"
                      checked={networkReceive}
                      onChange={e => setNetworkReceive(e.target.checked)}
                      className="rounded bg-[#27272a] border-[#3f3f46] text-blue-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                    <span>{L('📡 원격 예약 수신 허용 (포트 9988)', '📡 Remote Receiver (Port 9988)')}</span>
                  </label>
                  <span className={`text-[11px] ${secondaryText}`}>{L('보안 토큰 활성', 'Token Active')}</span>
                </div>
              </div>

              {/* Settings Toggle Button */}
              <button
                onClick={() => {
                  playSoundEffect('buttonClick');
                  setShowSettingsModal(true);
                }}
                className={`w-full py-2 font-bold rounded border flex items-center justify-center gap-2 transition-colors cursor-pointer ${subtleBtnBg}`}
              >
                <Settings className="w-4 h-4 text-blue-500" />
                <span>{L('⚙️ 설정 (Settings) ...', '⚙️ Settings & Preferences ...')}</span>
              </button>

              {/* 3 Tab Navigation Header Bar */}
              <div className={`flex items-center gap-1 border-b pb-1 ${subtleDivider}`}>
                <button
                  onClick={() => {
                    setActiveTab('control');
                    playSoundEffect('buttonClick');
                  }}
                  className={`flex-1 py-1.5 rounded text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer whitespace-nowrap border ${
                    activeTab === 'control'
                      ? 'bg-blue-600 text-white border-blue-600 shadow'
                      : subtleBtnBg
                  }`}
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span>{L('⏱ 간편 제어', '⏱ Quick Control')}</span>
                </button>
                <button
                  onClick={() => {
                    setActiveTab('scheduler');
                    playSoundEffect('buttonClick');
                  }}
                  className={`flex-1 py-1.5 rounded text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer whitespace-nowrap border ${
                    activeTab === 'scheduler'
                      ? 'bg-blue-600 text-white border-blue-600 shadow'
                      : subtleBtnBg
                  }`}
                >
                  <Calendar className="w-3.5 h-3.5" />
                  <span>{L('📅 스케줄러', '📅 Scheduler')}</span>
                </button>
                <button
                  onClick={() => {
                    setActiveTab('history');
                    playSoundEffect('buttonClick');
                  }}
                  className={`flex-1 py-1.5 rounded text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer whitespace-nowrap border ${
                    activeTab === 'history'
                      ? 'bg-blue-600 text-white border-blue-600 shadow'
                      : subtleBtnBg
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>{L('📋 동작 기록', '📋 Activity Logs')}</span>
                </button>
              </div>

              {/* ============================================================= */}
              {/* TAB 1: Control Tab (간편 제어)                                */}
              {/* ============================================================= */}
              {activeTab === 'control' && (
                <div className="space-y-3">
                  {/* Power Mode: Clean Dropdown/Pulldown Selector vs Grid Toggle */}
                  <div className="space-y-1.5">
                    <div className={`flex items-center justify-between text-[11px] font-semibold ${secondaryText}`}>
                      <div className="flex items-center gap-1.5">
                        <span>{L('⚡ 전원 동작 선택:', '⚡ Power Action:')}</span>
                        <span className={`font-bold ${isLight ? 'text-blue-600' : 'text-blue-400'}`}>
                          {powerMode === 'shutdown' && L('🛑 시스템 종료', '🛑 Shutdown')}
                          {powerMode === 'restart' && L('🔄 다시 시작', '🔄 Restart')}
                          {powerMode === 'sleep' && L('🌙 절전 모드', '🌙 Sleep Mode')}
                          {powerMode === 'screenoff' && L('📺 화면 끄기', '📺 Screen Off')}
                          {powerMode === 'logout' && L('🚪 로그아웃', '🚪 Sign Out')}
                          {powerMode === 'alarm' && L('🔔 알람 알림', '🔔 Alarm Only')}
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
                        className={`text-[10px] underline cursor-pointer transition-colors whitespace-nowrap ${secondaryText}`}
                        title={
                          powerModeDisplayMode === 'dropdown'
                            ? L('모든 버튼 그리드로 펼치기', 'Expand all action buttons into grid')
                            : L('드롭다운으로 화면을 깔끔하게 접기', 'Collapse into clean dropdown menu')
                        }
                      >
                        {powerModeDisplayMode === 'dropdown'
                          ? L('🔲 버튼 펼치기', '🔲 Expand Grid')
                          : L('📋 풀다운 깔끔 접기', '📋 Compact Dropdown')}
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
                              shutdown: L('시스템 종료', 'Shutdown'),
                              restart: L('다시 시작', 'Restart'),
                              sleep: L('절전 모드', 'Sleep'),
                              screenoff: L('화면 끄기', 'Screen Off'),
                              logout: L('로그아웃', 'Sign Out'),
                              alarm: L('알람 알림', 'Alarm Only'),
                            };
                            showInAppToast(
                              L(
                                `⚡ 전원 동작: [${labels[e.target.value] || e.target.value}] 설정 완료`,
                                `⚡ Power Action set to [${labels[e.target.value] || e.target.value}]`
                              )
                            );
                          }}
                          className={`w-full border hover:border-blue-500/70 rounded px-3 py-2 text-xs font-bold appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer pl-8 pr-8 shadow-inner ${inputFieldBg}`}
                        >
                          <option value="shutdown">{L('🛑 1. 시스템 종료 (Shutdown) - 모든 앱을 닫고 PC 전원을 완전히 끕니다', '🛑 1. Shutdown - Close all apps and power off PC')}</option>
                          <option value="restart">{L('🔄 2. 다시 시작 (Restart) - 운영체제를 안전하게 재부팅합니다', '🔄 2. Restart - Reboot operating system safely')}</option>
                          <option value="sleep">{L('🌙 3. 절전 모드 (Sleep) - 작업 상태를 RAM에 유지하고 저전력 대기로 전환', '🌙 3. Sleep - Keep session in RAM in low-power state')}</option>
                          <option value="screenoff">{L('📺 4. 화면 끄기 (Screen Off) - 백그라운드 유지 상태에서 모니터만 절전', '📺 4. Screen Off - Turn off monitor while running tasks')}</option>
                          <option value="logout">{L('🚪 5. 로그아웃 (Sign Out) - 현재 계정 세션을 안전하게 종료합니다', '🚪 5. Sign Out - Safely log off current user session')}</option>
                          <option value="alarm">{L('🔔 6. 알람 알림 (Alarm Only) - 전원 차단 없이 알림음과 팝업만 발생', '🔔 6. Alarm Only - Ring alert chime without power action')}</option>
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
                          { id: 'shutdown', label: L('종료', 'Shutdown'), icon: Power, color: 'bg-red-600 text-white' },
                          { id: 'restart', label: L('재시작', 'Restart'), icon: RotateCw, color: 'bg-orange-600 text-white' },
                          { id: 'sleep', label: L('절전', 'Sleep'), icon: Moon, color: 'bg-indigo-600 text-white' },
                          { id: 'screenoff', label: L('화면끔', 'Screen Off'), icon: Monitor, color: 'bg-purple-600 text-white' },
                          { id: 'logout', label: L('로그아웃', 'Sign Out'), icon: LogOut, color: 'bg-slate-700 text-white' },
                          { id: 'alarm', label: L('알람', 'Alarm'), icon: Bell, color: 'bg-yellow-600 text-white' }
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
                                  : subtleBtnBg
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
                      className={`py-1.5 rounded font-bold text-xs transition-colors cursor-pointer border ${
                        runType === 'timer'
                          ? 'bg-blue-600 text-white border-blue-600'
                          : subtleBtnBg
                      }`}
                    >
                      {L('⏳ 시간 타이머 (후)', '⏳ Countdown Timer')}
                    </button>
                    <button
                      onClick={() => {
                        setRunType('schedule');
                        if (inputH > 23) setInputH(23);
                        playSoundEffect('buttonClick');
                      }}
                      className={`py-1.5 rounded font-bold text-xs transition-colors cursor-pointer border ${
                        runType === 'schedule'
                          ? 'bg-blue-600 text-white border-blue-600'
                          : subtleBtnBg
                      }`}
                    >
                      {L('⏰ 특정 시각 예약 (정시)', '⏰ Specific Time')}
                    </button>
                  </div>

                  {/* Big Digital Display Counter (Tkinter Courier Font Display) */}
                  <div className={`border rounded py-4 px-3 text-center shadow-inner ${panelBg}`}>
                    <div className={`text-[11px] font-medium mb-1 ${secondaryText}`}>
                      {isTimerRunning
                        ? L('⚡ 카운트다운 진행 중...', '⚡ Countdown running...')
                        : runType === 'schedule'
                        ? L(
                            `⏰ 예약 목표 시각: ${String(Math.min(23, inputH)).padStart(2, '0')}:${String(Math.min(59, inputM)).padStart(2, '0')} (24시간제)`,
                            `⏰ Scheduled Target: ${String(Math.min(23, inputH)).padStart(2, '0')}:${String(Math.min(59, inputM)).padStart(2, '0')} (24h)`
                          )
                        : L('대기 상태 (시작 대기)', 'Standby (Ready to start)')}
                    </div>
                    <div
                      className={`text-4xl sm:text-5xl font-mono font-black tracking-wider ${isLight ? 'text-blue-600' : 'text-blue-400'}`}
                      style={{ fontFamily: "'Courier New', Courier, monospace" }}
                    >
                      {formatDigitalTime(remainingSeconds)}
                    </div>
                    <div className={`text-[11px] mt-1 ${secondaryText}`}>
                      {forceClose && (
                        <span className={`font-bold ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                          {L('⚡ 실행 중인 앱 강제 종료 (/f) 활성', '⚡ Force close running apps (/f) active')}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Spinbox Inputs (H / M / S) */}
                  <div className={`border p-3 rounded ${panelBg}`}>
                    <div className={`text-[11px] font-semibold mb-2 ${secondaryText}`}>
                      {runType === 'schedule'
                        ? L('[정시 예약] 지정한 24시간제 시각(시:분)에 동작을 수행합니다.', '[Specific Time] Execute power action at the target 24h clock time (H : M).')
                        : L('[타이머] 지정된 시간/분/초 후 동작을 수행합니다.', '[Timer] Execute power action after specified H / M / S.')}
                    </div>
                    <div className="flex items-center justify-center gap-4">
                      {/* Hour */}
                      <div className="flex flex-col items-center">
                        <span className={`text-[11px] mb-1 ${secondaryText}`}>
                          {runType === 'schedule' ? L('시 (0~23)', 'Hour (0-23)') : L('시 (H)', 'Hours (H)')}
                        </span>
                        <div className={`flex items-center border rounded ${inputFieldBg}`}>
                          <input
                            type="number"
                            min="0"
                            max={runType === 'schedule' ? 23 : 99}
                            value={inputH}
                            onChange={e => {
                              const maxH = runType === 'schedule' ? 23 : 99;
                              setInputH(Math.min(maxH, Math.max(0, parseInt(e.target.value) || 0)));
                            }}
                            className="w-12 text-center bg-transparent font-bold py-1 text-sm focus:outline-none"
                          />
                          <div className={`flex flex-col border-l ${subtleDivider}`}>
                            <button
                              onClick={() => setInputH(prev => Math.min(runType === 'schedule' ? 23 : 99, prev + 1))}
                              className={`px-1 ${isLight ? 'hover:bg-black/10 text-slate-700' : 'hover:bg-[#3f3f46] text-slate-300'}`}
                            >
                              <ChevronUp className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => setInputH(prev => Math.max(0, prev - 1))}
                              className={`px-1 ${isLight ? 'hover:bg-black/10 text-slate-700' : 'hover:bg-[#3f3f46] text-slate-300'}`}
                            >
                              <ChevronDown className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Minute */}
                      <div className="flex flex-col items-center">
                        <span className={`text-[11px] mb-1 ${secondaryText}`}>{L('분 (M)', 'Mins (M)')}</span>
                        <div className={`flex items-center border rounded ${inputFieldBg}`}>
                          <input
                            type="number"
                            min="0"
                            max="59"
                            value={inputM}
                            onChange={e => setInputM(Math.min(59, Math.max(0, parseInt(e.target.value) || 0)))}
                            className="w-12 text-center bg-transparent font-bold py-1 text-sm focus:outline-none"
                          />
                          <div className={`flex flex-col border-l ${subtleDivider}`}>
                            <button
                              onClick={() => setInputM(prev => Math.min(59, prev + 1))}
                              className={`px-1 ${isLight ? 'hover:bg-black/10 text-slate-700' : 'hover:bg-[#3f3f46] text-slate-300'}`}
                            >
                              <ChevronUp className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => setInputM(prev => Math.max(0, prev - 1))}
                              className={`px-1 ${isLight ? 'hover:bg-black/10 text-slate-700' : 'hover:bg-[#3f3f46] text-slate-300'}`}
                            >
                              <ChevronDown className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Second (hidden in schedule mode for 24h target time accuracy) */}
                      {runType === 'timer' && (
                        <div className="flex flex-col items-center">
                          <span className={`text-[11px] mb-1 ${secondaryText}`}>{L('초 (S)', 'Secs (S)')}</span>
                          <div className={`flex items-center border rounded ${inputFieldBg}`}>
                            <input
                              type="number"
                              min="0"
                              max="59"
                              value={inputS}
                              onChange={e => setInputS(Math.min(59, Math.max(0, parseInt(e.target.value) || 0)))}
                              className="w-12 text-center bg-transparent font-bold py-1 text-sm focus:outline-none"
                            />
                            <div className={`flex flex-col border-l ${subtleDivider}`}>
                              <button
                                onClick={() => setInputS(prev => Math.min(59, prev + 1))}
                                className={`px-1 ${isLight ? 'hover:bg-black/10 text-slate-700' : 'hover:bg-[#3f3f46] text-slate-300'}`}
                              >
                                <ChevronUp className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => setInputS(prev => Math.max(0, prev - 1))}
                                className={`px-1 ${isLight ? 'hover:bg-black/10 text-slate-700' : 'hover:bg-[#3f3f46] text-slate-300'}`}
                              >
                                <ChevronDown className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* 60-Minute Battery Consumption & Prediction Chart (Recharts) */}
                    <div className="mt-3">
                      <BatteryHistoryChart
                        currentBattery={battery}
                        timerState={isTimerRunning ? 'running' : 'idle'}
                        secondsRemaining={remainingSeconds}
                        lang={currentLang}
                        theme={currentTheme}
                      />
                    </div>

                    {/* Quick +Preset Pull-down & Fast Buttons */}
                    <div className={`mt-3 pt-2 border-t ${subtleDivider} space-y-1.5`}>
                      <div className={`flex items-center justify-between text-[11px] font-semibold ${secondaryText}`}>
                        <span>{L('⏱️ 시간 프리셋 (풀다운 / 빠른 선택):', '⏱️ Time Presets (Dropdown / Quick):')}</span>
                        <span className={`text-[10px] font-mono ${isLight ? 'text-blue-600' : 'text-blue-400'}`}>{L('단축 제어', 'Quick Ctrl')}</span>
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
                                showInAppToast(
                                  L(
                                    `⚡ ${sec >= 3600 ? `${sec / 3600}시간` : `${sec / 60}분`} 프리셋이 즉시 설정되었습니다.`,
                                    `⚡ Preset (${sec >= 3600 ? `${sec / 3600}h` : `${sec / 60}m`}) applied immediately.`
                                  )
                                );
                              }
                              e.target.value = '';
                            }}
                            className={`w-full border hover:border-blue-500/70 rounded px-2.5 py-1 text-xs appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer pr-7 font-medium ${inputFieldBg}`}
                          >
                            <option value="">{L('⏱️ 자주 쓰는 시간 프리셋 풀다운...', '⏱️ Select quick time preset...')}</option>
                            <optgroup label={L('➕ 시간 추가 (현재 시간에 누적)', '➕ Add Time (Accumulate)')}>
                              <option value="add:300">{L('+5분 추가', '+5m Add')}</option>
                              <option value="add:600">{L('+10분 추가', '+10m Add')}</option>
                              <option value="add:900">{L('+15분 추가', '+15m Add')}</option>
                              <option value="add:1800">{L('+30분 추가', '+30m Add')}</option>
                              <option value="add:2700">{L('+45분 추가', '+45m Add')}</option>
                              <option value="add:3600">{L('+1시간 추가', '+1h Add')}</option>
                              <option value="add:7200">{L('+2시간 추가', '+2h Add')}</option>
                            </optgroup>
                            <optgroup label={L('⚡ 즉시 지정 (지정 시간으로 타이머 리셋)', '⚡ Quick Set (Reset timer to preset)')}>
                              <option value="set:1800">{L('⚡ 30분 빠른 타이머 설정', '⚡ Set 30m Timer')}</option>
                              <option value="set:3600">{L('⚡ 1시간 빠른 타이머 설정', '⚡ Set 1h Timer')}</option>
                              <option value="set:7200">{L('⚡ 2시간 빠른 타이머 설정', '⚡ Set 2h Timer')}</option>
                              <option value="set:10800">{L('⚡ 3시간 빠른 타이머 설정', '⚡ Set 3h Timer')}</option>
                            </optgroup>
                          </select>
                          <ChevronDown className={`w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none ${secondaryText}`} />
                        </div>
                        <button
                          onClick={() => addPresetTime(10 * 60)}
                          className={`px-2 py-1 rounded text-xs font-bold border cursor-pointer shrink-0 whitespace-nowrap ${subtleBtnBg}`}
                        >
                          {L('+10분', '+10m')}
                        </button>
                        <button
                          onClick={() => addPresetTime(30 * 60)}
                          className={`px-2 py-1 rounded text-xs font-bold border cursor-pointer shrink-0 whitespace-nowrap ${subtleBtnBg}`}
                        >
                          {L('+30분', '+30m')}
                        </button>
                        <button
                          onClick={() => addPresetTime(60 * 60)}
                          className={`px-2 py-1 rounded text-xs font-bold border cursor-pointer shrink-0 whitespace-nowrap ${subtleBtnBg}`}
                        >
                          {L('+1시간', '+1h')}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Execution Control Action Buttons */}
                  <div className="flex items-center gap-2 pt-1">
                    {!isTimerRunning ? (
                      <button
                        onClick={startTimer}
                        className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded flex items-center justify-center gap-2 shadow-md transition-colors cursor-pointer"
                      >
                        <Play className="w-4 h-4 fill-white" />
                        <span>{L('▶ 타이머 시작', '▶ Start Timer')}</span>
                      </button>
                    ) : (
                      <button
                        onClick={stopTimer}
                        className="flex-1 py-2.5 bg-red-600 hover:bg-red-500 text-white font-bold rounded flex items-center justify-center gap-2 shadow-md transition-colors cursor-pointer"
                      >
                        <Square className="w-4 h-4 fill-white" />
                        <span>{L('⏹ 타이머 중지', '⏹ Stop Timer')}</span>
                      </button>
                    )}
                    <button
                      onClick={resetTimer}
                      className={`px-4 py-2.5 font-bold rounded flex items-center justify-center gap-1.5 transition-colors cursor-pointer whitespace-nowrap border ${subtleBtnBg}`}
                    >
                      <RotateCcw className="w-4 h-4" />
                      <span>{L('🔄 리셋', '🔄 Reset')}</span>
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
                    <span className={`font-bold ${primaryText}`}>{L('📅 예약된 전원 제어 규칙 목록', '📅 Scheduled Power Rules')}</span>
                    <span className={`text-[11px] font-semibold ${isLight ? 'text-blue-600' : 'text-blue-400'}`}>
                      {L(`${rules.length}개 활성`, `${rules.length} Active`)}
                    </span>
                  </div>

                  {/* Rules List Container */}
                  <div className={`border rounded p-2 max-h-56 overflow-y-auto space-y-1.5 ${panelBg}`}>
                    {rules.map(rule => (
                      <div
                        key={rule.id}
                        className={`border p-2 rounded flex items-center justify-between text-xs ${cardBg}`}
                      >
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={rule.enabled}
                            onChange={() => toggleRuleEnabled(rule.id)}
                            className="rounded border-slate-400 text-blue-600 w-4 h-4 cursor-pointer"
                          />
                          <div>
                            <div className={`font-bold flex items-center gap-1.5 ${primaryText}`}>
                              <span>{rule.name}</span>
                              <span className={`px-1.5 py-0.2 text-[10px] rounded font-bold ${isLight ? 'bg-red-100 text-red-700' : 'bg-red-600/30 text-red-300'}`}>
                                {rule.mode}
                              </span>
                            </div>
                            <div className={`text-[11px] ${secondaryText}`}>
                              ⏰ {rule.time} | 📅 {rule.days.join(', ')} | {L('⚡ /f 강제 종료', '⚡ /f Force Close')}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => deleteScheduleRule(rule.id)}
                          className={`hover:text-red-500 p-1 cursor-pointer ${secondaryText}`}
                          title={L('삭제', 'Delete')}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Quick Add Rule Form */}
                  <div className={`border p-3 rounded space-y-2 ${panelBg}`}>
                    <div className={`text-xs font-bold ${primaryText}`}>{L('➕ 새 스케줄 규칙 등록', '➕ Add New Schedule Rule')}</div>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder={L('규칙 제목', 'Rule Title')}
                        value={newRuleName}
                        onChange={e => setNewRuleName(e.target.value)}
                        className={`border rounded px-2.5 py-1 text-xs ${inputFieldBg}`}
                      />
                      <input
                        type="time"
                        value={newRuleTime}
                        onChange={e => setNewRuleTime(e.target.value)}
                        className={`border rounded px-2.5 py-1 text-xs ${inputFieldBg}`}
                      />
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <select
                        value={newRuleMode}
                        onChange={e => setNewRuleMode(e.target.value as any)}
                        className={`border rounded px-2 py-1 text-xs ${inputFieldBg}`}
                      >
                        <option value="shutdown">{L('종료 (Shutdown)', 'Shutdown')}</option>
                        <option value="restart">{L('재시작 (Restart)', 'Restart')}</option>
                        <option value="sleep">{L('절전 (Sleep)', 'Sleep')}</option>
                        <option value="screenoff">{L('화면끔 (Screen Off)', 'Screen Off')}</option>
                        <option value="logout">{L('로그아웃 (Logout)', 'Sign Out')}</option>
                        <option value="alarm">{L('알람 (Alarm)', 'Alarm')}</option>
                      </select>
                      <button
                        onClick={addScheduleRule}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold transition-colors cursor-pointer"
                      >
                        {L('+ 등록하기', '+ Add Rule')}
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
                    <span className={`font-bold text-xs ${primaryText}`}>
                      {L('📋 시스템 전원 제어 및 타이머 동작 기록', '📋 System Power Control & Timer Logs')}
                    </span>
                    <button
                      onClick={() => {
                        setLogs([
                          `[${new Date().toLocaleTimeString(isEn ? 'en-US' : 'ko-KR')}] ${L('로그가 초기화되었습니다.', 'Logs cleared.')}`
                        ]);
                        showInAppToast(L('로그가 초기화되었습니다.', 'Logs have been cleared.'));
                      }}
                      className={`px-2 py-0.5 rounded text-[11px] font-bold cursor-pointer border ${isLight ? 'bg-red-50 border-red-300 hover:bg-red-100 text-red-700' : 'bg-red-600/20 border-red-500/40 hover:bg-red-600/40 text-red-300'}`}
                    >
                      {L('🗑️ 로그 초기화', '🗑️ Clear Logs')}
                    </button>
                  </div>
                  <div
                    className={`border rounded p-3 text-[11px] font-mono h-64 overflow-y-auto space-y-1 ${panelBg} ${isLight ? 'text-slate-800' : 'text-slate-300'}`}
                    style={{ fontFamily: "'Consolas', monospace" }}
                  >
                    {logs.map((log, i) => (
                      <div key={i} className={`leading-relaxed border-b pb-0.5 ${subtleDivider}`}>
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Footer Information & CISNET Branding */}
              <div className={`pt-2.5 border-t text-center text-[11px] space-y-1 ${subtleDivider} ${secondaryText}`}>
                <div className="flex items-center justify-center gap-2 flex-wrap">
                  <a
                    href="http://www.cisnet.co.kr/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`transition-colors cursor-pointer ${isLight ? 'hover:text-slate-900' : 'hover:text-slate-200'}`}
                  >
                    {L('소속: http://www.cisnet.co.kr/', 'Org: http://www.cisnet.co.kr/')}
                  </a>
                  <span>|</span>
                  <span>{L('개발자: AhBiYout', 'Developer: AhBiYout')}</span>
                  <span>|</span>
                  <span className={`font-bold ${isLight ? 'text-blue-600' : 'text-blue-400'}`}>v{APP_VERSION}</span>
                </div>
                <div className="flex items-center justify-center gap-2 flex-wrap">
                  <a
                    href="https://ahbiyoutvibe.blogspot.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`underline transition-colors cursor-pointer ${isLight ? 'text-blue-600 hover:text-blue-700' : 'text-blue-400 hover:text-blue-300'}`}
                  >
                    {L('구글블로그: https://ahbiyoutvibe.blogspot.com/', 'Blog: https://ahbiyoutvibe.blogspot.com/')}
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* WINDOW 2: PowerNetworkScheduler.exe (50-PC Lab Fleet Control Tower)       */}
        {/* ========================================================================= */}
        {activeApp === 'network' && (
          <div
            className={`w-full max-w-[940px] rounded shadow-2xl overflow-hidden flex flex-col border ${windowBg} ${
              isWindowMaximized ? 'fixed inset-3 max-w-none z-40 overflow-y-auto' : ''
            }`}
            style={{ fontFamily: "'Malgun Gothic', 'Segoe UI', Arial, sans-serif" }}
          >
            {/* Window Title Bar */}
            <div className={`border-b px-3 py-2 flex items-center justify-between text-xs select-none ${titleBarBg}`}>
              <div className={`flex items-center gap-2 font-bold ${primaryText}`}>
                <div className="w-4 h-4 rounded bg-blue-600 flex items-center justify-center text-white text-[10px] font-black">
                  N
                </div>
                <span>PowerNetworkScheduler v{APP_VERSION} - {L('50대 컴퓨터실 원격 통합 제어 타워', '50-PC Lab Remote Fleet Control Tower')}</span>
              </div>
              <div className={`flex items-center gap-1 ${secondaryText}`}>
                <span className={`text-[11px] font-bold mr-2 ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                  {L('● UDP 9986 / TCP 9988 병렬 워커 가동', '● UDP 9986 / TCP 9988 Parallel')}
                </span>
                <button
                  onClick={() => setIsWindowMaximized(!isWindowMaximized)}
                  className={`w-7 h-5 flex items-center justify-center rounded cursor-pointer ${isLight ? 'hover:bg-black/10' : 'hover:bg-[#27272a]'}`}
                  title={L('최대화', 'Maximize')}
                >
                  <span className="text-[10px]">□</span>
                </button>
                <button
                  onClick={() => setActiveApp('main')}
                  className="w-7 h-5 flex items-center justify-center hover:bg-red-600 hover:text-white rounded cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="p-4 space-y-3 text-xs">
              {/* Section 1: Administrator Recovery Key & Token */}
              <div className={`border p-2.5 rounded space-y-2 ${panelBg}`}>
                <div className="flex items-center justify-between font-bold">
                  <span className={primaryText}>
                    {L('🔑 관리자 보안 인증 & 비상 복구 키 (ScheduleCrypto)', '🔑 Admin Auth & Recovery Key (ScheduleCrypto)')}
                  </span>
                  <span className={`text-[10px] font-mono ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                    HMAC-SHA256 Signed
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <input
                    type="password"
                    defaultValue="PowerRescue#2026!Admin"
                    placeholder={L('마스터 복구 키', 'Master Recovery Key')}
                    className={`border px-2.5 py-1 rounded font-mono ${inputFieldBg}`}
                  />
                  <input
                    type="text"
                    defaultValue="CisnetMasterToken2026"
                    placeholder={L('사내 보안 인증 토큰', 'Network Security Token')}
                    className={`border px-2.5 py-1 rounded font-mono ${inputFieldBg}`}
                  />
                </div>
              </div>

              {/* Section 2: Full 50-PC Computer Lab Control Tower */}
              <LabNetworkFleetPanel
                lang={currentLang}
                theme={currentTheme}
                devices={labDevices}
                onDevicesChange={setLabDevices}
                selectedIps={selectedDeviceIPs}
                onSelectedIpsChange={setSelectedDeviceIPs}
                onToast={(msg) => showInAppToast(msg)}
                onPlaySound={(kind) => playSoundEffect(kind)}
              />
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* WINDOW 3: ApplySharedSchedules.exe (One-Click Offline Schedule Injector)   */}
        {/* ========================================================================= */}
        {activeApp === 'injector' && (
          <div
            className={`w-full max-w-[500px] rounded shadow-2xl overflow-hidden flex flex-col border ${windowBg} ${
              isWindowMaximized ? 'fixed inset-3 max-w-none z-40 overflow-y-auto' : ''
            }`}
            style={{ fontFamily: "'Malgun Gothic', 'Segoe UI', Arial, sans-serif" }}
          >
            {/* Window Title Bar */}
            <div className={`border-b px-3 py-2 flex items-center justify-between text-xs select-none ${titleBarBg}`}>
              <div className={`flex items-center gap-2 font-bold ${primaryText}`}>
                <div className="w-4 h-4 rounded bg-emerald-600 flex items-center justify-center text-white text-[10px] font-black">
                  I
                </div>
                <span>ApplySharedSchedules v{APP_VERSION} - {L('스케줄 원클릭 주입기', 'One-Click Schedule Injector')}</span>
              </div>
              <div className={`flex items-center gap-1 ${secondaryText}`}>
                <button
                  onClick={() => setIsWindowMaximized(!isWindowMaximized)}
                  className={`w-7 h-5 flex items-center justify-center rounded cursor-pointer ${isLight ? 'hover:bg-black/10' : 'hover:bg-[#27272a]'}`}
                  title={L('최대화', 'Maximize')}
                >
                  <span className="text-[10px]">□</span>
                </button>
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
            </div>

            <div className="p-4 space-y-3.5 text-xs">
              <div className={`border p-3 rounded space-y-1 ${isLight ? 'bg-emerald-50 border-emerald-300' : 'bg-emerald-950/30 border-emerald-500/40'}`}>
                <div className={`font-bold flex items-center gap-1.5 ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                  <ShieldCheck className="w-4 h-4" />
                  <span>{L('ScheduleCrypto HMAC-SHA256 무결성 검증 완료', 'ScheduleCrypto HMAC-SHA256 Verified')}</span>
                </div>
                <div className={`text-[11px] ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                  {L(
                    '본 실행 파일에는 관리자 인증 서명과 함께 사내 표준 전원 스케줄이 암호화 봉투 형태로 임베딩되어 있습니다.',
                    'This portable executable carries standard corporate power schedules sealed with an admin HMAC-SHA256 signature.'
                  )}
                </div>
              </div>

              {/* Embedded Schedule Preview */}
              <div className={`border p-3 rounded space-y-2 ${panelBg}`}>
                <div className={`font-bold ${primaryText}`}>{L('📦 주입 대상 스케줄 규칙 (미리보기)', '📦 Embedded Schedule Rules Preview')}</div>
                <div className={`border p-2 rounded text-[11px] font-mono space-y-1 ${cardBg} ${primaryText}`}>
                  <div>{L('• [규칙 1] 🏢 정시 퇴근 자동 종료 (18:30 월~금)', '• [Rule 1] 🏢 Office EOD Shutdown (18:30 Mon-Fri)')}</div>
                  <div>{L('• [규칙 2] 🌙 야간 심야 자동 종료 (23:30 매일)', '• [Rule 2] 🌙 Midnight Auto Shutdown (23:30 Daily)')}</div>
                  <div>{L('• [규칙 3] 🔄 월요일 아침 정기 리부팅 (08:30 월)', '• [Rule 3] 🔄 Weekly Monday Reboot (08:30 Mon)')}</div>
                </div>
              </div>

              {/* Target Location Detection */}
              <div className={`border p-3 rounded space-y-1 text-[11px] ${panelBg}`}>
                <div className={`font-bold ${primaryText}`}>{L('🎯 자동 탐지된 대상 경로', '🎯 Auto-Detected Target Config Path')}</div>
                <div className={`font-mono break-all ${isLight ? 'text-blue-600' : 'text-blue-400'}`}>
                  %APPDATA%\PowerController\power_scheduler_rules.json
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => {
                  playSoundEffect('actionSuccess');
                  showInAppToast(
                    L(
                      '🚀 스케줄이 안전하게 주입 및 동기화되었습니다! (무결성 100% 검증)',
                      '🚀 Schedules injected & synced safely! (100% Integrity Verified)'
                    )
                  );
                }}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded flex items-center justify-center gap-2 shadow transition-colors text-sm cursor-pointer"
              >
                <HardDrive className="w-4 h-4" />
                <span>{L('🚀 스케줄 원클릭 즉시 주입 및 적용', '🚀 One-Click Inject & Apply Schedules')}</span>
              </button>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* WINDOW 4: DeviceController.exe (Dedicated Individual Device Control Panel) */}
        {/* ========================================================================= */}
        {activeApp === 'devices' && (
          <div
            className={`w-full max-w-[740px] rounded shadow-2xl overflow-hidden flex flex-col border ${windowBg} ${
              isWindowMaximized ? 'fixed inset-3 max-w-none z-40 overflow-y-auto' : ''
            }`}
            style={{ fontFamily: "'Malgun Gothic', 'Segoe UI', Arial, sans-serif" }}
          >
            {/* Window Title Bar */}
            <div className={`border-b px-3 py-2 flex items-center justify-between text-xs select-none ${titleBarBg}`}>
              <div className={`flex items-center gap-2 font-bold ${primaryText}`}>
                <div className="w-4 h-4 rounded bg-emerald-600 flex items-center justify-center text-white text-[10px] font-black">
                  D
                </div>
                <span>DeviceController v{APP_VERSION} - {L('감지 디바이스 개별 원격 제어판', 'Individual Device Remote Control')} ({labDevices.length}{L('대', ' PCs')})</span>
              </div>
              <div className={`flex items-center gap-1 ${secondaryText}`}>
                <button
                  type="button"
                  onClick={() => setActiveApp('network')}
                  className={`mr-2 px-2 py-0.5 rounded text-[11px] font-bold border cursor-pointer ${
                    isLight ? 'bg-blue-50 text-blue-700 border-blue-300 hover:bg-blue-100' : 'bg-blue-500/20 text-blue-300 border-blue-500/40 hover:bg-blue-500/30'
                  }`}
                >
                  {L('🏫 50대 관제 그리드 열기', '🏫 Open 50-PC Grid')}
                </button>
                <button
                  onClick={() => setIsWindowMaximized(!isWindowMaximized)}
                  className={`w-7 h-5 flex items-center justify-center rounded cursor-pointer ${isLight ? 'hover:bg-black/10' : 'hover:bg-[#27272a]'}`}
                  title={L('최대화', 'Maximize')}
                >
                  <span className="text-[10px]">□</span>
                </button>
                <button
                  onClick={() => setActiveApp('main')}
                  className="w-7 h-5 flex items-center justify-center hover:bg-red-600 hover:text-white rounded cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="p-4 space-y-3.5 text-xs">
              <div className={`border p-3 rounded flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${isLight ? 'bg-blue-50 border-blue-300' : 'bg-blue-950/30 border-blue-500/40'}`}>
                <div>
                  <div className={`font-bold flex items-center gap-1.5 ${isLight ? 'text-blue-700' : 'text-blue-400'}`}>
                    <Wifi className="w-4 h-4" />
                    <span>{L('개별 디바이스 직접 제어 타워 (TCP 9988 직결)', 'Direct Per-Device Control Tower (TCP 9988)')}</span>
                  </div>
                  <div className={`text-[11px] mt-0.5 ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                    {L(
                      '컴퓨터실 전체 등록 좌석(50대)별로 전원 종료(Shutdown), 재시작(Restart), 절전(Sleep), 화면 끄기, 알람을 즉시 실행할 수 있습니다.',
                      'Trigger immediate Shutdown, Restart, Sleep, Screen Off, or Alarm on any individual registered PC across the lab.'
                    )}
                  </div>
                </div>
                <div className={`text-[11px] font-mono font-bold whitespace-nowrap ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                  {L('온라인', 'Online')}: {labDevices.filter(d => d.status === 'online').length} / {labDevices.length}
                </div>
              </div>

              {/* Individual Device Cards List */}
              <div className="space-y-2 max-h-[52vh] overflow-y-auto pr-1">
                {labDevices.map((pc) => {
                  const statusLabel =
                    pc.status === 'online'
                      ? L('온라인', 'Online')
                      : pc.status === 'offline'
                      ? L('오프라인', 'Offline')
                      : pc.status === 'waking'
                      ? L('기상중', 'Waking')
                      : L('오류', 'Error');
                  const statusBadgeCls =
                    pc.status === 'online'
                      ? isLight ? 'bg-emerald-100 text-emerald-800' : 'bg-emerald-500/20 text-emerald-300'
                      : pc.status === 'waking'
                      ? isLight ? 'bg-amber-100 text-amber-800' : 'bg-amber-500/20 text-amber-300'
                      : isLight ? 'bg-slate-200 text-slate-700' : 'bg-slate-700/60 text-slate-300';

                  const triggerDeviceCmd = (
                    actionKey: 'shutdown' | 'restart' | 'sleep' | 'screenoff' | 'alarm',
                    koTag: string,
                    enTag: string,
                    toastMsg: string,
                    sound: 'actionSuccess' | 'timerAlarm' = 'actionSuccess'
                  ) => {
                    playSoundEffect(sound);
                    const ts = new Date().toLocaleTimeString(isEn ? 'en-US' : 'ko-KR');
                    const msg = `[${ts}] [${L(koTag, enTag)}] #${pc.seatNo} ${pc.hostname} (${pc.ip}) [OK]`;
                    setRemoteControlLogs(prev => [msg, ...prev.slice(0, 49)]);
                    setLabDevices(prev =>
                      prev.map(d =>
                        d.ip === pc.ip
                          ? {
                              ...d,
                              status: actionKey === 'shutdown' || actionKey === 'sleep' ? 'offline' : 'online',
                              lastAck: `${enTag} ACK`,
                            }
                          : d
                      )
                    );
                    showInAppToast(toastMsg);
                  };

                  return (
                    <div
                      key={pc.ip}
                      className={`border hover:border-blue-500/50 p-2.5 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 transition-all shadow ${panelBg}`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className={`w-9 h-9 rounded-md border flex flex-col items-center justify-center font-bold shrink-0 ${cardBg}`}>
                          <Cpu className={`w-3.5 h-3.5 ${pc.status === 'online' ? (isLight ? 'text-blue-600' : 'text-blue-400') : secondaryText}`} />
                          <span className="text-[9px] font-mono">{pc.seatNo}</span>
                        </div>
                        <div className="min-w-0">
                          <div className={`font-bold flex items-center gap-1.5 flex-wrap ${primaryText}`}>
                            <span>{pc.hostname}</span>
                            {pc.isSelf && (
                              <span className={`px-1.5 py-0.2 border rounded text-[9px] font-bold ${isLight ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-amber-500/20 text-amber-300 border-amber-500/40'}`}>
                                {L('👑 교사용 PC', '👑 Host PC')}
                              </span>
                            )}
                            <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${statusBadgeCls}`}>
                              {statusLabel}
                            </span>
                            {pc.rulesCount > 0 && (
                              <span className={`text-[10px] font-mono ${secondaryText}`}>
                                ({pc.rulesCount} {L('규칙', 'rules')})
                              </span>
                            )}
                          </div>
                          <div className={`text-[10.5px] font-mono mt-0.5 truncate ${secondaryText}`}>
                            {pc.ip} · MAC {pc.mac} · {pc.group}
                          </div>
                        </div>
                      </div>

                      {/* Individual Control Action Buttons ('Shutdown', 'Restart', 'Sleep', 'Screen Off', 'Alarm') */}
                      <div className="flex items-center gap-1 w-full sm:w-auto justify-end flex-wrap shrink-0">
                        <button
                          onClick={() =>
                            triggerDeviceCmd(
                              'shutdown',
                              '개별 종료',
                              'Shutdown',
                              L(`🛑 [#${pc.seatNo} ${pc.hostname}] PC에 즉시 전원 종료 명령을 전송했습니다.`, `🛑 Shutdown command sent to [#${pc.seatNo} ${pc.hostname}].`)
                            )
                          }
                          className="px-2 py-1 bg-red-600 hover:bg-red-500 text-white rounded font-bold text-[11px] shadow flex items-center gap-1 cursor-pointer transition-colors whitespace-nowrap"
                          title={L('이 PC 즉시 전원 종료 (Shutdown)', 'Shutdown this PC immediately')}
                        >
                          <Power className="w-3 h-3" />
                          <span>{L('종료', 'Shutdown')}</span>
                        </button>
                        <button
                          onClick={() =>
                            triggerDeviceCmd(
                              'restart',
                              '개별 재시작',
                              'Restart',
                              L(`🔄 [#${pc.seatNo} ${pc.hostname}] PC에 즉시 재시작 명령을 전송했습니다.`, `🔄 Restart command sent to [#${pc.seatNo} ${pc.hostname}].`)
                            )
                          }
                          className="px-2 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded font-bold text-[11px] shadow flex items-center gap-1 cursor-pointer transition-colors whitespace-nowrap"
                          title={L('이 PC 시스템 다시 시작 (Restart)', 'Restart this PC immediately')}
                        >
                          <RotateCw className="w-3 h-3" />
                          <span>{L('재시작', 'Restart')}</span>
                        </button>
                        <button
                          onClick={() =>
                            triggerDeviceCmd(
                              'sleep',
                              '개별 절전',
                              'Sleep',
                              L(`🌙 [#${pc.seatNo} ${pc.hostname}] PC를 절전 모드로 전환했습니다.`, `🌙 Sleep command sent to [#${pc.seatNo} ${pc.hostname}].`)
                            )
                          }
                          className="px-2 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-bold text-[11px] shadow flex items-center gap-1 cursor-pointer transition-colors whitespace-nowrap"
                          title={L('이 PC 절전 모드 전환 (Sleep)', 'Put this PC to Sleep')}
                        >
                          <Moon className="w-3 h-3" />
                          <span>{L('절전', 'Sleep')}</span>
                        </button>
                        <button
                          onClick={() =>
                            triggerDeviceCmd(
                              'screenoff',
                              '화면 끄기',
                              'Screen Off',
                              L(`📺 [#${pc.seatNo} ${pc.hostname}] PC 화면을 껐습니다.`, `📺 Screen Off sent to [#${pc.seatNo} ${pc.hostname}].`)
                            )
                          }
                          className="px-2 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded font-bold text-[11px] shadow flex items-center gap-1 cursor-pointer transition-colors whitespace-nowrap"
                          title={L('이 PC 화면 끄기', 'Turn off monitor on this PC')}
                        >
                          <Monitor className="w-3 h-3" />
                          <span>{L('화면끔', 'Screen Off')}</span>
                        </button>
                        <button
                          onClick={() =>
                            triggerDeviceCmd(
                              'alarm',
                              '비상 알람',
                              'Alarm',
                              L(`🚨 [#${pc.seatNo} ${pc.hostname}] PC에 긴급 알람을 송출했습니다.`, `🚨 Emergency alarm sent to [#${pc.seatNo} ${pc.hostname}].`),
                              'timerAlarm'
                            )
                          }
                          className="px-2 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded font-bold text-[11px] shadow flex items-center gap-1 cursor-pointer transition-colors whitespace-nowrap"
                          title={L('긴급 알람 송출', 'Send emergency alarm')}
                        >
                          <Bell className="w-3 h-3" />
                          <span>{L('알람', 'Alarm')}</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Realtime Execution Log for Individual Device Control */}
              <div className={`border rounded p-2 text-[10px] font-mono space-y-1 max-h-24 overflow-y-auto ${panelBg}`}>
                <div className={`font-bold flex items-center justify-between pb-1 border-b ${subtleDivider} ${secondaryText}`}>
                  <span>{L('📋 개별 디바이스 원격 제어 실시간 실행 콘솔', '📋 Per-Device Remote Execution Console')}</span>
                  <button
                    onClick={() => setRemoteControlLogs([
                      `[${new Date().toLocaleTimeString()}] ${L('콘솔 로그가 초기화되었습니다.', 'Console logs cleared.')}`
                    ])}
                    className={`cursor-pointer ${isLight ? 'text-slate-600 hover:text-slate-900' : 'text-slate-400 hover:text-slate-200'}`}
                  >
                    {L('지우기', 'Clear')}
                  </button>
                </div>
                {remoteControlLogs.map((log, lIdx) => (
                  <div key={lIdx} className={`whitespace-nowrap overflow-hidden text-ellipsis ${isLight ? 'text-emerald-700' : 'text-emerald-400/90'}`}>
                    {log}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Settings Modal (Tkinter Settings Style) */}
      {showSettingsModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className={`w-full max-w-[480px] rounded shadow-2xl overflow-hidden text-xs border ${windowBg}`}>
            <div className={`border-b px-3 py-2 flex items-center justify-between font-bold ${titleBarBg}`}>
              <span>{L('⚙️ PowerController 환경설정 (Settings)', '⚙️ PowerController Settings')}</span>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="hover:bg-red-600 p-1 rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="p-4 space-y-3 max-h-[75vh] overflow-y-auto">
              {/* 0. Display Language & Browser Auto-Detection */}
              <div className={`p-3 rounded space-y-2 border ${panelBg}`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold flex items-center gap-1.5">
                    🌐 {L('인터페이스 & 스크립트 언어 (Language)', 'Interface & Script Language')}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 font-mono">
                    {internalLangSource === 'auto'
                      ? L('브라우저 자동 감지', 'Auto-Detected')
                      : L('사용자 수동 설정', 'Manual Override')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleDesktopLangSwitch('ko')}
                    className={`flex-1 py-1.5 rounded text-xs font-bold border transition-colors cursor-pointer whitespace-nowrap ${
                      currentLang === 'ko'
                        ? 'bg-blue-600 text-white border-blue-500'
                        : subtleBtnBg
                    }`}
                  >
                    🇰🇷 한국어 (Korean)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDesktopLangSwitch('en')}
                    className={`flex-1 py-1.5 rounded text-xs font-bold border transition-colors cursor-pointer whitespace-nowrap ${
                      currentLang === 'en'
                        ? 'bg-blue-600 text-white border-blue-500'
                        : subtleBtnBg
                    }`}
                  >
                    🇺🇸 English (Global)
                  </button>
                  <button
                    type="button"
                    onClick={handleDesktopLangAutoReset}
                    className={`px-2.5 py-1.5 rounded text-[11px] font-semibold border cursor-pointer whitespace-nowrap shrink-0 ${subtleBtnBg}`}
                    title={L('브라우저 기본 언어로 자동 복원', 'Reset to browser auto-detection')}
                  >
                    {L('자동 감지 복원', 'Auto Reset')}
                  </button>
                </div>
              </div>

              <div className={`p-3 rounded space-y-2 border ${panelBg}`}>
                <span className="font-bold flex items-center gap-1">🎨 {L('테마 스타일 변경 (Theme Selection)', 'Theme Selection')}</span>
                <select
                  value={currentTheme}
                  onChange={(e) => {
                    const newTh = e.target.value as ThemeType;
                    setCurrentTheme(newTh);
                    localStorage.setItem('power_theme', newTh);
                    onThemeChange?.(newTh);
                    showInAppToast(L(`테마가 [${newTh}]로 변경되었습니다.`, `Theme changed to [${newTh}].`));
                  }}
                  className={`w-full p-2 rounded text-xs font-bold appearance-none cursor-pointer border ${cardBg}`}
                >
                  <option value="dark">{L('🌑 다크 (Fluent Dark)', '🌑 Fluent Dark')}</option>
                  <option value="gray">{L('🌫️ 그레이 (Simple Gray)', '🌫️ Simple Gray')}</option>
                  <option value="white">{L('☀️ 화이트 (Clean White)', '☀️ Clean White')}</option>
                  <option value="beige">{L('☕ 베이지 (Cozy Beige)', '☕ Cozy Beige')}</option>
                </select>
              </div>

              <div className={`${panelBg} p-3 rounded space-y-2 border`}>
                <span className={`font-bold ${primaryText}`}>{L('1. 부팅 및 트레이 동작', '1. Boot & System Tray Behavior')}</span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={autoStart} onChange={e => setAutoStart(e.target.checked)} />
                  <span>{L('Windows 시작 시 자동 실행 (레지스트리 Run 키)', 'Run automatically at Windows startup (Registry)')}</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={bootToTray} onChange={e => setBootToTray(e.target.checked)} />
                  <span>{L('부팅 시 화면 표시 없이 트레이로 바로 숨기기', 'Start silently minimized to system tray on boot')}</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={minimizeToTray} onChange={e => setMinimizeToTray(e.target.checked)} />
                  <span>{L('최소화 버튼 클릭 시 작업표시줄 대신 트레이로 숨김', 'Hide to system tray instead of taskbar when minimized')}</span>
                </label>
              </div>

              <div className={`${panelBg} p-3 rounded space-y-2 border`}>
                <span className={`font-bold ${primaryText}`}>{L('2. 강제 닫기 플래그 (/f)', '2. Force Close Flag (/f)')}</span>
                <label className={`flex items-center gap-2 cursor-pointer font-bold ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                  <input type="checkbox" checked={forceClose} onChange={e => setForceClose(e.target.checked)} />
                  <span>{L('전원 명령 시 저장되지 않은 프로그램 강제 종료 (/f) 기본 활성화', 'Force terminate unsaved applications (/f) by default')}</span>
                </label>
                <div className={`text-[11px] ${secondaryText}`}>
                  {L(
                    '컴퓨터 종료 시 메모장 등 저장 대화상자로 인한 전원 차단 중단 방지.',
                    'Prevents Windows shutdown from stalling on unsaved document prompts.'
                  )}
                </div>
              </div>

              <div className={`${panelBg} p-3 rounded space-y-2 border`}>
                <span className={`font-bold ${primaryText}`}>{L('3. 네트워크 원격 보안', '3. Network Remote Security')}</span>
                <label className={`flex items-center gap-2 cursor-pointer font-bold ${isLight ? 'text-blue-700' : 'text-blue-400'}`}>
                  <input type="checkbox" checked={networkReceive} onChange={e => setNetworkReceive(e.target.checked)} />
                  <span>{L('TCP 9988 포트 원격 스케줄 수신 활성화', 'Enable TCP 9988 remote command listener')}</span>
                </label>
                <div className="flex items-center gap-2 pt-1">
                  <span className={secondaryText}>{L('네트워크 보안 토큰:', 'Security Auth Token:')}</span>
                  <input
                    type="password"
                    defaultValue="MySecretToken#123"
                    className={`border px-2 py-1 rounded font-mono flex-1 text-xs ${inputFieldBg}`}
                  />
                </div>
              </div>

              {/* 4. Sound & Alert Themes (Pixabay Sound Effects & Web Audio Mixer) */}
              <div className={`${panelBg} p-3 rounded space-y-3 border`}>
                <div className="flex items-center justify-between">
                  <div className={`flex items-center gap-1.5 font-bold ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                    <Volume2 className={`w-4 h-4 ${isLight ? 'text-emerald-600' : 'text-emerald-400'}`} />
                    <span>{L('4. 알림 효과음 사운드 뱅크 (Pixabay 선별 & Web Audio)', '4. Sound Alert Bank (Web Audio Synthesizer)')}</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded border font-mono ${isLight ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'text-emerald-300/90 bg-emerald-500/10 border-emerald-500/30'}`}>
                    {L('현재:', 'Active:')}{' '}
                    {isEn
                      ? SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameEn || 'Classic Bell'
                      : SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameKo || '클래식 벨'}
                  </span>
                </div>

                {/* Master Volume Controller & Quick Presets */}
                <div className={`${cardBg} p-2.5 rounded border space-y-2`}>
                  <div className="flex items-center justify-between text-xs">
                    <span className={`font-semibold flex items-center gap-1.5 ${primaryText}`}>
                      {currentSoundVolume === 0 ? (
                        <VolumeX className="w-4 h-4 text-rose-500" />
                      ) : currentSoundVolume < 50 ? (
                        <Volume1 className="w-4 h-4 text-amber-500" />
                      ) : (
                        <Volume2 className="w-4 h-4 text-emerald-500" />
                      )}
                      <span>{L('마스터 볼륨 (Master Volume)', 'Master Volume')}</span>
                    </span>
                    <span className={`font-mono font-bold text-sm ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
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
                      className={`px-2 py-1 rounded text-[11px] font-bold border transition-colors cursor-pointer whitespace-nowrap ${subtleBtnBg}`}
                    >
                      {currentSoundVolume === 0 ? L('🔊 음소거 해제', '🔊 Unmute') : L('🔇 음소거', '🔇 Mute')}
                    </button>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={currentSoundVolume}
                      onChange={(e) => handleVolumeChange(parseInt(e.target.value))}
                      className="flex-1 accent-emerald-500 cursor-pointer h-1.5 bg-slate-500/30 rounded-lg"
                    />
                  </div>

                  {/* Quick Volume Preset Buttons */}
                  <div className={`flex items-center justify-between gap-1 pt-1 border-t ${subtleDivider}`}>
                    <span className={`text-[10px] font-medium ${secondaryText}`}>{L('빠른 볼륨 설정:', 'Quick Presets:')}</span>
                    <div className="flex items-center gap-1">
                      {[0, 30, 50, 80, 100].map((v) => (
                        <button
                          key={v}
                          type="button"
                          onClick={() => {
                            handleVolumeChange(v);
                            if (v > 0) playSoundEffect('buttonClick');
                          }}
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold transition-colors cursor-pointer border ${
                            currentSoundVolume === v
                              ? 'bg-emerald-600 text-white border-emerald-500'
                              : subtleBtnBg
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
                  <div className={`flex items-center justify-between text-[11px] font-semibold ${primaryText}`}>
                    <span>{L('알림음 테마 선택 (드롭다운 / 풀다운):', 'Select Alert Sound Theme:')}</span>
                    <span className={`text-[10px] font-mono ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                      ✓ {isEn ? SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameEn : SOUND_THEMES.find(t => t.id === currentSoundTheme)?.nameKo}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <select
                        value={currentSoundTheme}
                        onChange={(e) => handleSelectSoundTheme(e.target.value as SoundTheme)}
                        className={`w-full border hover:border-emerald-500/70 rounded px-3 py-2 text-xs font-bold appearance-none focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer pl-8 pr-8 shadow-inner ${inputFieldBg}`}
                      >
                        {SOUND_THEMES.map((th) => (
                          <option key={th.id} value={th.id} className="py-1 font-medium">
                            {isEn ? `${th.icon} ${th.nameEn} - ${th.descEn}` : `${th.icon} ${th.nameKo} (${th.nameEn}) - ${th.descKo}`}
                          </option>
                        ))}
                      </select>
                      <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-sm pointer-events-none">
                        {SOUND_THEMES.find(t => t.id === currentSoundTheme)?.icon || '🔔'}
                      </span>
                      <ChevronDown className={`w-3.5 h-3.5 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none ${secondaryText}`} />
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        playSoundEffect('timerAlarm');
                        const selected = SOUND_THEMES.find(t => t.id === currentSoundTheme);
                        showInAppToast(
                          L(
                            `[${selected?.nameKo}] 알림음 사운드 테스트 재생`,
                            `Playing [${selected?.nameEn}] sound preview`
                          )
                        );
                      }}
                      className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold transition-colors flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow shrink-0"
                      title={L('선택된 알림음 사운드 즉시 테스트 재생', 'Preview selected alert chime')}
                    >
                      <Play className="w-3 h-3 fill-white" />
                      <span>{L('테스트 재생', 'Play Test')}</span>
                    </button>
                  </div>
                  <div className={`text-[10px] pl-1 ${secondaryText}`}>
                    ℹ️ {isEn ? SOUND_THEMES.find(t => t.id === currentSoundTheme)?.descEn : SOUND_THEMES.find(t => t.id === currentSoundTheme)?.descKo}
                  </div>
                </div>

                {/* 2. Situational Sound Audition Test Pull-down */}
                <div className={`${cardBg} p-2.5 rounded border space-y-2`}>
                  <div className={`flex items-center justify-between text-xs font-semibold ${primaryText}`}>
                    <span>{L('상황별 효과음 테스트 풀다운:', 'Situational Sound Audition:')}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <select
                        value={selectedSoundTestTrigger}
                        onChange={(e) => setSelectedSoundTestTrigger(e.target.value as any)}
                        className={`w-full border hover:border-blue-500/70 rounded px-3 py-2 text-xs appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer pr-8 font-medium shadow-inner ${inputFieldBg}`}
                      >
                        <option value="preview">{L('🔔 1. 테마 대표 시그니처 톤 (미리듣기)', '🔔 1. Signature Theme Tone (Preview)')}</option>
                        <option value="warningTick">{L('⏱️ 2. 10초 카운트다운 틱 경고음 (Tick)', '⏱️ 2. 10-Second Countdown Tick')}</option>
                        <option value="hourlyChime">{L('🏛️ 3. 매시 정각 시계탑 차임벨 (00분 정각)', '🏛️ 3. Hourly Bell Tower Chime')}</option>
                        <option value="timerAlarm">{L('🚨 4. 타이머 만료 알람 경보음 (Alarm)', '🚨 4. Timer Expiration Alarm')}</option>
                        <option value="actionSuccess">{L('✨ 5. 전원 명령 완료 및 스케줄 등록 성공음', '✨ 5. Command Success Chime')}</option>
                      </select>
                      <ChevronDown className={`w-3.5 h-3.5 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none ${secondaryText}`} />
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        playSoundEffect(selectedSoundTestTrigger);
                        const labels: Record<string, string> = {
                          preview: L('테마 대표 시그니처 톤', 'Signature Tone'),
                          warningTick: L('10초 카운트다운 틱 경고음', '10s Warning Tick'),
                          hourlyChime: L('정각 시계탑 차임벨', 'Hourly Chime'),
                          timerAlarm: L('타이머 만료 알람 경보음', 'Timer Alarm'),
                          actionSuccess: L('명령 실행 및 성공음', 'Action Success')
                        };
                        showInAppToast(`🔊 [${labels[selectedSoundTestTrigger] || selectedSoundTestTrigger}] ${L('재생', 'Played')}`);
                      }}
                      className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-bold transition-colors flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow shrink-0"
                    >
                      <Play className="w-3 h-3 fill-white" />
                      <span>{L('테스트 재생', 'Audition')}</span>
                    </button>
                  </div>
                </div>

                {/* Additional Audio Toggles */}
                <div className={`space-y-1.5 pt-1 border-t ${subtleDivider}`}>
                  <label className={`flex items-center justify-between cursor-pointer py-1 ${primaryText}`}>
                    <span className="text-xs">{L('🔔 매시 정각 시계탑 차임벨 (00분 00초) 알림', '🔔 Hourly Top-of-Hour Chime (00m 00s)')}</span>
                    <input
                      type="checkbox"
                      checked={currentHourlyChime}
                      onChange={(e) => handleHourlyChimeToggle(e.target.checked)}
                      className="rounded border-slate-400 text-emerald-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                  </label>
                  <label className={`flex items-center justify-between cursor-pointer py-1 ${primaryText}`}>
                    <span className="text-xs">{L('🖱️ 버튼 클릭 및 조작 인터랙션 효과음', '🖱️ Interactive Button Click Sound Feedback')}</span>
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
                      className="rounded border-slate-400 text-emerald-600 focus:ring-0 w-4 h-4 cursor-pointer"
                    />
                  </label>
                </div>
              </div>

              {/* 5. Smart Power Saving Mode (<20% battery auto dimming) */}
              <div className={`${panelBg} p-3 rounded space-y-2 border`}>
                <div className="flex items-center justify-between">
                  <span className={`font-bold flex items-center gap-1.5 ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                    {L('🍃 5. 스마트 절전 모드 (배터리 20% 이하 감지)', '🍃 5. Smart Eco Mode (<20% Battery Auto Dim)')}
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
                        showInAppToast(
                          e.target.checked
                            ? L('스마트 절전 모드가 활성화되었습니다.', 'Smart Eco Mode enabled.')
                            : L('스마트 절전 모드가 비활성화되었습니다.', 'Smart Eco Mode disabled.')
                        );
                      }}
                      className="sr-only peer"
                    />
                    <div className="relative w-7 h-4 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-600"></div>
                  </label>
                </div>
                <div className={`text-[11px] leading-relaxed ${secondaryText}`}>
                  {L(
                    '배터리 잔량이 20% 이하로 떨어지면 플로팅 위젯의 투명도를 자동으로 낮추고 배경 애니메이션을 어둡게 감쇠하여 배터리 방전을 지연시킵니다.',
                    'Automatically dims floating widgets and pauses background animations when battery drops below 20%.'
                  )}
                </div>
              </div>

              {/* 6. Auto-Lock Desktop Session on Idle (Timer Running) */}
              <div className={`${panelBg} p-3 rounded space-y-2 border`}>
                <div className="flex items-center justify-between">
                  <span className={`font-bold flex items-center gap-1.5 ${isLight ? 'text-blue-700' : 'text-blue-400'}`}>
                    {L('🔒 6. 타이머 가동 중 자동 화면 잠금 (Auto-Lock Desktop)', '🔒 6. Auto-Lock Desktop Session on Idle')}
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
                        showInAppToast(
                          e.target.checked
                            ? L('유휴 상태 자동 화면 잠금이 활성화되었습니다.', 'Idle Auto-Lock enabled.')
                            : L('유휴 상태 자동 화면 잠금이 비활성화되었습니다.', 'Idle Auto-Lock disabled.')
                        );
                      }}
                      className="sr-only peer"
                    />
                    <div className="relative w-7 h-4 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                <div className={`text-[11px] leading-relaxed ${secondaryText}`}>
                  {L(
                    '타이머 가동 중 지정된 시간 동안 마우스/키보드 입력이 없으면 Windows 데스크톱 세션을 자동으로 잠급니다(Win + L).',
                    'Automatically locks Windows session (Win + L) after specified idle duration while a countdown timer is running.'
                  )}
                </div>
                <div className={`flex items-center justify-between gap-2 pt-1 border-t ${subtleDivider}`}>
                  <span className={`text-xs ${secondaryText}`}>{L('유휴 감지 시간:', 'Idle Timeout:')}</span>
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
                    className={`text-xs font-semibold rounded px-2.5 py-1 border focus:outline-none focus:border-blue-500 cursor-pointer ${inputFieldBg} ${!idleLockEnabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <option value="1">{L('1분 (1 min)', '1 min')}</option>
                    <option value="2">{L('2분 (2 mins)', '2 mins')}</option>
                    <option value="3">{L('3분 (3 mins)', '3 mins')}</option>
                    <option value="5">{L('5분 (5 mins - 기본)', '5 mins (Default)')}</option>
                    <option value="10">{L('10분 (10 mins)', '10 mins')}</option>
                    <option value="15">{L('15분 (15 mins)', '15 mins')}</option>
                    <option value="30">{L('30분 (30 mins)', '30 mins')}</option>
                  </select>
                </div>
              </div>

              {/* 7. Real-time Update Section */}
              <div className={`p-3 rounded space-y-2 border ${isLight ? 'bg-blue-50 border-blue-300' : 'bg-gradient-to-r from-blue-950/40 to-indigo-950/40 border-blue-500/30'}`}>
                <div className="flex items-center justify-between">
                  <span className={`font-bold flex items-center gap-1.5 ${isLight ? 'text-blue-700' : 'text-blue-300'}`}>
                    <Sparkles className={`w-3.5 h-3.5 ${isLight ? 'text-amber-500' : 'text-amber-300'}`} />
                    {L('7. GitHub 실시간 업데이트 & 버전 정보', '7. GitHub Live Updates & Version Info')}
                  </span>
                  <span className={`font-mono font-bold ${isLight ? 'text-blue-700' : 'text-blue-400'}`}>v{APP_VERSION}</span>
                </div>
                <div className={`text-[11px] leading-relaxed ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                  {L(
                    'GitHub 공식 저장소의 최신 버전 태그와 배포 인스톨러(.exe)를 실시간으로 비교하고 업데이트합니다.',
                    'Compare installed version with official GitHub releases and download installers in real time.'
                  )}
                </div>
                <button
                  onClick={() => {
                    setShowSettingsModal(false);
                    setShowUpdateModal(true);
                  }}
                  className="w-full py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded shadow transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{L('🚀 업데이트 알림 팝업창 열기 & 최신 확인', '🚀 Check for Updates & Open Release Notes')}</span>
                </button>
              </div>
            </div>
            <div className={`border-t px-3 py-2 flex items-center justify-end gap-2 ${panelBg}`}>
              <button
                onClick={() => {
                  setShowSettingsModal(false);
                  showInAppToast(L('환경설정이 안전하게 저장되었습니다.', 'Preferences saved safely.'));
                }}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded text-xs cursor-pointer whitespace-nowrap"
              >
                {L('확인 (적용)', 'Apply & Save')}
              </button>
              <button
                onClick={() => setShowSettingsModal(false)}
                className={`px-3 py-1.5 rounded text-xs border cursor-pointer whitespace-nowrap ${subtleBtnBg}`}
              >
                {L('취소', 'Cancel')}
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
              {L('🔒 데스크톱 세션 잠김 (Idle Auto-Lock)', '🔒 Desktop Session Locked (Idle Auto-Lock)')}
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {L(
                `타이머 가동 중 ${idleLockMinutes}분 동안 활동이 없어 화면이 자동으로 잠겼습니다.`,
                `Screen locked automatically after ${idleLockMinutes} minute(s) of inactivity while countdown timer was active.`
              )}
            </p>
            <button
              onClick={() => {
                setIsDesktopLocked(false);
                lastUserActivityRef.current = Date.now();
                soundEngine.play(currentSoundTheme, 'actionSuccess');
                showInAppToast(L('🔓 데스크톱 세션 잠금이 정상 해제되었습니다.', '🔓 Desktop session unlocked successfully.'));
              }}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg shadow cursor-pointer transition-colors text-xs flex items-center justify-center gap-2"
            >
              <span>{L('🔓 잠금 해제 (클릭 또는 Enter)', '🔓 Unlock Session (Click or Enter)')}</span>
            </button>
          </div>
        </div>
      )}

      {/* Global Real-time Update Modal */}
      <UpdateModal
        isOpen={showUpdateModal}
        onClose={() => setShowUpdateModal(false)}
        lang={currentLang}
      />
    </div>
  );
};

export default DesktopAppView;
