import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Power,
  RotateCw,
  Play,
  Pause,
  RotateCcw,
  Pin,
  PinOff,
  Moon,
  Sun,
  Clock,
  Terminal,
  Volume2,
  VolumeX,
  Music,
  Plus,
  ShieldAlert,
  Info,
  Laptop,
  LogOut,
  Palette,
  Folder,
  FileText,
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  ArrowUp,
  RotateCcw as RefreshIcon,
  Search,
  HardDrive,
  Cpu,
  Monitor,
  Menu,
  Maximize2,
  Minimize2,
  X,
  Star,
  Network,
  Eye,
  Type
} from 'lucide-react';
import { PowerMode, TimerState, ThemeType, ExplorerFolder, APP_VERSION } from './types';
import CommandCopier from './components/CommandCopier';
import FavoritesManager from './components/FavoritesManager';
import PowerSimulator from './components/PowerSimulator';
import PackagerGuide from './components/PackagerGuide';
import AdvancedScheduler from './components/AdvancedScheduler';
import CompactWidget, { CompactWidgetDesign } from './components/CompactWidget';
import StartupTodayTasksModal from './components/StartupTodayTasksModal';
import DesktopAppView from './components/DesktopAppView';
import { GitHubUpdateBanner } from './components/GitHubUpdateBanner';

interface DraftSettingsState {
  theme: ThemeType;
  soundTheme: 'classic' | 'scifi' | 'cozy';
  showCurrentTimeCompact: boolean;
  widgetOpacity: number;
  mainOpacity: number;
  selectedFont: string;
  graceSeconds: number;
  hourlyChime: boolean;
  startupTasksAlert: boolean;
  widgetDesign: CompactWidgetDesign;
  widgetWidth: number;
  clockFontSize: number;
  timerFontSize: number;
  forceCloseEnabled: boolean;
}

export default function App() {
  const [viewMode, setViewMode] = useState<'desktop' | 'web'>('desktop');

  const [lang, setLang] = useState<'ko' | 'en'>(() => {
    try {
      const saved = localStorage.getItem('power_lang');
      return (saved === 'ko' || saved === 'en') ? saved : 'ko';
    } catch {
      return 'ko';
    }
  });

  const handleLangChange = (newLang: 'ko' | 'en') => {
    setLang(newLang);
    localStorage.setItem('power_lang', newLang);
    addLog(newLang === 'en' ? 'Language changed to English.' : '언어가 한국어로 변경되었습니다.');
  };

  // Theme & Window properties
  const [theme, setTheme] = useState<ThemeType>('beige');
  const [alwaysOnTop, setAlwaysOnTop] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('power_always_on_top');
      return saved !== null ? saved === 'true' : false;
    } catch {
      return false;
    }
  });
  const [soundEnabled, setSoundEnabled] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('power_sound_enabled');
      return saved !== null ? saved === 'true' : true;
    } catch {
      return true;
    }
  });
  const [soundTheme, setSoundTheme] = useState<'classic' | 'scifi' | 'cozy'>(() => {
    try {
      const saved = localStorage.getItem('power_sound_theme');
      return (saved as 'classic' | 'scifi' | 'cozy') || 'classic';
    } catch {
      return 'classic';
    }
  });

  // Hourly Chime & Startup alert states
  const [hourlyChime, setHourlyChime] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('power_hourly_chime');
      return saved !== null ? saved === 'true' : true;
    } catch {
      return true;
    }
  });

  const [startupTasksAlert, setStartupTasksAlert] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('power_startup_tasks_alert');
      return saved !== null ? saved === 'true' : true;
    } catch {
      return true;
    }
  });

  // Compact Widget Customizer States
  const [widgetDesign, setWidgetDesign] = useState<CompactWidgetDesign>(() => {
    try {
      const saved = localStorage.getItem('power_widget_design');
      return (saved as CompactWidgetDesign) || 'standard';
    } catch {
      return 'standard';
    }
  });

  const [widgetWidth, setWidgetWidth] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('power_widget_width');
      return saved ? parseInt(saved, 10) : 340;
    } catch {
      return 340;
    }
  });

  const [clockFontSize, setClockFontSize] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('power_clock_font_size');
      return saved ? parseInt(saved, 10) : 11;
    } catch {
      return 11;
    }
  });

  const [timerFontSize, setTimerFontSize] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('power_timer_font_size');
      return saved ? parseInt(saved, 10) : 24;
    } catch {
      return 24;
    }
  });

  // Startup Today Tasks modal states
  const [todayTasksModalOpen, setTodayTasksModalOpen] = useState<boolean>(false);
  const [todayTasks, setTodayTasks] = useState<any[]>([]);

  // Settings Modal State and Buffered Draft State
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [draftSettings, setDraftSettings] = useState<DraftSettingsState | null>(null);
  const [activeAccordion, setActiveAccordion] = useState<string>('theme'); // 'theme' | 'sound' | 'alwaysOnTop' | 'mainWindow'
  const [isLicenseOpen, setIsLicenseOpen] = useState<boolean>(false);
  const [licenseModalLang, setLicenseModalLang] = useState<'ko' | 'en'>('ko');

  const handleSoundThemeChange = (newTheme: 'classic' | 'scifi' | 'cozy') => {
    setSoundTheme(newTheme);
    try {
      localStorage.setItem('power_sound_theme', newTheme);
    } catch {}
    if (lang === 'en') {
      addLog(`Sound alert theme updated to: ${newTheme === 'classic' ? 'Classic Beep' : newTheme === 'scifi' ? 'Sci-Fi Synth' : 'Cozy Chime'}`);
    } else {
      addLog(`경고음 알림 사운드 테마가 변경되었습니다: ${newTheme === 'classic' ? '클래식 비프' : newTheme === 'scifi' ? 'SF 신스' : '아늑한 멜로디'}`);
    }
  };
  
  // Custom Warning Timing settings
  const [warningTimes, setWarningTimes] = useState<number[]>(() => {
    try {
      const saved = localStorage.getItem('power_warning_times');
      return saved ? JSON.parse(saved) : [10, 60]; // default: 10 seconds, 1 min (60s)
    } catch (e) {
      return [10, 60];
    }
  });

  const handleToggleWarningTime = (seconds: number) => {
    setWarningTimes(prev => {
      let updated;
      if (prev.includes(seconds)) {
        updated = prev.filter(t => t !== seconds);
      } else {
        updated = [...prev, seconds].sort((a,b) => a - b);
      }
      localStorage.setItem('power_warning_times', JSON.stringify(updated));
      const getLabel = (s: number) => s === 10 
        ? (lang === 'en' ? 'Beep every second 10s before' : '10초 전 매초 비프') 
        : formatKoreanTime(s) + (lang === 'en' ? ' before' : ' 전 단발 알림음');
      if (lang === 'en') {
        addLog(`Warning config updated: [${getLabel(seconds)}] ${prev.includes(seconds) ? 'disabled' : 'enabled'}`);
      } else {
        addLog(`경고 설정 변동: [${getLabel(seconds)}] ${prev.includes(seconds) ? '해제됨' : '지정됨'}`);
      }
      return updated;
    });
  };

  // Custom Grace Warning Duration settings
  const [graceSeconds, setGraceSeconds] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('power_grace_seconds');
      return saved ? parseInt(saved) : 10;
    } catch {
      return 10;
    }
  });

  const handleGraceSecondsChange = (seconds: number) => {
    setGraceSeconds(seconds);
    try {
      localStorage.setItem('power_grace_seconds', seconds.toString());
    } catch {}
    if (lang === 'en') {
      addLog(`Reservation warning duration set to: ${seconds} seconds`);
    } else {
      addLog(`예약작업 실행 전 안내 대기 시간이 ${seconds}초로 변경되었습니다.`);
    }
  };

  // Force close apps flag (Windows /f param) - Enabled by default
  const [forceCloseEnabled, setForceCloseEnabled] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('power_force_close_enabled');
      return saved !== null ? saved === 'true' : true; // Default: Enabled (true)
    } catch {
      return true;
    }
  });

  const handleToggleForceClose = () => {
    setForceCloseEnabled(prev => {
      const updated = !prev;
      try {
        localStorage.setItem('power_force_close_enabled', updated ? 'true' : 'false');
      } catch {}
      if (lang === 'en') {
        addLog(`Force Close apps flag (/f): ${updated ? 'Enabled' : 'Disabled'}`);
      } else {
        addLog(`실행 중인 앱 강제 종료 플래그 (/f): ${updated ? '활성화됨 (기본)' : '비활성화됨'}`);
      }
      return updated;
    });
  };
  
  // Navigation & Explorer layout properties
  const [activeFolder, setActiveFolder] = useState<ExplorerFolder>('timer');
  const [historyStack, setHistoryStack] = useState<ExplorerFolder[]>(['timer']);
  const [historyIndex, setHistoryIndex] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [currentTimeText, setCurrentTimeText] = useState<string>('');

  // Core Timer logic
  const [powerMode, setPowerMode] = useState<PowerMode>('shutdown');
  const [runType, setRunType] = useState<'timer' | 'schedule'>('timer');
  const [timerState, setTimerState] = useState<TimerState>('idle');
  const [totalSeconds, setTotalSeconds] = useState<number>(1800); // Default 30 mins (1800s)
  const [secondsRemaining, setSecondsRemaining] = useState<number>(1800);

  // Manual inputs
  const [inputH, setInputH] = useState<number>(0);
  const [inputM, setInputM] = useState<number>(30);
  const [inputS, setInputS] = useState<number>(0);

  // Terminal Logs
  const [logs, setLogs] = useState<string[]>([]);

  // Simulation View
  const [showSimulator, setShowSimulator] = useState<boolean>(false);

  // Custom Notification state
  const [notification, setNotification] = useState<{ message: string; type: 'info' | 'error' | 'success' } | null>(null);

  const triggerNotification = (message: string, type: 'info' | 'error' | 'success' = 'info') => {
    setNotification({ message, type });
  };

  // Real-time System Telemetry from Backend API
  const [systemStatus, setSystemStatus] = useState<{
    cpu: number;
    memory: { total: number; free: number; used: number; pct: number };
    disk: { total: number; free: number; used: number; pct: number };
    network: { online: boolean; latency: number };
    uptime: number;
    platform: string;
  } | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/system-status');
        if (res.ok) {
          const data = await res.json();
          setSystemStatus(data);
        }
      } catch (err) {
        // Fallback simulated metrics for non-hosted sandboxes
        setSystemStatus({
          cpu: Math.floor(12 + Math.random() * 8),
          memory: {
            total: 16 * 1024 * 1024 * 1024,
            free: 9 * 1024 * 1024 * 1024,
            used: 7 * 1024 * 1024 * 1024,
            pct: 43
          },
          disk: {
            total: 256 * 1024 * 1024 * 1024,
            free: 148 * 1024 * 1024 * 1024,
            used: 108 * 1024 * 1024 * 1024,
            pct: 42
          },
          network: {
            online: navigator.onLine,
            latency: 15
          },
          uptime: 7200,
          platform: 'win32'
        });
      }
    };

    fetchStatus();
    const intervalId = setInterval(fetchStatus, 3000);
    return () => clearInterval(intervalId);
  }, []);

  // Compact floating widget background opacity state (30 to 100)
  const [widgetOpacity, setWidgetOpacity] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('power_widget_opacity');
      return saved ? parseInt(saved, 10) : 100;
    } catch {
      return 100;
    }
  });

  // Option to show current time in compact always-on-top window
  const [showCurrentTimeCompact, setShowCurrentTimeCompact] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('power_show_current_time_compact');
      return saved ? saved === 'true' : false;
    } catch {
      return false;
    }
  });

  // Main window background opacity state (20 to 100)
  const [mainOpacity, setMainOpacity] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('power_main_opacity');
      return saved ? parseInt(saved, 10) : 100;
    } catch {
      return 100;
    }
  });

  // Active App Font style ('font-sans', 'font-display', 'font-mono', 'font-serif')
  const [selectedFont, setSelectedFont] = useState<string>(() => {
    try {
      const saved = localStorage.getItem('power_selected_font');
      return saved || 'font-malgun';
    } catch {
      return 'font-malgun';
    }
  });

  // Timer Ref for precision interval
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Sidebar drag-scroll (grab to scroll) state & refs
  const sidebarRef = useRef<HTMLDivElement | null>(null);
  const isDraggingSidebar = useRef<boolean>(false);
  const startDragY = useRef<number>(0);
  const startScrollTop = useRef<number>(0);
  const [isSidebarGrabbing, setIsSidebarGrabbing] = useState<boolean>(false);

  const handleSidebarMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!sidebarRef.current) return;
    isDraggingSidebar.current = true;
    setIsSidebarGrabbing(true);
    startDragY.current = e.pageY - sidebarRef.current.offsetTop;
    startScrollTop.current = sidebarRef.current.scrollTop;
  };

  const handleSidebarMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDraggingSidebar.current || !sidebarRef.current) return;
    e.preventDefault();
    const y = e.pageY - sidebarRef.current.offsetTop;
    const walkY = (y - startDragY.current) * 1.5; // Scroll speed sensitivity multiplier
    sidebarRef.current.scrollTop = startScrollTop.current - walkY;
  };

  const handleSidebarMouseUpOrLeave = () => {
    isDraggingSidebar.current = false;
    setIsSidebarGrabbing(false);
  };

  // Theme configuration definitions
  const themeConfigs: Record<ThemeType, {
    bg: string;
    windowBg: string;
    titleBar: string;
    sidebarBg: string;
    mainAreaBg: string;
    border: string;
    text: string;
    subtext: string;
    accentBg: string;
    statusBarBg: string;
    itemHover: string;
    name: string;
    panelBg: string;
    panelBorder: string;
    inputContainerBg: string;
    inputBox: string;
    btnInactive: string;
    subPanelBg: string;
    presetBtn: string;
    favoritesBoxBg: string;
    logsPanelBg: string;
    logsInnerBg: string;
    logsLineHover: string;
  }> = {
    dark: {
      bg: 'bg-[#0a0d16] text-[#e1e4ed]',
      windowBg: 'bg-[#181a24] border-[#2d3142]',
      titleBar: 'bg-gradient-to-r from-[#11131a] to-[#1c202d] text-gray-100 border-[#2b2f3d]',
      sidebarBg: 'bg-[#0f111a] border-r border-[#262938]',
      mainAreaBg: 'bg-[#141620]',
      border: 'border-[#2a2d3d]',
      text: 'text-[#e1e4ed]',
      subtext: 'text-gray-400',
      accentBg: 'bg-blue-600 hover:bg-blue-500 text-white',
      statusBarBg: 'bg-[#0d0e15] border-t border-[#1e212f] text-gray-400',
      itemHover: 'hover:bg-[#202436]',
      name: '윈도우 11 Fluent 다크',
      panelBg: 'bg-[#1f2330]',
      panelBorder: 'border-[#2d3142]/80',
      inputContainerBg: 'bg-[#11131a] border-[#2d3142]',
      inputBox: 'bg-black/40 text-white border-gray-700',
      btnInactive: 'bg-[#1a1d29] hover:bg-[#252a3b] text-gray-300 border border-[#2d3142]/65',
      subPanelBg: 'bg-[#181a24] border-[#2d3142]',
      presetBtn: 'border-gray-800 hover:border-blue-500 bg-black/20 hover:text-blue-400 text-gray-300',
      favoritesBoxBg: 'border-gray-800/50 bg-black/15',
      logsPanelBg: 'border-gray-800 bg-[#1a1d29]',
      logsInnerBg: 'bg-black/30',
      logsLineHover: 'hover:bg-zinc-800'
    },
    gray: {
      bg: 'bg-[#1e293b] text-[#f8fafc]',
      windowBg: 'bg-[#334155] border-[#475569] shadow-2xl',
      titleBar: 'bg-gradient-to-r from-[#1e293b] to-[#334155] text-white border-b border-[#475569]',
      sidebarBg: 'bg-[#1e293b] border-r border-[#475569]',
      mainAreaBg: 'bg-[#334155]',
      border: 'border-[#475569]',
      text: 'text-[#f8fafc]',
      subtext: 'text-[#e2e8f0]',
      accentBg: 'bg-[#475569] hover:bg-[#64748b] text-white border border-[#475569]',
      statusBarBg: 'bg-[#1e293b] border-t border-[#475569] text-[#f1f5f9]',
      itemHover: 'hover:bg-[#475569]',
      name: '심플 그레이',
      panelBg: 'bg-[#1e293b]/80',
      panelBorder: 'border-[#475569]',
      inputContainerBg: 'bg-[#0f172a]/40 border-[#475569]',
      inputBox: 'bg-[#1e293b] text-[#f8fafc] border-[#475569]',
      btnInactive: 'bg-[#273142] hover:bg-[#344156] text-slate-100 border border-[#475569]',
      subPanelBg: 'bg-[#242f41] border-[#475569]',
      presetBtn: 'border-[#64748b] hover:border-blue-400 bg-black/30 hover:text-blue-300 text-slate-100 font-medium',
      favoritesBoxBg: 'border-[#475569] bg-black/20',
      logsPanelBg: 'border-[#475569] bg-[#242f41]',
      logsInnerBg: 'bg-[#1e293b]',
      logsLineHover: 'hover:bg-[#334155]'
    },
    beige: {
      bg: 'bg-[#f5f0e6] text-[#2c2217]',
      windowBg: 'bg-[#faf6ee] border-[#c8bcaa] shadow-xl',
      titleBar: 'bg-gradient-to-r from-[#ebe2d4] to-[#ded4c3] text-[#2c2217] border-b border-[#c8bcaa]',
      sidebarBg: 'bg-[#ebe2d4] border-r border-[#c8bcaa]',
      mainAreaBg: 'bg-[#faf6ee]',
      border: 'border-[#c8bcaa]',
      text: 'text-[#2c2217]',
      subtext: 'text-[#5c4d38]',
      accentBg: 'bg-[#6e5d47] hover:bg-[#584835] text-white border border-[#584835]',
      statusBarBg: 'bg-[#ebe2d4] border-t border-[#c8bcaa] text-[#3d3222]',
      itemHover: 'hover:bg-[#f5f0e6]',
      name: '아늑한 베이지',
      panelBg: 'bg-[#eee7da]',
      panelBorder: 'border-[#c8bcaa]',
      inputContainerBg: 'bg-white border-[#c8bcaa]',
      inputBox: 'bg-[#faf6ee] text-[#2c2217] border-[#c8bcaa] font-bold',
      btnInactive: 'bg-[#e8ded0] hover:bg-[#ded1c0] text-[#3d3222] border border-[#c8bcaa] font-semibold',
      subPanelBg: 'bg-[#f0e8dc] border-[#c8bcaa]',
      presetBtn: 'border-[#c8bcaa] hover:border-[#584835] bg-white hover:text-[#2c2217] text-[#3d3222] font-semibold',
      favoritesBoxBg: 'border-[#c8bcaa] bg-white',
      logsPanelBg: 'border-[#c8bcaa] bg-white',
      logsInnerBg: 'bg-[#faf6ee]',
      logsLineHover: 'hover:bg-[#eee7da]'
    }
  };

  const currentThemeConfig = themeConfigs[theme];

  const t = {
    title: lang === 'ko' ? '시스템 탐색기' : 'System Explorer',
    allFolders: lang === 'ko' ? '모든 폴더' : 'All Folders',
    quickAccess: lang === 'ko' ? '빠른 바로 가기 (Quick Access)' : 'Quick Access',
    thisPc: lang === 'ko' ? '내 PC (This PC)' : 'This PC',
    folderTimerDesc: lang === 'ko' ? '프로그램 파일 지연 배치 및 로컬 권한 펄스 매니저' : 'Program File Delay Batch and Local Permission Pulse Manager',
    powerActionMode: lang === 'ko' ? '전원 액션 모드 지정' : 'Power Action Mode Selection',
    alwaysOnTop: lang === 'ko' ? '항상 위에 핀' : 'Always on Top Pin',
    themeRotary: lang === 'ko' ? '테마 순환' : 'Cycle Theme',
    alarmSound: lang === 'ko' ? 'alarm 켬' : 'Alarm sound',
    alarmOn: lang === 'ko' ? 'alarm 켬' : 'Alarm On',
    alarmOff: lang === 'ko' ? 'alarm 끔' : 'Alarm Off',
    logBurn: lang === 'ko' ? '로그 소각' : 'Clear Logs',
    searchPlaceholder: lang === 'ko' ? '전원 검색...' : 'Search power...',
    parentDirectory: lang === 'ko' ? '상위 디렉터리 (시간 제어기)' : 'Up directly (Time Controller)',
    networkStatusOnline: lang === 'ko' ? '네트워크 상태 : 온라인' : 'Network Status: Online',
    networkDesc: lang === 'ko' ? '로컬 타이머 수면 감지 데몬이 가동 중입니다. 지정 시간이 만기되면 가상 정원 종료 시뮬레이터로 안전하고 편리하게 진입합니다.' : 'The local timer sleep detection daemon is running. When the scheduled time expires, the virtual power shutdown simulator is launched safely and conveniently.',
    timerStateStatus: {
      running: lang === 'ko' ? '수면예정' : 'Running',
      paused: lang === 'ko' ? '중지됨' : 'Paused',
      idle: lang === 'ko' ? '대기중' : 'Idle'
    },
    hours: lang === 'ko' ? '시' : 'Hr',
    mins: lang === 'ko' ? '분' : 'Min',
    secs: lang === 'ko' ? '초' : 'Sec',
    scheduledTimePrefix: lang === 'ko' ? '예정 시간:' : 'Scheduled Time:',
    warningTimesConfig: lang === 'ko' ? '사전 알림 주기 및 사운드 구성' : 'Notification & Sound Settings',
    warningTimesDesc: lang === 'ko' ? '예상 만기 직전 지정된 대기 시점에 경고 비프음이 연주되어 원격/수면 중 사전 피드백을 전달합니다.' : 'A warning beep plays at specified countdown markings before completion providing helpful feedback.',
    warningTimerUnit: lang === 'ko' ? '10초 전 매초 비프' : 'Beep every second 10s before',
    quickPresetsTitle: lang === 'ko' ? '원클릭 신속 배치 사전설정 (퀵 슬롯)' : 'One-Click Fast Presets (Quick Slots)',
    quickPresetsDesc: lang === 'ko' ? '미리 지정된 타이머 값을 클릭하여 즉각적으로 수면 전원 제어 예약을 가동합니다.' : 'Click any preset below to instantly trigger the power control timer.',
    widgetOpacityTitle: lang === 'ko' ? '위젯 투명도 조절' : 'Widget Opacity Control',
    widgetExitTitle: lang === 'ko' ? '위젯 종료 (상세 탐색기 복원)' : 'Exit Widget (Restore Standard Explorer)',
    startTimerBtn: lang === 'ko' ? '지연 수면제어 감시 타이머 예약 가동' : 'Start Delay Power Monitor Countdown',
    pauseTimerBtn: lang === 'ko' ? '일시 정지' : 'Pause',
    resumeTimerBtn: lang === 'ko' ? '다시 시작' : 'Resume',
    resetTimerBtn: lang === 'ko' ? '로그 세션 리셋 익스펜드' : 'Reset Timer Session',
    systemErrorPrefix: lang === 'ko' ? '⚠️ 경고: 대기 시간은 최소 1초 이상이어야 시작 가능합니다.' : '⚠️ Warning: Remaining duration must be at least 1 second to start.',
    logsNoticeSaved: lang === 'ko' ? '시스템 로그를 텍스트 파일(.txt)로 다운로드 완료했습니다.' : 'Successfully downloaded system logs to text file (.txt).',
    logsNoticeNoLogs: lang === 'ko' ? '⚠️ 다운로드할 로그가 없습니다.' : '⚠️ No logs to download.',
    logsTabTitleFile: lang === 'ko' ? '파일(F)' : 'File(F)',
    logsTabTitleEdit: lang === 'ko' ? '편집(E)' : 'Edit(E)',
    logsTabTitleFormat: lang === 'ko' ? '서식(O)' : 'Format(O)',
    logsTabTitleDownloadBtn: lang === 'ko' ? '텍스트 파일로 저장' : 'Save as .txt File',
    logsTabTitleClearBtn: lang === 'ko' ? '로그 완전 비우기' : 'Clear All Logs',
    logsEmpty: lang === 'ko' ? '기록된 시스템 트랙이 존재하지 않습니다.' : 'No system logs recorded.',
    localDiskC: lang === 'ko' ? '로컬 디스크 (C:)' : 'Local Disk (C:)',
    diskUsagePct: lang === 'ko' ? '42% 사용 중' : '42% in use',
  };

  const applyThemeStyles = (newTheme: ThemeType) => {
    document.body.className = ''; // Reset classes
    if (newTheme === 'dark') {
      document.body.style.backgroundColor = '#0a0d16';
      document.body.classList.add('dark-mode');
    } else if (newTheme === 'gray') {
      document.body.style.backgroundColor = '#1e293b';
    } else if (newTheme === 'beige') {
      document.body.style.backgroundColor = '#f5f0e6';
    }
  };

  const handleThemeChange = (newTheme: ThemeType) => {
    setTheme(newTheme);
    localStorage.setItem('power_theme', newTheme);
    applyThemeStyles(newTheme);
    const themeName = lang === 'en' 
      ? (newTheme === 'dark' ? 'Windows 11 Fluent Dark' : newTheme === 'gray' ? 'Simple Gray' : 'Cozy Beige')
      : themeConfigs[newTheme].name;
    addLog(lang === 'en' ? `Theme modified: [${themeName}]` : `테마 변경 완료: [${themeName}]`);
  };

  // Sync real-time clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const optionsStr = now.toLocaleDateString(lang === 'en' ? 'en-US' : 'ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' });
      const timeStr = now.toLocaleTimeString(lang === 'en' ? 'en-US' : 'ko-KR', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setCurrentTimeText(`${optionsStr} ${timeStr}`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, [lang]);

  // Initialize Theme and Log
  useEffect(() => {
    addLog(lang === 'en' ? 'System Sleep & Power Control Explorer fully loaded.' : '시스템 수면 전원 제어 탐색기 로드 완료.');
    addLog((lang === 'en' ? 'Current Time: ' : '현재 시간: ') + new Date().toLocaleTimeString(lang === 'en' ? 'en-US' : 'ko-KR'));
    
    const saved = localStorage.getItem('power_theme') as ThemeType;
    const initialTheme = (saved && ['dark', 'gray', 'beige'].includes(saved)) ? saved : 'beige';
    setTheme(initialTheme);
    applyThemeStyles(initialTheme);
  }, []);

  // Hourly Chime Feature (정각 알림 기능)
  const lastChimedHourRef = useRef<number>(-1);
  useEffect(() => {
    const checkChime = () => {
      const now = new Date();
      const mins = now.getMinutes();
      const secs = now.getSeconds();
      const curHour = now.getHours();

      if (hourlyChime && mins === 0 && secs === 0 && lastChimedHourRef.current !== curHour) {
        lastChimedHourRef.current = curHour;
        if (soundEnabled) {
          playTestSound(soundTheme);
        }
        const hourStr = curHour.toString().padStart(2, '0') + ':00';
        const msg = lang === 'en'
          ? `🔔 [Hourly Chime] It is now ${hourStr}`
          : `🔔 [정각 알림] 현재 시각: ${hourStr} 입니다.`;
        addLog(msg);
        triggerNotification(msg, 'info');
      }
    };
    const interval = setInterval(checkChime, 1000);
    return () => clearInterval(interval);
  }, [hourlyChime, soundEnabled, soundTheme, lang]);

  // Startup Today's Scheduled Tasks Alert Feature (부팅/시작 시 오늘 예약 작업 알림)
  useEffect(() => {
    if (!startupTasksAlert) return;
    const timer = setTimeout(() => {
      try {
        const stored = localStorage.getItem('system_power_scheduler_rules_v2');
        if (stored) {
          const rules = JSON.parse(stored);
          const today = new Date();
          const todayDayOfWeek = today.getDay(); // 0: Sun, 1: Mon, ...
          const yyyy = today.getFullYear();
          const mm = String(today.getMonth() + 1).padStart(2, '0');
          const dd = String(today.getDate()).padStart(2, '0');
          const todayDateStr = `${yyyy}-${mm}-${dd}`;

          const todays = rules.filter((r: any) => {
            if (!r.isActive) return false;
            if (r.type === 'daily') return true;
            if (r.type === 'weekly' && Array.isArray(r.days)) return r.days.includes(todayDayOfWeek);
            if (r.type === 'once' && r.date === todayDateStr) return true;
            if (r.type === 'interval') return true;
            return false;
          });

          if (todays.length > 0) {
            setTodayTasks(todays);
            setTodayTasksModalOpen(true);
            addLog(lang === 'en'
              ? `Startup check: Found ${todays.length} active scheduled power task(s) for today.`
              : `시작 작업 점검: 오늘 실행 예정인 전원 제어 예약 작업이 ${todays.length}건 발견되었습니다.`);
          }
        }
      } catch (e) {
        console.error(e);
      }
    }, 2000);
    return () => clearTimeout(timer);
  }, [startupTasksAlert, lang]);

  // Settings Open, Cancel, Confirm handlers
  const handleOpenSettings = () => {
    setDraftSettings({
      theme,
      soundTheme,
      showCurrentTimeCompact,
      widgetOpacity,
      mainOpacity,
      selectedFont,
      graceSeconds,
      hourlyChime,
      startupTasksAlert,
      widgetDesign,
      widgetWidth,
      clockFontSize,
      timerFontSize,
      forceCloseEnabled
    });
    setIsSettingsOpen(true);
  };

  const handleCancelSettings = () => {
    // Revert without applying
    setIsSettingsOpen(false);
  };

  const handleConfirmSettings = () => {
    if (!draftSettings) {
      setIsSettingsOpen(false);
      return;
    }
    if (draftSettings.theme !== theme) {
      setTheme(draftSettings.theme);
      localStorage.setItem('power_theme', draftSettings.theme);
      applyThemeStyles(draftSettings.theme);
    }
    if (draftSettings.soundTheme !== soundTheme) {
      setSoundTheme(draftSettings.soundTheme);
      localStorage.setItem('power_sound_theme', draftSettings.soundTheme);
    }
    if (draftSettings.showCurrentTimeCompact !== showCurrentTimeCompact) {
      setShowCurrentTimeCompact(draftSettings.showCurrentTimeCompact);
      localStorage.setItem('power_show_current_time_compact', draftSettings.showCurrentTimeCompact ? 'true' : 'false');
    }
    if (draftSettings.widgetOpacity !== widgetOpacity) {
      setWidgetOpacity(draftSettings.widgetOpacity);
      localStorage.setItem('power_widget_opacity', draftSettings.widgetOpacity.toString());
    }
    if (draftSettings.mainOpacity !== mainOpacity) {
      setMainOpacity(draftSettings.mainOpacity);
      localStorage.setItem('power_main_opacity', draftSettings.mainOpacity.toString());
    }
    if (draftSettings.selectedFont !== selectedFont) {
      setSelectedFont(draftSettings.selectedFont);
      localStorage.setItem('power_selected_font', draftSettings.selectedFont);
    }
    if (draftSettings.graceSeconds !== graceSeconds) {
      setGraceSeconds(draftSettings.graceSeconds);
      localStorage.setItem('power_grace_seconds', draftSettings.graceSeconds.toString());
    }
    if (draftSettings.hourlyChime !== hourlyChime) {
      setHourlyChime(draftSettings.hourlyChime);
      localStorage.setItem('power_hourly_chime', draftSettings.hourlyChime ? 'true' : 'false');
    }
    if (draftSettings.startupTasksAlert !== startupTasksAlert) {
      setStartupTasksAlert(draftSettings.startupTasksAlert);
      localStorage.setItem('power_startup_tasks_alert', draftSettings.startupTasksAlert ? 'true' : 'false');
    }
    if (draftSettings.widgetDesign !== widgetDesign) {
      setWidgetDesign(draftSettings.widgetDesign);
      localStorage.setItem('power_widget_design', draftSettings.widgetDesign);
    }
    if (draftSettings.widgetWidth !== widgetWidth) {
      setWidgetWidth(draftSettings.widgetWidth);
      localStorage.setItem('power_widget_width', draftSettings.widgetWidth.toString());
    }
    if (draftSettings.clockFontSize !== clockFontSize) {
      setClockFontSize(draftSettings.clockFontSize);
      localStorage.setItem('power_clock_font_size', draftSettings.clockFontSize.toString());
    }
    if (draftSettings.timerFontSize !== timerFontSize) {
      setTimerFontSize(draftSettings.timerFontSize);
      localStorage.setItem('power_timer_font_size', draftSettings.timerFontSize.toString());
    }
    if (draftSettings.forceCloseEnabled !== forceCloseEnabled) {
      setForceCloseEnabled(draftSettings.forceCloseEnabled);
      localStorage.setItem('power_force_close_enabled', draftSettings.forceCloseEnabled ? 'true' : 'false');
    }

    addLog(lang === 'en' ? 'Settings preferences applied and saved successfully.' : '환경 설정이 성공적으로 저장 및 적용되었습니다.');
    triggerNotification(lang === 'en' ? 'Settings applied!' : '설정이 저장되었습니다!', 'success');
    setIsSettingsOpen(false);
  };

  // Notification Auto-dismiss after 3.5 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 3500);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  // Sync inputs with state when timer is idle
  useEffect(() => {
    if (timerState === 'idle') {
      const calculatedSec = (inputH * 3600) + (inputM * 60) + inputS;
      setTotalSeconds(calculatedSec);
      setSecondsRemaining(calculatedSec);
    }
  }, [inputH, inputM, inputS, timerState]);

  // Handle countdown tick
  useEffect(() => {
    if (timerState === 'running') {
      timerRef.current = setInterval(() => {
        setSecondsRemaining(prev => {
          if (prev <= 1) {
            clearInterval(timerRef.current!);
            handleTimerComplete();
            return 0;
          }
          
          if (soundEnabled) {
            const nextSec = prev - 1;
            // graceSeconds 이하 연속 비프: warningTimes에 10이 있고, 다음 초가 graceSeconds 이하일 때 매초 비프(0초 제외)
            if (nextSec <= graceSeconds && nextSec > 0 && warningTimes.includes(10)) {
              playWarningTick();
            } else if (warningTimes.includes(nextSec)) {
              // 지정한 특정 초 전일 때 경고 멜로디 연주
              playAlertChime();
              if (lang === 'en') {
                addLog(`🔔 [Warning] Scheduled action executes in ${formatKoreanTime(nextSec)}!`);
              } else {
                addLog(`🔔 [사전 경고 알림] 예정 동작 실행 ${formatKoreanTime(nextSec)} 전입니다!`);
              }
            }
          }
          
          if (prev % 60 === 0 && prev > 0) {
            if (lang === 'en') {
              addLog(`Time remaining: ${Math.floor(prev / 60)} mins left...`);
            } else {
              addLog(`남은 대기 시간: ${Math.floor(prev / 60)}분 전...`);
            }
          }

          return prev - 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [timerState, soundEnabled, warningTimes, soundTheme, graceSeconds]);

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString('ko-KR', { hour12: false });
    setLogs(prev => [`[${timestamp}] ${msg}`, ...prev.slice(0, 49)]);
  };

  const playTestSound = (theme: 'classic' | 'scifi' | 'cozy') => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      
      if (theme === 'classic') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
        osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.15); // A5
        gain.gain.setValueAtTime(0.06, audioCtx.currentTime);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.35);
      } else if (theme === 'scifi') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(1000, audioCtx.currentTime); 
        osc.frequency.exponentialRampToValueAtTime(2000, audioCtx.currentTime + 0.25);
        gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.3);
      } else { // cozy
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
        osc.frequency.setValueAtTime(783.99, audioCtx.currentTime + 0.12); // G5
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.35);
      }
    } catch (e) {}
  };

  const playWarningTick = () => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      
      if (soundTheme === 'classic') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(1000, audioCtx.currentTime); 
        gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
      } else if (soundTheme === 'scifi') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(2000, audioCtx.currentTime); 
        gain.gain.setValueAtTime(0.02, audioCtx.currentTime);
      } else { // cozy
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
        gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
      }
      
      osc.start();
      osc.stop(audioCtx.currentTime + 0.08);
    } catch (e) {}
  };

  const playAlertChime = () => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      
      if (soundTheme === 'classic') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
        osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.15); // A5
        gain.gain.setValueAtTime(0.06, audioCtx.currentTime);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.4);
      } else if (soundTheme === 'scifi') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(1200, audioCtx.currentTime); 
        osc.frequency.exponentialRampToValueAtTime(1800, audioCtx.currentTime + 0.35);
        gain.gain.setValueAtTime(0.03, audioCtx.currentTime);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.4);
      } else { // cozy
        osc.type = 'sine';
        osc.frequency.setValueAtTime(698.46, audioCtx.currentTime); // F5
        osc.frequency.setValueAtTime(932.33, audioCtx.currentTime + 0.15); // Bb5
        gain.gain.setValueAtTime(0.06, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.45);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.5);
      }
    } catch (e) {}
  };

  const playChime = () => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      
      if (soundTheme === 'classic') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
        osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.15); // E5
        osc.frequency.setValueAtTime(783.99, audioCtx.currentTime + 0.3); // G5
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.6);
      } else if (soundTheme === 'scifi') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(880, audioCtx.currentTime); 
        osc.frequency.setValueAtTime(1760, audioCtx.currentTime + 0.15); 
        osc.frequency.setValueAtTime(2200, audioCtx.currentTime + 0.3); 
        gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.5);
      } else { // cozy
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
        osc.frequency.setValueAtTime(698.46, audioCtx.currentTime + 0.15); // F5
        osc.frequency.setValueAtTime(880.00, audioCtx.currentTime + 0.3); // A5
        osc.frequency.setValueAtTime(1046.50, audioCtx.currentTime + 0.45); // C6
        gain.gain.setValueAtTime(0.07, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.75);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.8);
      }
    } catch (e) {}
  };

  const getPowerModeKorean = (m: PowerMode) => {
    if (lang === 'en') {
      switch (m) {
        case 'shutdown': return 'System Shutdown';
        case 'restart': return 'System Restart';
        case 'sleep': return 'Enter Sleep Mode';
        case 'screenoff': return 'Turn Off Monitor';
        case 'logout': return 'Account Log Out';
        case 'alarm': return 'Trigger Sound Alarm';
      }
    }
    switch (m) {
      case 'shutdown': return '시스템 종료';
      case 'restart': return '시스템 재시작';
      case 'sleep': return '절전 대기 진입';
      case 'screenoff': return '모니터 화면 끄기';
      case 'logout': return '계정 로그아웃';
      case 'alarm': return '예약 사운드 알람';
    }
  };

  const handleTriggerRule = (mode: PowerMode, label: string, forceCloseApps: boolean, warningNotification: boolean) => {
    setPowerMode(mode);
    if (lang === 'en') {
      addLog(`📢 [Scheduler Offline Trigger] "${label}" automation rule invoked. (Mode: ${getPowerModeKorean(mode)})`);
    } else {
      addLog(`📢 [스케줄 오프라인 트리거] "${label}" 자동화 예약이 격발되었습니다. (모드: ${getPowerModeKorean(mode)})`);
    }
    
    if (soundEnabled) {
      if (warningNotification) {
        playWarningTick();
      }
      playChime();
    }
    setShowSimulator(true);
  };

  const handleTimerComplete = () => {
    setTimerState('complete');
    if (lang === 'en') {
      addLog(`Time completed! Launching [${getPowerModeKorean(powerMode)}] virtual simulation.`);
    } else {
      addLog(`시간 마감! [${getPowerModeKorean(powerMode)}] 가상 시뮬레이션을 가동합니다.`);
    }
    if (soundEnabled) {
      playChime();
    }
    setShowSimulator(true);
  };

  const handleQuickPreset = (minutes: number) => {
    const sec = minutes * 60;
    setTotalSeconds(sec);
    setSecondsRemaining(sec);
    
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    setInputH(h);
    setInputM(m);
    setInputS(0);

    setTimerState('running');
    if (lang === 'en') {
      addLog(`Instant Timer running: ${minutes}m quick preset scheduled (${getPowerModeKorean(powerMode)}).`);
    } else {
      addLog(`즉시 타이머 구동: ${minutes}분 퀵 슬롯 예약 설정됨 (${getPowerModeKorean(powerMode)}).`);
    }
    
    // Switch view to Timer Controller to allow them to see countdown!
    navigateToFolder('timer');
  };

  const handleFavoriteSelect = (selectedMode: PowerMode, durationSec: number) => {
    setPowerMode(selectedMode);
    setTotalSeconds(durationSec);
    setSecondsRemaining(durationSec);

    const h = Math.floor(durationSec / 3600);
    const m = Math.floor((durationSec % 3600) / 60);
    const s = durationSec % 60;
    setInputH(h);
    setInputM(m);
    setInputS(s);

    setTimerState('running');
    if (lang === 'en') {
      addLog(`Favorite preset triggered: [${getPowerModeKorean(selectedMode)}] for ${Math.floor(durationSec / 60)} mins.`);
    } else {
      addLog(`즐겨찾기 원클릭 즉시 가동: [${getPowerModeKorean(selectedMode)}] ${Math.floor(durationSec / 60)}분.`);
    }
    navigateToFolder('timer');
  };

  const cycleTheme = () => {
    const list: ThemeType[] = ['dark', 'gray', 'beige'];
    const nextIdx = (list.indexOf(theme) + 1) % list.length;
    handleThemeChange(list[nextIdx]);
  };

  const toggleAlwaysOnTop = () => {
    const updated = !alwaysOnTop;
    setAlwaysOnTop(updated);
    try {
      localStorage.setItem('power_always_on_top', String(updated));
    } catch {}
    if (lang === 'en') {
      addLog(updated ? 'Compact floating widget mode activated.' : 'Explorer desktop view restored.');
    } else {
      addLog(updated ? '컴팩트 플로팅 위젯 모드 활성화.' : '탐색기 데스크톱 뷰 복구.');
    }
  };

  const toggleSoundEnabled = () => {
    const updated = !soundEnabled;
    setSoundEnabled(updated);
    try {
      localStorage.setItem('power_sound_enabled', String(updated));
    } catch {}
  };

  const handleWidgetOpacityChange = (val: number) => {
    setWidgetOpacity(val);
    try {
      localStorage.setItem('power_widget_opacity', String(val));
    } catch {}
  };

  const handleShowCurrentTimeCompactChange = (val: boolean) => {
    setShowCurrentTimeCompact(val);
    try {
      localStorage.setItem('power_show_current_time_compact', String(val));
    } catch {}
    if (lang === 'en') {
      addLog(val ? 'Show Current Time option enabled.' : 'Show Current Time option disabled.');
    } else {
      addLog(val ? '현재 시간 표시 옵션이 활성화되었습니다.' : '현재 시간 표시 옵션이 비활성화되었습니다.');
    }
  };

  const handleMainOpacityChange = (val: number) => {
    setMainOpacity(val);
    try {
      localStorage.setItem('power_main_opacity', String(val));
    } catch {}
  };

  const handleFontChange = (val: string) => {
    setSelectedFont(val);
    try {
      localStorage.setItem('power_selected_font', val);
    } catch {}
    
    let fontNameEn = '';
    let fontNameKo = '';
    switch(val) {
      case 'font-sans': fontNameEn = 'Inter (Sans)'; fontNameKo = 'Inter (산세리프)'; break;
      case 'font-display': fontNameEn = 'Space Grotesk'; fontNameKo = 'Space Grotesk (디스플레이)'; break;
      case 'font-mono': fontNameEn = 'JetBrains Mono'; fontNameKo = 'JetBrains Mono (고정폭)'; break;
      case 'font-serif': fontNameEn = 'Myeongjo (Serif)'; fontNameKo = '나눔명조 (세리프)'; break;
      case 'font-malgun': fontNameEn = 'Malgun Gothic'; fontNameKo = '맑은 고딕'; break;
      case 'font-gulim': fontNameEn = 'Gulim'; fontNameKo = '굴림'; break;
      case 'font-batang': fontNameEn = 'Batang'; fontNameKo = '바탕'; break;
    }
    
    if (lang === 'en') {
      addLog(`Font changed to ${fontNameEn}.`);
    } else {
      addLog(`폰트가 ${fontNameKo}로 변경되었습니다.`);
    }
  };

  const formatTimeStr = (totalSecs: number) => {
    const h = Math.floor(totalSecs / 3600);
    const m = Math.floor((totalSecs % 3600) / 60);
    const s = totalSecs % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const formatKoreanTime = (totalSecs: number) => {
    const h = Math.floor(totalSecs / 3600);
    const m = Math.floor((totalSecs % 3600) / 60);
    const s = totalSecs % 60;
    
    const elements = [];
    if (lang === 'en') {
      if (h > 0) elements.push(`${h}h`);
      if (m > 0) elements.push(`${m}m`);
      if (s > 0 || elements.length === 0) elements.push(`${s}s`);
    } else {
      if (h > 0) elements.push(`${h}시간`);
      if (m > 0) elements.push(`${m}분`);
      if (s > 0 || elements.length === 0) elements.push(`${s}초`);
    }
    return elements.join(' ');
  };

  const handleStartTimer = () => {
    if (runType === 'timer') {
      const total = (inputH * 3600) + (inputM * 60) + inputS;
      if (total <= 0) {
        if (lang === 'en') {
          addLog('⚠️ Warning: Remaining duration must be at least 1 second to start.');
        } else {
          addLog('⚠️ 경고: 대기 시간은 최소 1초 이상이어야 시작 가능합니다.');
        }
        return;
      }
      setTotalSeconds(total);
      setSecondsRemaining(total);
      setTimerState('running');
      if (lang === 'en') {
        addLog(`Timer started: ${formatTimeStr(total)} remains until [${powerMode}].`);
      } else {
        addLog(`타이머 가동 시작: ${formatKoreanTime(total)} 후 [${getPowerModeKorean(powerMode)}].`);
      }
    } else {
      if (inputH < 0 || inputH > 23 || inputM < 0 || inputM > 59) {
        if (lang === 'en') {
          addLog('⚠️ Error: Please enter hours between 0-23 and minutes between 0-59.');
        } else {
          addLog('⚠️ 오류: 시는 0~23 사이, 분은 0~59 사이로 입력하여 주십시오.');
        }
        return;
      }
      const now = new Date();
      const targetTime = new Date(now);
      targetTime.setHours(inputH, inputM, 0, 0);
      if (targetTime.getTime() <= now.getTime()) {
        targetTime.setDate(targetTime.getDate() + 1);
      }
      const total = Math.floor((targetTime.getTime() - now.getTime()) / 1000);
      setTotalSeconds(total);
      setSecondsRemaining(total);
      setTimerState('running');
      const timeLabel = targetTime.toLocaleTimeString(lang === 'en' ? 'en-US' : 'ko-KR', { hour: '2-digit', minute: '2-digit' });
      if (lang === 'en') {
        addLog(`Schedule started: Action [${powerMode}] will run at ${timeLabel} (in ${formatTimeStr(total)}).`);
      } else {
        addLog(`특정 시각 예약 가동 시작: 설정 시각 ${timeLabel} 에 컴퓨터 [${getPowerModeKorean(powerMode)}] 예약 진행됨.`);
      }
    }
  };

  const handlePauseTimer = () => {
    setTimerState('paused');
    if (lang === 'en') {
      addLog('Timer has been paused.');
    } else {
      addLog('타이머가 일시 정지되었습니다.');
    }
  };

  const handleResumeTimer = () => {
    setTimerState('running');
    if (lang === 'en') {
      addLog('Timer has been resumed.');
    } else {
      addLog('타이머가 다시 시작되었습니다.');
    }
  };

  const handleResetTimer = () => {
    setTimerState('idle');
    setSecondsRemaining(totalSeconds);
    if (lang === 'en') {
      addLog('Timer session restored and initialized.');
    } else {
      addLog('타이머 세션 복구 및 초기화 완료.');
    }
  };

  const handleModeChange = (mode: PowerMode) => {
    setPowerMode(mode);
    if (lang === 'en') {
      addLog(`Target action changed to [${getPowerModeKorean(mode)}].`);
    } else {
      addLog(`대상 동작을 [${getPowerModeKorean(mode)}] 로 변경하였습니다.`);
    }
  };

  const handleCleanLogs = () => {
    setLogs([]);
    if (lang === 'en') {
      addLog('Memory logs permanently cleared.');
    } else {
      addLog('메모리 보존 로그 파일을 영구 소각 완료했습니다.');
    }
  };

  const handleDownloadLogs = () => {
    if (logs.length === 0) {
      if (lang === 'en') {
        addLog('⚠️ No logs available for download.');
      } else {
        addLog('⚠️ 다운로드할 로그가 없습니다.');
      }
      return;
    }
    const logText = logs.slice().reverse().join('\r\n'); // chronological order since logs is prepended
    const blob = new Blob([logText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `system_power_logs_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    if (lang === 'en') {
      addLog('System logs successfully downloaded as a text file (.txt).');
    } else {
      addLog('시스템 로그를 텍스트 파일(.txt)로 다운로드 완료했습니다.');
    }
  };

  // SVG progressive dash
  const getStrokeDashOffset = () => {
    const strokeWidth = 8;
    const radius = 80;
    const circumference = 2 * Math.PI * radius;
    const percentage = secondsRemaining / (totalSeconds || 1);
    return circumference - (percentage * circumference);
  };

  // Browser-styled Back/Forward Nav Stack
  const navigateToFolder = (folder: ExplorerFolder) => {
    if (folder === activeFolder) return;
    
    const newHistory = historyStack.slice(0, historyIndex + 1);
    const updatedHistory = [...newHistory, folder];
    setHistoryStack(updatedHistory);
    setHistoryIndex(updatedHistory.length - 1);
    setActiveFolder(folder);
    if (lang === 'en') {
      addLog(`Path changed: [My PC > Power Controller > ${getFolderLabel(folder)}]`);
    } else {
      addLog(`경로 이동: [내 PC > 전원제어기 > ${getFolderLabel(folder)}]`);
    }
  };

  const handleGoBack = () => {
    if (historyIndex > 0) {
      const idx = historyIndex - 1;
      setHistoryIndex(idx);
      setActiveFolder(historyStack[idx]);
    }
  };

  const handleGoForward = () => {
    if (historyIndex < historyStack.length - 1) {
      const idx = historyIndex + 1;
      setHistoryIndex(idx);
      setActiveFolder(historyStack[idx]);
    }
  };

  const handleGoUp = () => {
    // Navigates to the first tab (Timer) as parent directory
    navigateToFolder('timer');
  };

  const getFolderLabel = (f: ExplorerFolder) => {
    if (lang === 'en') {
      switch (f) {
        case 'timer': return 'Time_Controller.exe';
        case 'scheduler': return 'Task_Scheduler.msc';
        case 'packager': return 'Single_File_Packager.lnk';
        case 'command': return 'Terminal_CLI_Command.cmd';
        case 'favorites': return 'Favorites_Folder';
        case 'logs': return 'notepad_logs.txt';
      }
    }
    switch (f) {
      case 'timer': return '시간_제어기.exe';
      case 'scheduler': return '작업_스케줄러.msc';
      case 'packager': return '단일_파일_패키저.lnk';
      case 'command': return '터미널_CLI_명령.cmd';
      case 'favorites': return '즐겨찾기_폴더';
      case 'logs': return 'notepad_logs.txt';
    }
  };

  const getSidebarItemLabel = (f: ExplorerFolder) => {
    if (lang === 'en') {
      switch (f) {
        case 'timer': return 'Time Controller.exe';
        case 'scheduler': return 'Task Scheduler.msc';
        case 'packager': return 'EXE Portable Builder';
        case 'command': return 'Terminal CLI Console';
        case 'favorites': return 'Favorites Vault';
        case 'logs': return 'notepad_logs.txt';
      }
    } else {
      switch (f) {
        case 'timer': return '시간 제어기.exe';
        case 'scheduler': return '작업 스케줄러.msc';
        case 'packager': return 'EXE 단일 파일 빌더';
        case 'command': return '터미널 CLI 명령창';
        case 'favorites': return '즐겨찾기 보관함';
        case 'logs': return 'notepad_logs.txt';
      }
    }
  };

  // Sidebar tree folder lists
  const sidebarItems: { id: ExplorerFolder; label: string; icon: any; isLink?: boolean }[] = [
    { id: 'timer', label: '시간 제어기.exe', icon: Cpu },
    { id: 'scheduler', label: '작업 스케줄러.msc', icon: Clock },
    { id: 'packager', label: 'EXE 단일 파일 빌더', icon: Monitor },
    { id: 'command', label: '터미널 CLI 명령창', icon: Terminal },
    { id: 'favorites', label: '즐겨찾기 보관함', icon: Star },
    { id: 'logs', label: 'notepad_logs.txt', icon: FileText }
  ];

  // Helper filter for file search
  const filteredSidebarItems = sidebarItems.filter(item => 
    item.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // "타이머 동작 시 1분 남았을때 상단고정옵션이 체크되어 있으면 상단창 배경색을 변동시켜 사용자에게 주의를 줍니다."
  const isWarningActive = alwaysOnTop && timerState === 'running' && secondsRemaining <= 60 && secondsRemaining > 0;

  // Option A: Windows Desktop Native App View (PowerController.exe / Tkinter Mirroring Mode)
  if (viewMode === 'desktop') {
    return (
      <div className={selectedFont}>
        <DesktopAppView
          onSwitchToWeb={() => setViewMode('web')}
          onOpenLicense={() => setIsLicenseOpen(true)}
          isWebAvailable={true}
        />

        {/* License Modal Portal */}
        <AnimatePresence>
          {isLicenseOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="w-full max-w-[540px] rounded-lg border border-gray-700 bg-gray-900 shadow-2xl p-5 flex flex-col max-h-[90vh] text-slate-100"
              >
                <div className="flex items-center justify-between pb-3 border-b border-gray-800">
                  <span className="text-sm font-bold flex items-center gap-1.5 text-white">
                    📄 {licenseModalLang === 'en' ? 'License & Terms Agreement Notice' : '사용권 계약 및 오픈소스 라이선스 약관 고지'}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center bg-gray-800 rounded p-0.5 border border-gray-700 text-xs">
                      <button
                        onClick={() => setLicenseModalLang('ko')}
                        className={`px-2 py-0.5 rounded cursor-pointer ${licenseModalLang === 'ko' ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
                      >
                        🇰🇷 한국어
                      </button>
                      <button
                        onClick={() => setLicenseModalLang('en')}
                        className={`px-2 py-0.5 rounded cursor-pointer ${licenseModalLang === 'en' ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
                      >
                        🇺🇸 English
                      </button>
                    </div>
                    <button
                      onClick={() => setIsLicenseOpen(false)}
                      className="p-1 rounded hover:bg-white/10 text-gray-400 hover:text-white"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto my-4 p-3 rounded font-mono text-[12.5px] select-text leading-relaxed whitespace-pre-wrap bg-gray-950 text-gray-300 border border-gray-800 max-h-[60vh]">
                  {licenseModalLang === 'en' ? (
                    `[End User License Agreement & Open Source Notice]

Before installing and using this software (PowerController), please review and agree to the license terms and open-source software component disclosures below.

--------------------------------------------------
1. Software Standard License (MIT License)
--------------------------------------------------
Copyright (c) 2026 AhBiYout

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

--------------------------------------------------
2. Open Source Libraries & Copyright Disclosures
--------------------------------------------------
PowerController incorporates standard native modules and libraries:
■ PowerCoreNative.dll (Waitable wakeup timer, Sleep state lock, Process killer)
■ NetBeaconEngine.dll (Winsock2 UDP ringbuffer beacon engine)
■ FirewallNative.dll (Windows Firewall COM direct registration)
■ SysPowerHook.dll (Session lock hook, Battery & UPS monitor)
■ ScheduleCrypto.dll (C99 SHA-256, HMAC-SHA256 digital signature, Encrypted envelope)
■ pystray, Pillow, PyInstaller, Tkinter`
                  ) : (
                    `[사용권 계약 및 오픈소스 라이선스 약관 고지]

본 프로그램(PowerController)을 설치하여 사용하기 전, 아래의 사용권 및 사용된 오픈소스 소프트웨어 구성 정보를 확인하고 동의해주시기 바랍니다.

--------------------------------------------------
1. 프로그램 표준 라이선스 (MIT License)
--------------------------------------------------
Copyright (c) 2026 AhBiYout

이 소프트웨어의 복제본과 관련된 문서 파일(이하 "소프트웨어")을 획득하는 모든 사람에게 소프트웨어를 제한 없이 사용할 수 있는 권한을 부여합니다. 여기에는 소프트웨어의 사본을 사용, 복제, 수정, 병합, 게시, 배포, 서브라이선스 부여 및/또는 판매할 수 있는 권한이 포함되며, 이를 위해 다음 조건을 충족해야 합니다:

상기 저작권 고시와 본 허용 고시가 소프트웨어의 모든 복제본 또는 상당 부분에 포함되어야 합니다.

소프트웨어는 "있는 그대로" 제공되며, 상품성, 특정 목적에의 적합성 및 비침해에 대한 보증을 포함하되 이에 국한되지 않고 명시적이거나 묵시적인 어떠한 보증도 제공하지 않습니다.

--------------------------------------------------
2. 사용된 네이티브 엔진 및 오픈소스 라이브러리
--------------------------------------------------
■ 5대 순수 창작 저수준 C/C++ DLL 엔진:
  - PowerCoreNative.dll: 초정밀 하드웨어 웨이크업 타이머 및 무음 프로세스 트리 종료
  - NetBeaconEngine.dll: Winsock2 논블로킹 UDP 비콘 및 512 슬롯 링버퍼
  - FirewallNative.dll: Windows Defender 방화벽 COM 직결 0.05초 일괄 트랜잭션
  - SysPowerHook.dll: Windows 세션 알림 감지 및 하드웨어 배터리 위험 수위 보호
  - ScheduleCrypto.dll: HMAC-SHA256 디지털 서명 및 암호화 봉투 무결성 검증
■ pystray, Pillow (PIL), PyInstaller, Tkinter 표준 GUI`
                  )}
                </div>
                <div className="pt-3 border-t border-gray-800 flex justify-end">
                  <button
                    onClick={() => setIsLicenseOpen(false)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer"
                  >
                    {licenseModalLang === 'ko' ? '확인 (닫기)' : 'Close'}
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div id="explorer-main-container" className={`min-h-screen p-3 md:p-6 flex flex-col items-center justify-center gap-5 transition-colors duration-300 ${currentThemeConfig.bg} ${selectedFont}`}>
      
      {/* Top Banner to switch to Desktop Native View */}
      <div className="w-full max-w-4xl bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 flex items-center justify-between shadow-lg text-xs">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 font-bold rounded">웹 대시보드 뷰</span>
          <span className="text-slate-400 hidden sm:inline">실제 Windows 데스크톱 앱(Tkinter GUI) 화면으로 전환할 수 있습니다.</span>
        </div>
        <button
          onClick={() => setViewMode('desktop')}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg shadow transition-colors flex items-center gap-1.5 cursor-pointer"
        >
          <Monitor className="w-3.5 h-3.5" />
          <span>🖥️ 데스크톱 앱 화면으로 전환</span>
        </button>
      </div>

      {/* Simulation Engine Overlay Portal */}
      {showSimulator && (
        <PowerSimulator
          mode={powerMode}
          lang={lang}
          forceClose={forceCloseEnabled}
          onClose={() => {
            setShowSimulator(false);
            setTimerState('idle');
            setSecondsRemaining(totalSeconds);
            addLog(lang === 'en' ? 'Simulator safely aborted and restored to the main queue.' : '시뮬레이터를 안전하게 중단하고 메인 대기열로 복구했습니다.');
          }}
          onRestartSimulation={() => {
            setShowSimulator(false);
            setTimerState('idle');
            addLog(lang === 'en' ? 'System power control reset. Configure a new action.' : '시스템 전원 제어를 리셋했습니다. 새 작동을 구성하세요.');
          }}
        />
      )}

      {/* Dynamic Display Layout: Always on top (Compact widget style) vs Full View */}
      {alwaysOnTop ? (
        <CompactWidget
          lang={lang}
          widgetDesign={widgetDesign}
          setWidgetDesign={setWidgetDesign}
          widgetWidth={widgetWidth}
          setWidgetWidth={setWidgetWidth}
          clockFontSize={clockFontSize}
          setClockFontSize={setClockFontSize}
          timerFontSize={timerFontSize}
          setTimerFontSize={setTimerFontSize}
          widgetOpacity={widgetOpacity}
          handleWidgetOpacityChange={handleWidgetOpacityChange}
          showCurrentTimeCompact={showCurrentTimeCompact}
          handleShowCurrentTimeCompactChange={handleShowCurrentTimeCompactChange}
          selectedFont={selectedFont}
          handleFontChange={handleFontChange}
          powerMode={powerMode}
          handleModeChange={handleModeChange}
          timerState={timerState}
          secondsRemaining={secondsRemaining}
          totalSeconds={totalSeconds}
          inputH={inputH}
          inputM={inputM}
          inputS={inputS}
          setInputH={setInputH}
          setInputM={setInputM}
          setInputS={setInputS}
          handleStartTimer={handleStartTimer}
          handlePauseTimer={handlePauseTimer}
          handleResumeTimer={handleResumeTimer}
          handleResetTimer={handleResetTimer}
          handleTimerComplete={handleTimerComplete}
          handleQuickPreset={handleQuickPreset}
          toggleAlwaysOnTop={toggleAlwaysOnTop}
          isWarningActive={isWarningActive}
          currentThemeConfig={currentThemeConfig}
          formatTimeStr={formatTimeStr}
          getPowerModeKorean={getPowerModeKorean}
        />
      ) : (
        /* ==================== TKINTER-STYLE DESKTOP APP LAYOUT ==================== */
        <div
          id="explorer-app-window"
          className={`w-full max-w-[485px] rounded-xl overflow-hidden shadow-2xl flex flex-col border transition-all duration-300 ${currentThemeConfig.windowBg}`}
          style={{ minHeight: '740px', opacity: mainOpacity / 100 }}
        >
          {/* GitHub Releases Real-time Live Update Notification */}
          <GitHubUpdateBanner lang={lang} />

          {/* 1. App Window Title Bar */}
          <div className={`p-2.5 px-4 flex items-center justify-between border-b select-none ${currentThemeConfig.titleBar}`}>
            <div className="flex items-center gap-2.5">
              <div className="relative w-6 h-6 rounded-lg overflow-hidden ring-1 ring-cyan-400/40 shadow-sm shadow-cyan-500/20 flex-shrink-0 bg-slate-950">
                <img
                  src="/PowerController.png"
                  alt="App Icon"
                  className="w-full h-full object-cover scale-105"
                />
              </div>
              <span className="text-[13.5px] font-bold tracking-tight">
                {lang === 'en' ? 'Power Control Center' : '전원 종료/재시작 타이머'}
              </span>
              <span className="text-[12px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono font-semibold border border-blue-500/30">
                v{APP_VERSION}
              </span>
            </div>
            {/* Windows System Control Buttons */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => toggleAlwaysOnTop()}
                className="p-1 px-1.5 rounded hover:bg-blue-500 hover:text-white transition-colors text-gray-400"
                title={lang === 'en' ? 'Switch to compact mini widget' : '컴팩트 미니 알람 위젯으로 전환'}
              >
                <Minimize2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => addLog(lang === 'en' ? 'Window maximize simulated.' : '창 최대화가 가상 가동되었습니다.')}
                className="p-1 px-1.5 rounded hover:bg-gray-700 transition-colors text-gray-400"
                title={lang === 'en' ? 'Maximize' : '최대화'}
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => {
                  const c = confirm(lang === 'en' ? 'Ignore virtual program instance?' : '프로그램 가상 인스턴스를 무시하시겠습니까?');
                  if (c) addLog(lang === 'en' ? 'Shutdown event received.' : '종료 이벤트 수신 완료.');
                }}
                className="p-1 px-1.5 rounded hover:bg-rose-600 hover:text-white transition-colors text-gray-400"
                title={lang === 'en' ? 'Close' : '닫기'}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* 2. Classic File Menu Bar (MenuBar) */}
          <div className={`flex items-center px-4 py-1 text-[13.5px] border-b border-gray-500/10 bg-black/10 dark:bg-white/5 gap-3 select-none ${theme === 'beige' ? 'text-[#2c2217] font-semibold' : 'text-gray-200'}`}>
            <button onClick={() => {
              addLog(lang === 'en' ? 'Menu [File] triggered.' : '메뉴 [파일] 실행.');
              triggerNotification(lang === 'en' ? 'File Menu Options: Settings are auto-saved.' : '파일 메뉴 옵션: 설정이 자동으로 저장됩니다.', 'success');
            }} className={`${theme === 'beige' ? 'hover:bg-black/10' : 'hover:text-white'} cursor-pointer px-1 py-0.5 rounded`}>{lang === 'en' ? 'File(F)' : '파일(F)'}</button>
            <button onClick={() => {
              addLog(lang === 'en' ? 'Menu [Edit] triggered.' : '메뉴 [편집] 실행.');
              triggerNotification(lang === 'en' ? 'Edit Menu: You can click favorites presets below to instantly select them.' : '편집 메뉴: 하단 즐겨찾기 보관함을 통해 빠르고 정확한 지연 타이머를 설정할 수 있습니다.', 'info');
            }} className={`${theme === 'beige' ? 'hover:bg-black/10' : 'hover:text-white'} cursor-pointer px-1 py-0.5 rounded`}>{lang === 'en' ? 'Edit(E)' : '편집(E)'}</button>
            <button onClick={() => {
              addLog(lang === 'en' ? 'Menu [View] triggered.' : '메뉴 [보기] 실행.');
              cycleTheme();
            }} className={`${theme === 'beige' ? 'hover:bg-black/10' : 'hover:text-white'} cursor-pointer px-1 py-0.5 rounded`}>{lang === 'en' ? 'View(V)' : '보기(V)'}</button>
            
            <button onClick={() => {
              handleLangChange(lang === 'ko' ? 'en' : 'ko');
            }} className={`${theme === 'beige' ? 'hover:bg-black/10' : 'hover:text-white'} cursor-pointer px-1 py-0.5 rounded`}>{lang === 'en' ? 'Language(L)' : '한/영(L)'}</button>
            
            <button onClick={() => triggerNotification(lang === 'en' ? `Power Auto Shutdown Controller v${APP_VERSION}\nAuthor: AhBiYout\nCompany: cisnet.co.kr\nGoogle Blog: https://ahbiyoutvibe.blogspot.com/` : `전원 자동 오프 제어기 v${APP_VERSION}\n제작자: AhBiYout\n회사: cisnet.co.kr\n구글 블로그: https://ahbiyoutvibe.blogspot.com/`, 'info')} className={`${theme === 'beige' ? 'hover:bg-black/10' : 'hover:text-white'} cursor-pointer px-1 py-0.5 rounded`}>{lang === 'en' ? 'Help(H)' : '도움말(H)'}</button>
          </div>

          {/* 3. Tab Navigation Header Bar */}
          <div className="grid grid-cols-3 gap-1 p-2 bg-black/10 border-b border-gray-500/10">
            <button
              onClick={() => setActiveFolder('timer')}
              className={`py-1.5 rounded text-[13.5px] font-bold transition-all cursor-pointer ${
                activeFolder === 'timer' || activeFolder === 'favorites' || activeFolder === 'packager' || activeFolder === 'command'
                  ? 'bg-[#3b82f6] text-white shadow font-extrabold'
                  : theme === 'beige' ? 'bg-[#ebe2d4] hover:bg-[#ded1c0] text-[#3d3222]' : 'bg-black/20 hover:bg-white/5 text-gray-200'
              }`}
            >
              ⏱ {lang === 'en' ? 'Control' : '간편 제어'}
            </button>
            <button
              onClick={() => setActiveFolder('scheduler')}
              className={`py-1.5 rounded text-[13.5px] font-bold transition-all cursor-pointer ${
                activeFolder === 'scheduler'
                  ? 'bg-[#3b82f6] text-white shadow font-extrabold'
                  : theme === 'beige' ? 'bg-[#ebe2d4] hover:bg-[#ded1c0] text-[#3d3222]' : 'bg-black/20 hover:bg-white/5 text-gray-200'
              }`}
            >
              📅 {lang === 'en' ? 'Scheduler' : '스케줄러'}
            </button>
            <button
              onClick={() => setActiveFolder('logs')}
              className={`py-1.5 rounded text-[13.5px] font-bold transition-all cursor-pointer ${
                activeFolder === 'logs'
                  ? 'bg-[#3b82f6] text-white shadow font-extrabold'
                  : theme === 'beige' ? 'bg-[#ebe2d4] hover:bg-[#ded1c0] text-[#3d3222]' : 'bg-black/20 hover:bg-white/5 text-gray-200'
              }`}
            >
              📋 {lang === 'en' ? 'Logs' : '동작 기록'}
            </button>
          </div>

          {/* 4. Main Body Content View Area */}
          <div className={`flex-1 p-4 overflow-y-auto [scrollbar-width:thin] flex flex-col no-scrollbar transition-colors duration-300 ${currentThemeConfig.mainAreaBg} ${currentThemeConfig.text}`}>
            {(activeFolder === 'timer' || activeFolder === 'favorites' || activeFolder === 'packager' || activeFolder === 'command') && (
              <div className="space-y-4 flex flex-col flex-1">
                {/* Mode Grid Row */}
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 select-none">
                  {[
                    {
                      id: 'shutdown',
                      label: lang === 'en' ? 'Shutdown' : '시스템종료',
                      shortLabel: lang === 'en' ? 'Shut' : '종료',
                      icon: Power,
                      activeBg: 'bg-gradient-to-b from-rose-500 to-rose-700 text-white shadow-lg shadow-rose-900/40 ring-1 ring-rose-400/50',
                      iconColor: 'text-rose-400 group-hover:text-rose-300',
                    },
                    {
                      id: 'restart',
                      label: lang === 'en' ? 'Restart' : '다시시작',
                      shortLabel: lang === 'en' ? 'Re' : '재시작',
                      icon: RotateCw,
                      activeBg: 'bg-gradient-to-b from-blue-500 to-blue-700 text-white shadow-lg shadow-blue-900/40 ring-1 ring-blue-400/50',
                      iconColor: 'text-blue-400 group-hover:text-blue-300',
                    },
                    {
                      id: 'sleep',
                      label: lang === 'en' ? 'Sleep' : '절전모드',
                      shortLabel: lang === 'en' ? 'Sleep' : '절전',
                      icon: Moon,
                      activeBg: 'bg-gradient-to-b from-indigo-500 to-indigo-700 text-white shadow-lg shadow-indigo-900/40 ring-1 ring-indigo-400/50',
                      iconColor: 'text-indigo-400 group-hover:text-indigo-300',
                    },
                    {
                      id: 'screenoff',
                      label: lang === 'en' ? 'Screen Off' : '화면끄기',
                      shortLabel: lang === 'en' ? 'Scr' : '화면끔',
                      icon: Monitor,
                      activeBg: 'bg-gradient-to-b from-amber-500 to-amber-700 text-white shadow-lg shadow-amber-900/40 ring-1 ring-amber-400/50',
                      iconColor: 'text-amber-400 group-hover:text-amber-300',
                    },
                    {
                      id: 'logout',
                      label: lang === 'en' ? 'Sign Out' : '로그아웃',
                      shortLabel: lang === 'en' ? 'Log' : '로그아웃',
                      icon: LogOut,
                      activeBg: 'bg-gradient-to-b from-emerald-500 to-emerald-700 text-white shadow-lg shadow-emerald-900/40 ring-1 ring-emerald-400/50',
                      iconColor: 'text-emerald-400 group-hover:text-emerald-300',
                    },
                    {
                      id: 'alarm',
                      label: lang === 'en' ? 'Alarm Only' : '알람알림',
                      shortLabel: lang === 'en' ? 'Alarm' : '알람',
                      icon: Volume2,
                      activeBg: 'bg-gradient-to-b from-pink-500 to-pink-700 text-white shadow-lg shadow-pink-900/40 ring-1 ring-pink-400/50',
                      iconColor: 'text-pink-400 group-hover:text-pink-300',
                    },
                  ].map((modeItem) => {
                    const active = powerMode === modeItem.id;
                    const ModeIcon = modeItem.icon;
                    return (
                      <button
                        key={modeItem.id}
                        onClick={() => handleModeChange(modeItem.id as PowerMode)}
                        className={`group relative py-2.5 px-1 rounded-lg font-bold cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-1.5 ${
                          active
                            ? `${modeItem.activeBg} scale-[1.02]`
                            : `${currentThemeConfig.btnInactive} hover:scale-[1.02]`
                        }`}
                        title={getPowerModeKorean(modeItem.id as PowerMode)}
                      >
                        <div className={`p-1 rounded-md transition-colors ${active ? 'bg-white/20 text-white' : modeItem.iconColor}`}>
                          <ModeIcon className="w-5 h-5 stroke-[2.2]" />
                        </div>
                        <span className="text-[11.5px] tracking-tight font-medium">
                          {modeItem.shortLabel}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {/* Run Type Toggle */}
                <div className="grid grid-cols-2 gap-2 select-none">
                  <button
                    onClick={() => {
                      if (timerState !== 'idle') {
                        triggerNotification(lang === 'en' ? 'Cannot switch mode while a task is running. Please reset first.' : '예약이 이미 가동 중일 때는 변경할 수 없습니다. 리셋 후 변경하십시오.', 'error');
                        return;
                      }
                      setRunType('timer');
                    }}
                    className={`py-1.5 text-[13.5px] font-bold rounded cursor-pointer transition-all ${
                      runType === 'timer'
                        ? 'bg-[#3b82f6] text-white shadow font-bold'
                        : currentThemeConfig.btnInactive
                    }`}
                  >
                    ⏳ {lang === 'en' ? 'Timer (Delay)' : '시간 타이머 (후)'}
                  </button>
                  <button
                    onClick={() => {
                      if (timerState !== 'idle') {
                        triggerNotification(lang === 'en' ? 'Cannot switch mode while a task is running. Please reset first.' : '예약이 이미 가동 중일 때는 변경할 수 없습니다. 리셋 후 변경하십시오.', 'error');
                        return;
                      }
                      setRunType('schedule');
                      const now = new Date();
                      setInputH((now.getHours() + 1) % 24);
                      setInputM(0);
                      setInputS(0);
                    }}
                    className={`py-1.5 text-[13.5px] font-bold rounded cursor-pointer transition-all ${
                      runType === 'schedule'
                        ? 'bg-[#3b82f6] text-white shadow font-bold'
                        : currentThemeConfig.btnInactive
                    }`}
                  >
                    ⏰ {lang === 'en' ? 'Clock (Specific)' : '특정 시각 예약 (정시)'}
                  </button>
                </div>

                {/* Big Digital Clock Gauge Panel */}
                <div className={`border rounded py-4 text-center select-all shadow-inner transition-colors duration-300 ${currentThemeConfig.panelBg} ${currentThemeConfig.panelBorder}`}>
                  {timerState === 'idle' ? (
                    <span className="text-4xl font-mono font-bold tracking-wider text-[#3b82f6] block">
                      {runType === 'timer'
                        ? `${inputH.toString().padStart(2, '0')}:${inputM.toString().padStart(2, '0')}:${inputS.toString().padStart(2, '0')}`
                        : `${inputH.toString().padStart(2, '0')}:${inputM.toString().padStart(2, '0')}:00`
                      }
                    </span>
                  ) : (
                    <div className="space-y-0.5">
                      <span className="text-4xl font-mono font-bold tracking-wider text-[#3b82f6] block">
                        {formatTimeStr(secondsRemaining)}
                      </span>
                      <span className={`text-[13.5px] font-semibold uppercase tracking-widest font-mono ${currentThemeConfig.subtext}`}>
                        {t.timerStateStatus[timerState]} • {getPowerModeKorean(powerMode)}
                      </span>
                    </div>
                  )}
                </div>

                {/* Real-time System Telemetry Panel (Live resource data) */}
                <div className={`grid grid-cols-2 gap-2.5 p-2.5 rounded-xl border transition-all duration-300 ${currentThemeConfig.panelBg} ${currentThemeConfig.panelBorder}`}>
                  {/* CPU / MEMORY column */}
                  <div className="space-y-2">
                    {/* CPU telemetry */}
                    <div className="flex flex-col gap-0.5">
                      <div className="flex items-center justify-between text-[13.5px] font-bold">
                        <span className={`flex items-center gap-1 ${theme === 'beige' ? 'text-blue-700' : 'text-blue-400'}`}>
                          <Cpu className="w-3 h-3" />
                          CPU {lang === 'en' ? 'Usage' : '점유율'}
                        </span>
                        <span className={`font-mono text-[13.5px] font-bold ${theme === 'beige' ? 'text-[#2c2217]' : 'text-gray-200'}`}>
                          {systemStatus ? `${systemStatus.cpu}%` : '--%'}
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-black/20 dark:bg-black/50 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full transition-all duration-500" 
                          style={{ width: `${systemStatus ? systemStatus.cpu : 0}%` }}
                        />
                      </div>
                    </div>

                    {/* Memory telemetry */}
                    <div className="flex flex-col gap-0.5">
                      <div className="flex items-center justify-between text-[13.5px] font-bold">
                        <span className={`flex items-center gap-1 ${theme === 'beige' ? 'text-indigo-700' : 'text-indigo-400'}`}>
                          <HardDrive className="w-3 h-3" />
                          RAM {lang === 'en' ? 'Memory' : '메모리'}
                        </span>
                        <span className={`font-mono text-[13.5px] font-bold ${theme === 'beige' ? 'text-[#2c2217]' : 'text-gray-200'}`}>
                          {systemStatus ? `${systemStatus.memory.pct}%` : '--%'}
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-black/20 dark:bg-black/50 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-indigo-500 rounded-full transition-all duration-500" 
                          style={{ width: `${systemStatus ? systemStatus.memory.pct : 0}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* DISK / NETWORK column */}
                  <div className="space-y-2">
                    {/* Disk space telemetry */}
                    <div className="flex flex-col gap-0.5">
                      <div className="flex items-center justify-between text-[13.5px] font-bold">
                        <span className={`flex items-center gap-1 ${theme === 'beige' ? 'text-emerald-800' : 'text-emerald-400'}`}>
                          <HardDrive className="w-3 h-3" />
                          Disk C: {lang === 'en' ? 'Usage' : '디스크'}
                        </span>
                        <span className={`font-mono text-[13.5px] font-bold ${theme === 'beige' ? 'text-[#2c2217]' : 'text-gray-200'}`}>
                          {systemStatus ? `${systemStatus.disk.pct}%` : '--%'}
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-black/20 dark:bg-black/50 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-emerald-500 rounded-full transition-all duration-500" 
                          style={{ width: `${systemStatus ? systemStatus.disk.pct : 0}%` }}
                        />
                      </div>
                    </div>

                    {/* Network online latency */}
                    <div className="flex flex-col gap-0.5">
                      <div className="flex items-center justify-between text-[13.5px] font-bold">
                        <span className={`flex items-center gap-1 ${theme === 'beige' ? 'text-pink-800' : 'text-pink-400'}`}>
                          <Network className="w-3 h-3" />
                          {lang === 'en' ? 'Network' : '네트워크'}
                        </span>
                        <span className={`font-mono text-[13.5px] px-1 rounded font-bold ${
                          systemStatus?.network.online 
                            ? (theme === 'beige' ? 'bg-emerald-100 text-emerald-800' : 'bg-emerald-500/15 text-emerald-400')
                            : (theme === 'beige' ? 'bg-rose-100 text-rose-800' : 'bg-rose-500/15 text-rose-400')
                        }`}>
                          {systemStatus 
                            ? systemStatus.network.online 
                              ? `ONLINE (${systemStatus.network.latency}ms)` 
                              : 'OFFLINE'
                            : '...'
                          }
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-black/30 dark:bg-black/50 rounded-full overflow-hidden flex items-center">
                        <div 
                          className={`h-full rounded-full transition-all duration-500 ${systemStatus?.network.online ? 'bg-emerald-500 w-full' : 'bg-rose-500 w-1/4'}`} 
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Input Fields */}
                <div className={`p-2.5 rounded border transition-colors duration-300 ${currentThemeConfig.inputContainerBg}`}>
                  <label className={`block text-[10.5px] font-bold mb-2 leading-tight ${currentThemeConfig.subtext}`}>
                    {runType === 'timer'
                      ? (lang === 'en' ? '[Timer Mode] Specify delay in hours/minutes/seconds.' : '[경과 시간 입력] 몇 시간/분/초 후에 전원을 제어할지 지정하십시오.')
                      : (lang === 'en' ? '[Clock Mode] Specify target hour and minute (24h format).' : '[특정 예약 시각 지정] 오늘/내일 몇 시 몇 분에 실행할지 24시 형식으로 입력하십시오.')
                    }
                  </label>

                  {timerState === 'idle' ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="flex flex-col items-center">
                        <span className={`text-[13.5px] font-bold mb-1 ${theme === 'beige' ? 'text-[#3d3222]' : 'text-gray-300'}`}>{runType === 'timer' ? (lang === 'en' ? 'H' : '시') : (lang === 'en' ? 'Hour' : '실행 시')}</span>
                        <input
                          type="number"
                          min={0}
                          max={23}
                          value={inputH}
                          onChange={(e) => setInputH(Math.min(23, Math.max(0, parseInt(e.target.value) || 0)))}
                          className={`w-16 text-center py-1.5 text-sm font-bold rounded font-mono transition-colors duration-300 focus:outline-none ${currentThemeConfig.inputBox}`}
                        />
                      </div>
                      <span className={`font-bold mt-4 ${theme === 'beige' ? 'text-[#3d3222]' : 'text-gray-400'}`}>:</span>
                      <div className="flex flex-col items-center">
                        <span className={`text-[13.5px] font-bold mb-1 ${theme === 'beige' ? 'text-[#3d3222]' : 'text-gray-300'}`}>{runType === 'timer' ? (lang === 'en' ? 'M' : '분') : (lang === 'en' ? 'Minute' : '실행 분')}</span>
                        <input
                          type="number"
                          min={0}
                          max={59}
                          value={inputM}
                          onChange={(e) => setInputM(Math.min(59, Math.max(0, parseInt(e.target.value) || 0)))}
                          className={`w-16 text-center py-1.5 text-sm font-bold rounded font-mono transition-colors duration-300 focus:outline-none ${currentThemeConfig.inputBox}`}
                        />
                      </div>
                      {runType === 'timer' && (
                        <>
                          <span className={`font-bold mt-4 ${theme === 'beige' ? 'text-[#3d3222]' : 'text-gray-400'}`}>:</span>
                          <div className="flex flex-col items-center">
                            <span className={`text-[13.5px] font-bold mb-1 ${theme === 'beige' ? 'text-[#3d3222]' : 'text-gray-300'}`}>{lang === 'en' ? 'S' : '초'}</span>
                            <input
                              type="number"
                              min={0}
                              max={59}
                              value={inputS}
                              onChange={(e) => setInputS(Math.min(59, Math.max(0, parseInt(e.target.value) || 0)))}
                              className={`w-16 text-center py-1.5 text-sm font-bold rounded font-mono transition-colors duration-300 focus:outline-none ${currentThemeConfig.inputBox}`}
                            />
                          </div>
                        </>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-1.5 text-[13.5px] text-blue-500 dark:text-blue-400 font-bold bg-blue-500/10 rounded-lg border border-blue-500/20 select-none">
                      {t.scheduledTimePrefix} <span className="font-mono">{new Date(Date.now() + (secondsRemaining * 1000)).toLocaleTimeString(lang === 'en' ? 'en-US' : 'ko-KR')}</span>
                    </div>
                  )}
                </div>

                {/* Execution Controls buttons */}
                <div className="grid grid-cols-3 gap-2">
                  {timerState === 'idle' ? (
                    <button
                      onClick={handleStartTimer}
                      className="col-span-3 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold text-[13.5px] transition-all cursor-pointer flex items-center justify-center gap-2 shadow shadow-blue-600/30"
                    >
                      <Play className="w-3.5 h-3.5 fill-white" />
                      {runType === 'timer' ? (lang === 'en' ? '▶ Start Timer' : '▶ 타이머 시작') : (lang === 'en' ? '▶ Start Clock Timer' : '▶ 특정 시각 예약 가동')}
                    </button>
                  ) : (
                    <>
                      {timerState === 'running' ? (
                        <button
                          onClick={handlePauseTimer}
                          className="py-2.5 bg-amber-500 hover:bg-amber-400 text-white rounded font-bold text-[13.5px] transition-all cursor-pointer flex items-center justify-center gap-1.5"
                        >
                          <Pause className="w-3.5 h-3.5" />
                          {lang === 'en' ? '⏸ Pause' : '⏸ 일시정지'}
                        </button>
                      ) : (
                        <button
                          onClick={handleResumeTimer}
                          className="py-2.5 bg-green-600 hover:bg-green-500 text-white rounded font-bold text-[13.5px] transition-all cursor-pointer flex items-center justify-center gap-1.5"
                        >
                          <Play className="w-3.5 h-3.5 fill-white" />
                          {lang === 'en' ? '▶ Resume' : '▶ 다시 시작'}
                        </button>
                      )}
                      <button
                        onClick={handleResetTimer}
                        className="py-2.5 bg-gray-600 hover:bg-gray-500 text-white rounded font-bold text-[13.5px] transition-all cursor-pointer flex items-center justify-center gap-1.5"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        {lang === 'en' ? '🔄 Reset' : '🔄 리셋'}
                      </button>
                      <button
                        onClick={handleTimerComplete}
                        className="py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded font-bold text-[13.5px] transition-all cursor-pointer flex items-center justify-center gap-1.5 shadow shadow-rose-600/30"
                      >
                        <Power className="w-3.5 h-3.5" />
                        {lang === 'en' ? 'Trigger' : '즉시 격발'}
                      </button>
                    </>
                  )}
                </div>

                 {/* Sub Tools: Quick Slots & Favorites */}
                 <div className={`p-2.5 rounded border space-y-3 flex-1 flex flex-col min-h-[220px] transition-colors duration-300 ${currentThemeConfig.subPanelBg}`}>
                   {/* Sub Tool Tab Selector */}
                   <div className="flex border-b border-gray-500/10 pb-2 gap-1.5 select-none">
                     <button
                       onClick={() => setActiveFolder('timer')}
                       className={`px-2.5 py-1 text-[13.5px] font-bold rounded cursor-pointer transition-all ${
                         activeFolder === 'timer' || activeFolder === 'favorites'
                           ? theme === 'beige'
                             ? 'bg-[#8c785c]/15 border border-[#8c785c]/40 text-[#8c785c] font-extrabold'
                             : 'bg-blue-600/25 border border-blue-500/40 text-blue-400 font-extrabold'
                           : `${currentThemeConfig.btnInactive} text-[13.5px]`
                       }`}
                     >
                       ⚡ {lang === 'en' ? 'Quick Slots' : '단축 퀵 슬롯'}
                     </button>
                     <button
                       onClick={() => setActiveFolder('packager')}
                       className={`px-2.5 py-1 text-[13.5px] font-bold rounded cursor-pointer transition-all ${
                         activeFolder === 'packager'
                           ? theme === 'beige'
                             ? 'bg-[#8c785c]/15 border border-[#8c785c]/40 text-[#8c785c] font-extrabold'
                             : 'bg-blue-600/25 border border-blue-500/40 text-blue-400 font-extrabold'
                           : `${currentThemeConfig.btnInactive} text-[13.5px]`
                       }`}
                     >
                       📦 {lang === 'en' ? 'File Builder' : '단일 파일 빌더'}
                     </button>
                     <button
                       onClick={() => setActiveFolder('command')}
                       className={`px-2.5 py-1 text-[13.5px] font-bold rounded cursor-pointer transition-all ${
                         activeFolder === 'command'
                           ? theme === 'beige'
                             ? 'bg-[#8c785c]/15 border border-[#8c785c]/40 text-[#8c785c] font-extrabold'
                             : 'bg-blue-600/25 border border-blue-500/40 text-blue-400 font-extrabold'
                           : `${currentThemeConfig.btnInactive} text-[13.5px]`
                       }`}
                     >
                       💻 {lang === 'en' ? 'CLI Script' : 'CLI 명령창'}
                     </button>
                   </div>

                   {activeFolder === 'timer' && (
                     <>
                       {/* Force Close Apps Toggle (/f Parameter) */}
                       <div className="flex items-center justify-between px-2 py-1.5 bg-black/10 dark:bg-white/5 rounded border border-gray-500/15 text-[13.5px]">
                         <label className="flex items-center gap-1.5 cursor-pointer select-none">
                           <input
                             type="checkbox"
                             checked={forceCloseEnabled}
                             onChange={handleToggleForceClose}
                             className="rounded border-gray-500 text-rose-600 focus:ring-0 cursor-pointer"
                           />
                           <span className="font-bold text-rose-500 flex items-center gap-1">
                             ⚡ {lang === 'en' ? 'Force Close Running Apps (/f)' : '실행 중인 앱 강제 종료 (/f)'}
                           </span>
                         </label>
                         <span className="text-[13.5px] text-gray-400 font-medium">
                           {forceCloseEnabled ? (lang === 'en' ? 'Default: Enabled' : '기본: 활성화 상태') : (lang === 'en' ? 'Disabled' : '비활성화')}
                         </span>
                       </div>

                       <div className="space-y-1.5">
                         <span className={`block text-[13.5px] uppercase font-bold pl-0.5 ${currentThemeConfig.subtext}`}>
                           ⚡ {lang === 'en' ? 'Quick preset slots (One-click delay)' : '지연 설정 퀵 슬롯 (원클릭 즉시 가동)'}
                         </span>
                         <div className="grid grid-cols-6 gap-1">
                           {[
                             { label: lang === 'en' ? '3m' : '3분', m: 3 },
                             { label: lang === 'en' ? '10m' : '10분', m: 10 },
                             { label: lang === 'en' ? '15m' : '15분', m: 15 },
                             { label: lang === 'en' ? '30m' : '30분', m: 30 },
                             { label: lang === 'en' ? '1h' : '1시간', m: 60 },
                             { label: lang === 'en' ? '2h' : '2시간', m: 120 },
                           ].map((preset, idx) => (
                             <button
                               key={idx}
                               onClick={() => handleQuickPreset(preset.m)}
                               className={`py-1 rounded cursor-pointer text-[13.5px] font-semibold transition-all duration-300 ${currentThemeConfig.presetBtn}`}
                             >
                               {preset.label}
                             </button>
                           ))}
                         </div>
                       </div>

                       <div className="flex-1 flex flex-col min-h-[110px]">
                         <span className={`block text-[13.5px] uppercase font-bold pl-0.5 mb-1 flex items-center gap-1 ${currentThemeConfig.subtext}`}>
                           ⭐ <span>{lang === 'en' ? 'Click preset to load' : '클릭 시 즉시 단축 예약 로드'}</span>
                         </span>
                         <div className={`flex-1 rounded border p-1 overflow-hidden flex flex-col transition-colors duration-300 ${currentThemeConfig.favoritesBoxBg}`}>
                           <FavoritesManager onFavSelect={handleFavoriteSelect} lang={lang} theme={theme} />
                         </div>
                       </div>
                     </>
                   )}

                   {activeFolder === 'packager' && (
                     <PackagerGuide lang={lang} />
                   )}

                   {activeFolder === 'command' && (
                     <CommandCopier mode={powerMode} durationSeconds={secondsRemaining} lang={lang} theme={theme} />
                   )}
                 </div>

                {/* Author Info */}
                <div className={`text-center text-[13.5px] font-mono select-none ${theme === 'beige' ? 'text-[#3d3222]' : 'text-gray-300'}`}>
                  <div className="flex flex-col items-center gap-1 mt-1">
                    <div className="flex items-center justify-center gap-2 flex-wrap text-[13.5px]">
                      <span>{lang === 'en' ? 'Developer: AhBiYout' : '개발자: AhBiYout'}</span>
                      <span>|</span>
                      <span>
                        {lang === 'en' ? 'Organization: ' : '소 속: '}
                        <a
                          href="http://www.cisnet.co.kr/"
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`${theme === 'beige' ? 'text-blue-700 hover:underline font-bold' : 'text-blue-400 hover:underline'} cursor-pointer`}
                        >
                          http://www.cisnet.co.kr/
                        </a>
                      </span>
                      <span>|</span>
                      <span className={`${theme === 'beige' ? 'text-blue-800' : 'text-blue-400'} font-semibold`}>v{APP_VERSION}</span>
                    </div>
                    <div className="flex items-center justify-center gap-2 flex-wrap text-[13.5px]">
                      <a
                        href="https://ahbiyoutvibe.blogspot.com/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`${theme === 'beige' ? 'text-blue-700 hover:underline font-bold' : 'text-blue-400 hover:underline'} cursor-pointer`}
                      >
                        {lang === 'en' ? 'Google Blog: https://ahbiyoutvibe.blogspot.com/' : '구글블로그: https://ahbiyoutvibe.blogspot.com/'}
                      </a>
                    </div>
                    <button
                      onClick={() => {
                        handleResetTimer();
                        setLicenseModalLang(lang);
                        setIsLicenseOpen(true);
                      }}
                      className={`${theme === 'beige' ? 'text-[#5c4d38] hover:text-blue-700' : 'text-gray-300 hover:text-blue-400'} underline cursor-pointer font-semibold`}
                    >
                      {lang === 'en' ? '📄 View License & Terms Agreement Notice' : '📄 라이선스 및 약관 동의 고지서'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {activeFolder === 'scheduler' && (
              <div className="flex-1 flex flex-col min-h-[500px]">
                <AdvancedScheduler
                  onTriggerRule={handleTriggerRule}
                  addLog={addLog}
                  soundEnabled={soundEnabled}
                  playWarningTick={playWarningTick}
                  lang={lang}
                  theme={theme}
                />
              </div>
            )}

            {activeFolder === 'logs' && (
              <div className="flex-1 flex flex-col min-h-[480px]">
                <div className={`text-[13.5px] font-bold mb-2 pl-1 select-none ${currentThemeConfig.subtext}`}>
                  📋 {lang === 'en' ? 'Power Control & Timer Logs' : '시스템 전원 제어 및 타이머 동작 기록'}
                </div>
                {/* Notepad Container */}
                <div className={`rounded border p-1 font-mono text-[13.5px] flex-1 flex flex-col mb-3 transition-colors duration-300 ${currentThemeConfig.logsPanelBg} ${currentThemeConfig.text}`}>
                  <div className={`flex items-center gap-2 border-b pb-1 px-1 mb-1 text-[13.5px] select-none ${currentThemeConfig.panelBorder} ${currentThemeConfig.subtext}`}>
                    <span>{t.logsTabTitleFile}</span>
                    <span>{t.logsTabTitleEdit}</span>
                    <span>{t.logsTabTitleFormat}</span>
                    <div className="ml-auto flex items-center gap-2">
                      <button
                        onClick={handleDownloadLogs}
                        className="px-2 py-0.5 text-blue-500 dark:text-blue-400 font-semibold border border-blue-500/30 rounded hover:bg-blue-500/15 cursor-pointer text-[13.5px]"
                      >
                        <span>{t.logsTabTitleDownloadBtn}</span>
                      </button>
                    </div>
                  </div>
                  <div className={`flex-1 p-2 overflow-y-auto max-h-[380px] no-scrollbar flex flex-col space-y-1 transition-colors duration-300 ${currentThemeConfig.logsInnerBg}`}>
                    {logs.length === 0 ? (
                      <div className="text-gray-500 italic text-center py-10">--- {t.logsEmpty} ---</div>
                    ) : (
                      logs.map((log, idx) => (
                        <div key={idx} className={`flex gap-1.5 rounded px-1 py-0.5 transition-colors duration-200 ${currentThemeConfig.logsLineHover}`}>
                          <span className="text-blue-500 font-bold">&gt;</span>
                          <span className={`break-all font-mono text-[10.5px] ${currentThemeConfig.text}`}>{log}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
                <button
                  onClick={handleCleanLogs}
                  className="w-full py-2 bg-rose-600 hover:bg-rose-500 text-white rounded font-bold text-[13.5px] cursor-pointer transition-colors"
                >
                  🗑️ {lang === 'en' ? 'Clear Logs' : '로그 기록 초기화'}
                </button>
              </div>
            )}
          </div>

          {/* 5. Window & Widget Display Settings (Settings Dialog Button) */}
          <div className="border-t border-gray-500/10 bg-black/10 dark:bg-white/5 select-none text-[13.5px]">
            {/* Settings trigger button */}
            <button
              onClick={handleOpenSettings}
              className={`w-full px-4 py-3 flex items-center justify-between hover:bg-black/10 text-[13.5px] font-bold transition-colors cursor-pointer ${theme === 'beige' ? 'text-[#2c2217]' : 'text-gray-200'}`}
            >
              <span className={`flex items-center gap-1.5 ${theme === 'beige' ? 'text-blue-700' : 'text-blue-400'}`}>
                <Palette className="w-4 h-4" />
                {lang === 'en' ? 'Settings ...' : '설정 ...'}
              </span>
              <ChevronRight className={`w-4 h-4 ${theme === 'beige' ? 'text-[#5c4d38]' : 'text-gray-400'}`} />
            </button>
          </div>

          {/* 6. Explorer Footer Status Bar */}
          <div className={`p-1.5 px-4 text-[13.5px] flex justify-between items-center font-medium ${currentThemeConfig.statusBarBg}`}>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1 pr-2">
                <span>{lang === 'en' ? `${sidebarItems.length} items ready` : `${sidebarItems.length}개 항목 대기`}</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <span className="border-r border-gray-500/20 pr-4">{lang === 'en' ? 'Selected Power: ' : '선택한 전원: '}<strong className={theme === 'beige' ? 'text-blue-800 font-extrabold' : 'text-blue-400 font-bold'}>{getPowerModeKorean(powerMode)}</strong></span>
              <span className="border-r border-gray-500/20 pr-4 hidden md:inline">{lang === 'en' ? 'Status: ' : '상태: '}<strong>{timerState === 'running' ? (lang === 'en' ? 'Monitoring' : '감시 작동 중') : (lang === 'en' ? 'Idle' : '대기')}</strong></span>
              <span className="hidden lg:inline pr-2">{currentTimeText}</span>
            </div>
          </div>

        </div>
      )}

      {/* Startup Today Tasks Modal */}
      <StartupTodayTasksModal
        isOpen={todayTasksModalOpen}
        tasks={todayTasks}
        lang={lang}
        onClose={() => setTodayTasksModalOpen(false)}
        onNavigateToScheduler={() => {
          setActiveFolder('scheduler');
          setTodayTasksModalOpen(false);
        }}
      />

      {/* Gorgeous Floating Toast Notification */}
      <AnimatePresence>
        {notification && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className={`fixed bottom-6 right-6 z-[9999] max-w-sm w-full backdrop-blur border rounded-xl p-4 shadow-2xl flex items-start gap-3 transition-colors duration-300 ${currentThemeConfig.windowBg} ${currentThemeConfig.text}`}
          >
            <div className={`p-1.5 rounded-lg ${
              notification.type === 'success' ? 'bg-emerald-500/20 text-emerald-400' :
              notification.type === 'error' ? 'bg-rose-500/20 text-rose-400' :
              'bg-blue-500/20 text-blue-400'
            }`}>
              {notification.type === 'success' && <Play className="w-5 h-5 fill-emerald-400/20" />}
              {notification.type === 'error' && <ShieldAlert className="w-5 h-5" />}
              {notification.type === 'info' && <Info className="w-5 h-5" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-[13.5px] font-semibold whitespace-pre-line leading-relaxed ${currentThemeConfig.text}`}>
                {notification.message}
              </p>
            </div>
            <button
              onClick={() => setNotification(null)}
              className={`transition-colors cursor-pointer ${currentThemeConfig.subtext} hover:opacity-85`}
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* License and Terms Modal */}
      <AnimatePresence>
        {isLicenseOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className={`w-full max-w-[506px] rounded-lg border shadow-2xl p-5 flex flex-col max-h-[90vh] transition-colors duration-300 ${currentThemeConfig.cardBg} ${currentThemeConfig.border}`}
            >
              <div className="flex items-center justify-between pb-3 border-b border-gray-500/10">
                <span className={`text-sm font-bold flex items-center gap-1.5 ${currentThemeConfig.text}`}>
                  📄 {licenseModalLang === 'en' ? 'License & Terms Agreement Notice' : '사용권 계약 및 오픈소스 라이선스 약관 고지'}
                </span>
                <div className="flex items-center gap-2">
                  <div className="flex items-center bg-gray-800/80 rounded p-0.5 border border-gray-700/50 text-xs">
                    <button
                      onClick={() => setLicenseModalLang('ko')}
                      className={`px-2 py-0.5 rounded cursor-pointer transition-colors ${licenseModalLang === 'ko' ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-gray-200'}`}
                    >
                      🇰🇷 한국어
                    </button>
                    <button
                      onClick={() => setLicenseModalLang('en')}
                      className={`px-2 py-0.5 rounded cursor-pointer transition-colors ${licenseModalLang === 'en' ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-gray-200'}`}
                    >
                      🇺🇸 English
                    </button>
                  </div>
                  <button
                    onClick={() => setIsLicenseOpen(false)}
                    className="p-1 rounded-full hover:bg-white/10 text-gray-400 hover:text-white cursor-pointer"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className={`flex-1 overflow-y-auto my-4 p-3 rounded font-mono text-[13.5px] select-text leading-relaxed whitespace-pre-wrap ${currentThemeConfig.logsInnerBg} ${currentThemeConfig.text}`}>
                {licenseModalLang === 'en' ? (
                  `[End User License Agreement & Open Source Notice]

Before installing and using this software (PowerController), please review and agree to the license terms and open-source software component disclosures below.

--------------------------------------------------
1. Software Standard License (MIT License)
--------------------------------------------------
Copyright (c) 2026 AhBiYout

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

--------------------------------------------------
2. Open Source Libraries & Copyright Disclosures
--------------------------------------------------
PowerController incorporates the following standard libraries and components to ensure reliable real-time and remote system power management:

■ pystray (v0.19.5+)
  - License: LGPL v3 / BSD Dual License
  - Purpose: System tray background residency monitoring and quick contextual tray menu operations
  - Feature: Low-power persistent event daemon

■ Pillow (PIL - Python Imaging Library v10.0+)
  - License: HPND License (Historical Permission Notice and Disclaimer)
  - Purpose: Dynamic multi-resolution power icon (64x64) rendering and mask compositing
  - Feature: Lossless performance-optimized drawing engine

■ PyInstaller (v6.0+)
  - License: GPL v2 with Bootloader Exception
  - Purpose: Standalone binary compilation and deployment wrapper packaging
  - Feature: Lightweight native binary execution runtime

■ Tkinter (Python Standard GUI Library)
  - License: Python Software Foundation (PSF) License
  - Purpose: Dark-mode desktop graphical user interface and schedule configuration controls
  - Feature: Lightweight and responsive OS-native GUI components

By proceeding with the installation, you acknowledge and agree to the license agreement and third-party notices above.`
                ) : (
                  `[사용권 계약 및 오픈소스 라이선스 약관 고지]

본 프로그램(PowerController)을 설치하여 사용하기 전, 아래의 사용권 및 사용된 오픈소스 소프트웨어 구성 정보를 확인하고 동의해주시기 바랍니다.

--------------------------------------------------
1. 프로그램 표준 라이선스 (MIT License)
--------------------------------------------------
Copyright (c) 2026 AhBiYout

이 소프트웨어의 복제본과 관련된 문서 파일(이하 "소프트웨어")을 획득하는 모든 사람에게 소프트웨어를 제한 없이 사용할 수 있는 권한을 부여합니다. 여기에는 소프트웨어의 사본을 사용, 복제, 수정, 병합, 게시, 배포, 서브라이선스 부여 및/또는 판매할 수 있는 권한이 포함되며, 이를 위해 다음 조건을 충족해야 합니다:

상기 저작권 고시와 본 허용 고시가 소프트웨어의 모든 복제본 또는 상당 부분에 포함되어야 합니다.

소프트웨어는 "있는 그대로" 제공되며, 상품성, 특정 목적에의 적합성 및 비침해에 대한 보증을 포함하되 이에 국한되지 않고 명시적이거나 묵시적인 어떠한 보증도 제공하지 않습니다. 저작업자나 저작권자는 어떠한 상황에서도 소프트웨어 또는 소프트웨어의 사용과 관련하여 발생하는 계약, 불법행위 또는 기타 다른 행위로 인한 청구, 손해 또는 기타 책임에 대해 책임을 지지 않습니다.

--------------------------------------------------
2. 사용된 오픈소스 라이브러리 및 저작권 (Used Libraries)
--------------------------------------------------
본 소프트웨어는 최적의 원격 및 실시간 컴퓨터 전원 감시 및 관리를 달성하기 위해 아래와 같은 표준 검증된 라이브러리와 인스턴스를 사용하고 있습니다:

■ pystray (v0.19.5+)
  - 라이선스: LGPL v3 / BSD Dual License
  - 사용 목적: 윈도우 작업 표시줄 우측의 시스템 트레이 백그라운드 상주 감시 컨트롤 및 트레이 우클릭 퀵 메뉴 컨트롤러 구현
  - 특징: 저전력 상향 트리거 데몬

■ Pillow (PIL - Python Imaging Library v10.0+)
  - 라이선스: HPND License (Historically Broad License)
  - 사용 목적: 시스템 트레이 내에서 동적으로 세련된 전원 번개 로고(64x64) 아이콘을 도식하며 마스킹 렌더링을 지휘
  - 특징: 무손실 속도 최적화 컴파일러용 동적 드로우 엔진

■ PyInstaller (v6.0+)
  - 라이선스: GPL v2 with Bootloader Exception
  - 사용 목적: 독립 실행형 패키지(Single EXE) 및 설치 마법사 빌드 래퍼 패키징 컴파일러 기동
  - 특징: 경량 패키징 런타임 릴리즈 바이너리

■ Tkinter (Python Standard GUI library)
  - 라이선스: Python Software Foundation (PSF) License
  - 사용 목적: 직관적인 사용자 중심의 어크릴 다크 테마 데스크톱 윈도우 인터페이스 구축 및 스케줄링 가이드 레이아웃
  - 특징: 경량의 신속한 운영체제 네이티브 GUI 컴포넌트

설치를 계속 진행하시면, 상위 라이선스 계약서와 사용 라이브러리 고지사항에 동의하시는 것으로 간주됩니다.`
                )}
              </div>

              <div className="text-center text-[13.5px] text-rose-400 font-bold mb-3">
                ⚠️ {licenseModalLang === 'en' ? 'Active timer has been stopped due to license viewing.' : '고지서 열람으로 인해 가동 중이던 타이머가 즉시 정지되었습니다.'}
              </div>

              <button
                onClick={() => setIsLicenseOpen(false)}
                className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold text-[13.5px] cursor-pointer transition-colors"
              >
                {licenseModalLang === 'en' ? 'OK' : '확인'}
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Settings Modal Dialog (Buffered Changes with Cancel / Confirm) */}
      <AnimatePresence>
        {isSettingsOpen && draftSettings && (
          <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4 select-none">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleCancelSettings}
              className="fixed inset-0 bg-black/75 backdrop-blur-sm"
            />

            {/* Modal Body */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ type: "spring", duration: 0.3 }}
              className={`relative w-full max-w-[506px] rounded-2xl border border-gray-500/20 p-5 shadow-2xl flex flex-col gap-3.5 overflow-hidden z-10 ${currentThemeConfig.windowBg} ${currentThemeConfig.text}`}
            >
              {/* Header */}
              <div className="flex items-center justify-between border-b border-gray-500/10 pb-2.5">
                <div className="flex items-center gap-2">
                  <Palette className="w-4 h-4 text-blue-400" />
                  <span className="font-bold text-[13.5px]">{lang === 'en' ? 'Preferences & Customization' : '환경 설정 및 맞춤화'}</span>
                  <span className="text-[13.5px] px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-400 font-mono font-semibold border border-blue-500/30">
                    v{APP_VERSION}
                  </span>
                </div>
                <button
                  onClick={handleCancelSettings}
                  className="p-1 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-white cursor-pointer"
                  title={lang === 'en' ? 'Cancel & Close' : '취소 후 닫기'}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Body */}
              <div className="flex flex-col gap-3 max-h-[460px] overflow-y-auto pr-1">
                {/* 1. Theme Selection */}
                <div className="flex flex-col gap-2 p-3 bg-black/10 dark:bg-white/5 rounded-xl border border-gray-500/10">
                  <span className="text-[13.5px] font-bold text-blue-400 flex items-center gap-1">🎨 {lang === 'en' ? 'Theme' : '테마 선택'}</span>
                  <div className="grid grid-cols-3 gap-1.5 mt-0.5">
                    <button
                      onClick={() => setDraftSettings({ ...draftSettings, theme: 'dark' })}
                      className={`px-2 py-1.5 rounded text-[13.5px] font-bold cursor-pointer text-center transition-all ${draftSettings.theme === 'dark' ? 'bg-blue-600 text-white shadow font-extrabold' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'}`}
                    >
                      {lang === 'en' ? 'Fluent Dark' : '다크'}
                    </button>
                    <button
                      onClick={() => setDraftSettings({ ...draftSettings, theme: 'gray' })}
                      className={`px-2 py-1.5 rounded text-[13.5px] font-bold cursor-pointer text-center transition-all ${draftSettings.theme === 'gray' ? 'bg-blue-600 text-white shadow font-extrabold' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'}`}
                    >
                      {lang === 'en' ? 'Simple Gray' : '그레이'}
                    </button>
                    <button
                      onClick={() => setDraftSettings({ ...draftSettings, theme: 'beige' })}
                      className={`px-2 py-1.5 rounded text-[13.5px] font-bold cursor-pointer text-center transition-all ${draftSettings.theme === 'beige' ? 'bg-blue-600 text-white shadow font-extrabold' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'}`}
                    >
                      {lang === 'en' ? 'Cozy Beige' : '베이지'}
                    </button>
                  </div>
                </div>

                {/* 2. Sound & Hourly Chime */}
                <div className="flex flex-col gap-2 p-3 bg-black/10 dark:bg-white/5 rounded-xl border border-gray-500/10">
                  <span className="text-[13.5px] font-bold text-emerald-400 flex items-center gap-1">🎵 {lang === 'en' ? 'Sound & Alerts' : '사운드 및 알림'}</span>
                  <div className="grid grid-cols-3 gap-1.5">
                    <button
                      onClick={() => {
                        setDraftSettings({ ...draftSettings, soundTheme: 'classic' });
                        playTestSound('classic');
                      }}
                      className={`py-1.5 rounded text-[13.5px] font-bold cursor-pointer text-center transition-all ${draftSettings.soundTheme === 'classic' ? 'bg-blue-600 text-white font-extrabold shadow' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'}`}
                    >
                      {lang === 'en' ? 'Classic' : '클래식'}
                    </button>
                    <button
                      onClick={() => {
                        setDraftSettings({ ...draftSettings, soundTheme: 'scifi' });
                        playTestSound('scifi');
                      }}
                      className={`py-1.5 rounded text-[13.5px] font-bold cursor-pointer text-center transition-all ${draftSettings.soundTheme === 'scifi' ? 'bg-blue-600 text-white font-extrabold shadow' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'}`}
                    >
                      {lang === 'en' ? 'Sci-Fi' : 'SF 신스'}
                    </button>
                    <button
                      onClick={() => {
                        setDraftSettings({ ...draftSettings, soundTheme: 'cozy' });
                        playTestSound('cozy');
                      }}
                      className={`py-1.5 rounded text-[13.5px] font-bold cursor-pointer text-center transition-all ${draftSettings.soundTheme === 'cozy' ? 'bg-blue-600 text-white font-extrabold shadow' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'}`}
                    >
                      {lang === 'en' ? 'Cozy' : '아늑한'}
                    </button>
                  </div>

                  {/* Hourly Chime Toggle */}
                  <div className="flex items-center justify-between gap-4 pt-2 border-t border-gray-500/10 mt-1">
                    <span className="text-[9.5px] text-gray-300 flex items-center gap-1">
                      🔔 {lang === 'en' ? 'Hourly Chime Notification' : '매 정각 알림 기능 (시계 종소리)'}
                    </span>
                    <label className="flex items-center gap-1.5 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={draftSettings.hourlyChime}
                        onChange={(e) => setDraftSettings({ ...draftSettings, hourlyChime: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="relative w-7 h-4 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-600"></div>
                    </label>
                  </div>

                  {/* Startup Tasks Alert Toggle */}
                  <div className="flex items-center justify-between gap-4 pt-2 border-t border-gray-500/10">
                    <span className="text-[9.5px] text-gray-300 flex items-center gap-1">
                      📅 {lang === 'en' ? 'Tray Briefing for Today Tasks on Startup' : '컴퓨터 부팅/시작 시 오늘 예약 작업 트레이 브리핑'}
                    </span>
                    <label className="flex items-center gap-1.5 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={draftSettings.startupTasksAlert}
                        onChange={(e) => setDraftSettings({ ...draftSettings, startupTasksAlert: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="relative w-7 h-4 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>

                {/* 3. Compact Floating Widget Designs & Size Controls */}
                <div className="flex flex-col gap-2.5 p-3 bg-black/10 dark:bg-white/5 rounded-xl border border-gray-500/10">
                  <span className="text-[13.5px] font-bold text-indigo-400 flex items-center gap-1">📌 {lang === 'en' ? 'Compact Widget Style & Size' : '상단고정창 디자인 및 크기 조절'}</span>
                  
                  {/* Design Preset Selector */}
                  <div className="flex flex-col gap-1">
                    <span className="text-[13.5px] text-gray-400">{lang === 'en' ? 'Window Style' : '창 디자인 스타일'}</span>
                    <div className="grid grid-cols-3 gap-1">
                      {[
                        { id: 'standard', label: lang === 'en' ? 'Neon Ring' : '네온 링' },
                        { id: 'cyber', label: lang === 'en' ? 'Cyber HUD' : '사이버 HUD' },
                        { id: 'slim', label: lang === 'en' ? 'Slim Bar' : '슬림 바' },
                        { id: 'retro', label: lang === 'en' ? 'Retro LED' : '레트로 LED' },
                        { id: 'minimal', label: lang === 'en' ? 'Clean Card' : '클린 카드' }
                      ].map((des) => (
                        <button
                          key={des.id}
                          onClick={() => setDraftSettings({ ...draftSettings, widgetDesign: des.id as CompactWidgetDesign })}
                          className={`py-1 text-[9.5px] rounded font-semibold transition-all cursor-pointer ${
                            draftSettings.widgetDesign === des.id
                              ? 'bg-indigo-600 text-white shadow'
                              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                          }`}
                        >
                          {des.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Widget Width Slider */}
                  <div className="flex items-center justify-between gap-4 pt-1">
                    <span className="text-[13.5px] text-gray-400">{lang === 'en' ? 'Widget Width' : '상단창 너비'}</span>
                    <div className="flex items-center gap-1.5 flex-1 max-w-[140px]">
                      <input
                        type="range"
                        min={260}
                        max={460}
                        step={10}
                        value={draftSettings.widgetWidth}
                        onChange={(e) => setDraftSettings({ ...draftSettings, widgetWidth: parseInt(e.target.value) })}
                        className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                      />
                      <span className="font-mono text-indigo-400 font-bold text-[13.5px] shrink-0 w-9 text-right">{draftSettings.widgetWidth}px</span>
                    </div>
                  </div>

                  {/* Clock Font Size Slider */}
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-[13.5px] text-gray-400">{lang === 'en' ? 'Clock Font Size' : '시계 글자 크기'}</span>
                    <div className="flex items-center gap-1.5 flex-1 max-w-[140px]">
                      <input
                        type="range"
                        min={8}
                        max={28}
                        step={1}
                        value={draftSettings.clockFontSize}
                        onChange={(e) => setDraftSettings({ ...draftSettings, clockFontSize: parseInt(e.target.value) })}
                        className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                      />
                      <span className="font-mono text-indigo-400 font-bold text-[13.5px] shrink-0 w-9 text-right">{draftSettings.clockFontSize}px</span>
                    </div>
                  </div>

                  {/* Timer Font Size Slider */}
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-[13.5px] text-gray-400">{lang === 'en' ? 'Timer Font Size' : '타이머 글자 크기'}</span>
                    <div className="flex items-center gap-1.5 flex-1 max-w-[140px]">
                      <input
                        type="range"
                        min={16}
                        max={36}
                        step={2}
                        value={draftSettings.timerFontSize}
                        onChange={(e) => setDraftSettings({ ...draftSettings, timerFontSize: parseInt(e.target.value) })}
                        className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                      />
                      <span className="font-mono text-indigo-400 font-bold text-[13.5px] shrink-0 w-9 text-right">{draftSettings.timerFontSize}px</span>
                    </div>
                  </div>

                  {/* Show Current Time Checkbox */}
                  <div className="flex items-center justify-between gap-4 pt-1">
                    <span className="text-[13.5px] text-gray-400">{lang === 'en' ? 'Show Clock in Widget' : '위젯 내 현재 시간표시'}</span>
                    <label className="flex items-center gap-1.5 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={draftSettings.showCurrentTimeCompact}
                        onChange={(e) => setDraftSettings({ ...draftSettings, showCurrentTimeCompact: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="relative w-7 h-4 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* Widget Opacity */}
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-[13.5px] text-gray-400">{lang === 'en' ? 'Widget Opacity' : '위젯 투명도'}</span>
                    <div className="flex items-center gap-1.5 flex-1 max-w-[140px]">
                      <input
                        type="range"
                        min={30}
                        max={100}
                        step={5}
                        value={draftSettings.widgetOpacity}
                        onChange={(e) => setDraftSettings({ ...draftSettings, widgetOpacity: parseInt(e.target.value) })}
                        className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                      />
                      <span className="font-mono text-blue-500 font-bold text-[13.5px] shrink-0 w-9 text-right">{draftSettings.widgetOpacity}%</span>
                    </div>
                  </div>
                </div>

                {/* 4. Window opacity & Font settings */}
                <div className="flex flex-col gap-2.5 p-3 bg-black/10 dark:bg-white/5 rounded-xl border border-gray-500/10">
                  <span className="text-[13.5px] font-bold text-rose-400 flex items-center gap-1">👁️ {lang === 'en' ? 'Main Window settings' : '메인창 설정'}</span>
                  <div className="flex items-center justify-between gap-4 mt-1">
                    <span className="text-[13.5px] text-gray-400">{lang === 'en' ? 'Window Opacity' : '창 투명도'}</span>
                    <div className="flex items-center gap-1.5 flex-1 max-w-[140px]">
                      <input
                        type="range"
                        min={20}
                        max={100}
                        step={5}
                        value={draftSettings.mainOpacity}
                        onChange={(e) => setDraftSettings({ ...draftSettings, mainOpacity: parseInt(e.target.value) })}
                        className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                      />
                      <span className="font-mono text-indigo-500 font-bold text-[13.5px] shrink-0 w-9 text-right">{draftSettings.mainOpacity}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-[13.5px] text-gray-400">{lang === 'en' ? 'Font Family' : '폰트 선택'}</span>
                    <select
                      value={draftSettings.selectedFont}
                      onChange={(e) => setDraftSettings({ ...draftSettings, selectedFont: e.target.value })}
                      className="bg-gray-800 text-gray-300 text-[13.5px] rounded px-1.5 py-1 border border-gray-700 focus:outline-none focus:border-blue-500"
                    >
                      <option value="font-sans">Inter (Sans-Serif)</option>
                      <option value="font-display">Space Grotesk (Tech)</option>
                      <option value="font-mono">JetBrains Mono (Coding)</option>
                      <option value="font-serif">{lang === 'en' ? 'Myeongjo (Serif)' : '나눔명조 (세리프)'}</option>
                      <option value="font-malgun">{lang === 'en' ? 'Malgun Gothic (Windows)' : '맑은 고딕 (윈도우 기본)'}</option>
                      <option value="font-gulim">{lang === 'en' ? 'Gulim (Windows)' : '굴림 (윈도우 기본)'}</option>
                      <option value="font-batang">{lang === 'en' ? 'Batang (Windows)' : '바탕 (윈도우 기본)'}</option>
                    </select>
                  </div>
                </div>

                {/* 5. Reservation Alert Settings */}
                <div className="flex flex-col gap-2.5 p-3 bg-black/10 dark:bg-white/5 rounded-xl border border-gray-500/10">
                  <span className="text-[13.5px] font-bold text-amber-400 flex items-center gap-1">⏰ {lang === 'en' ? 'Reservation Warning Delay' : '예약작업 안내 대기 시간'}</span>
                  <div className="flex items-center justify-between gap-4 mt-1">
                    <span className="text-[13.5px] text-gray-400">{lang === 'en' ? 'Warning Countdown' : '안내 대기시간'}</span>
                    <select
                      value={draftSettings.graceSeconds}
                      onChange={(e) => setDraftSettings({ ...draftSettings, graceSeconds: parseInt(e.target.value) })}
                      className="bg-gray-800 text-gray-300 text-[13.5px] rounded px-1.5 py-1 border border-gray-700 focus:outline-none focus:border-blue-500 cursor-pointer"
                    >
                      <option value="5">5{lang === 'en' ? ' seconds' : '초'}</option>
                      <option value="10">10{lang === 'en' ? ' seconds' : '초'}</option>
                      <option value="20">20{lang === 'en' ? ' seconds' : '초'}</option>
                      <option value="30">30{lang === 'en' ? ' seconds' : '초'}</option>
                      <option value="60">1{lang === 'en' ? ' minute' : '분'}</option>
                      <option value="180">3{lang === 'en' ? ' minutes' : '분'}</option>
                      <option value="300">5{lang === 'en' ? ' minutes' : '분'}</option>
                    </select>
                  </div>
                </div>

                {/* 6. Force Close Running Apps Flag (/f Parameter) */}
                <div className="flex flex-col gap-2 p-3 bg-black/10 dark:bg-white/5 rounded-xl border border-gray-500/10">
                  <span className="text-[13.5px] font-bold text-rose-400 flex items-center gap-1">⚡ {lang === 'en' ? 'Force Close Running Programs (/f Parameter)' : '실행 중인 프로그램 강제 종료 (/f 파라미터)'}</span>
                  <p className="text-[13.5px] text-gray-400 leading-relaxed">
                    {lang === 'en'
                      ? 'Appends Windows /f parameter to system shutdown/restart. Forces running apps or unsaved prompt dialogs to close without freezing or halting the power action. (Default: Enabled)'
                      : '컴퓨터 종료/재시작 시 저장 확인 창이나 응답 없는 프로그램이 있더라도 시스템 제어가 중단되지 않도록 Windows /f 파라미터를 강제 적용합니다. (기본: 옵션 활성화 상태)'}
                  </p>
                  <label className="flex items-center gap-2 cursor-pointer mt-0.5">
                    <input
                      type="checkbox"
                      checked={draftSettings.forceCloseEnabled}
                      onChange={(e) => setDraftSettings({ ...draftSettings, forceCloseEnabled: e.target.checked })}
                      className="rounded border-gray-600 text-rose-600 focus:ring-0 cursor-pointer"
                    />
                    <span className="text-[13.5px] text-gray-200 font-semibold">
                      {lang === 'en' ? 'Enable Force Close (/f) by default' : '실행 중인 프로그램 강제 종료 (/f) 활성화 (기본 권장)'}
                    </span>
                  </label>
                </div>
              </div>

              {/* Confirm / Cancel Buttons */}
              <div className="grid grid-cols-2 gap-2 mt-1">
                <button
                  onClick={handleCancelSettings}
                  className="py-2 rounded-xl bg-gray-700 hover:bg-gray-600 text-gray-200 font-semibold text-[13.5px] cursor-pointer transition-all"
                >
                  {lang === 'en' ? 'Cancel' : '취소'}
                </button>
                <button
                  onClick={handleConfirmSettings}
                  className="py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-[13.5px] cursor-pointer transition-all shadow-md active:scale-[0.98]"
                >
                  {lang === 'en' ? 'Confirm & Apply' : '확인 (적용)'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
