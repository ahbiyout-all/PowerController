import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Calendar, Clock, Power, RotateCw, Moon, Laptop, LogOut, CheckCircle, ArrowRight, X } from 'lucide-react';
import { PowerMode, ThemeType } from '../types';

interface ScheduledRule {
  id: string;
  name?: string;
  label?: string;
  type: 'daily' | 'weekly' | 'once' | 'interval';
  mode: PowerMode;
  time?: string;
  days?: number[];
  intervalMinutes?: number;
  date?: string;
  isActive: boolean;
  notifyBefore?: boolean;
}

interface StartupTodayTasksModalProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: ScheduledRule[];
  lang: 'ko' | 'en';
  theme?: ThemeType;
  onNavigateToScheduler: () => void;
}

const modalThemeConfigs = {
  dark: {
    container: 'bg-gray-900/95 border-blue-500/50 text-white',
    headerBorder: 'border-gray-800',
    titleText: 'text-white',
    subText: 'text-gray-400',
    card: 'bg-gray-800/90 border-gray-700/60 hover:border-blue-500/40',
    cardTitle: 'text-white',
    cardSubtext: 'text-gray-400',
    iconBg: 'bg-gray-900 border-gray-700',
    closeBtn: 'bg-gray-800 hover:bg-gray-700 text-gray-300',
    highlightText: 'text-cyan-300'
  },
  gray: {
    container: 'bg-[#1e293b]/95 border-[#475569] text-[#f1f5f9]',
    headerBorder: 'border-[#475569]/60',
    titleText: 'text-[#f1f5f9]',
    subText: 'text-[#cbd5e1]',
    card: 'bg-[#334155]/80 border-[#475569]/80 hover:border-blue-400',
    cardTitle: 'text-[#f1f5f9]',
    cardSubtext: 'text-[#cbd5e1]',
    iconBg: 'bg-[#1e293b] border-[#475569]',
    closeBtn: 'bg-[#334155] hover:bg-[#475569] text-slate-200',
    highlightText: 'text-blue-300'
  },
  beige: {
    container: 'bg-[#faf6ee] border-[#dfd5c6] text-[#4a3e2b] shadow-2xl',
    headerBorder: 'border-[#dfd5c6]',
    titleText: 'text-[#4a3e2b]',
    subText: 'text-[#8c785c]',
    card: 'bg-white border-[#dfd5c6] hover:border-[#8c785c]',
    cardTitle: 'text-[#4a3e2b]',
    cardSubtext: 'text-[#8c785c]',
    iconBg: 'bg-[#faf6ee] border-[#dfd5c6]',
    closeBtn: 'bg-[#ebe2d4] hover:bg-[#dfd5c6] text-[#4a3e2b]',
    highlightText: 'text-[#8c785c]'
  }
};

export default function StartupTodayTasksModal({
  isOpen,
  onClose,
  tasks,
  lang,
  theme = 'dark',
  onNavigateToScheduler,
}: StartupTodayTasksModalProps) {
  const currentModalTheme = modalThemeConfigs[theme] || modalThemeConfigs.dark;
  const [countdown, setCountdown] = useState<number>(5);

  useEffect(() => {
    if (!isOpen || tasks.length === 0) return;
    setCountdown(5);
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onClose();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isOpen, tasks.length, onClose]);

  if (!isOpen || tasks.length === 0) return null;

  const getPowerModeIcon = (mode: PowerMode) => {
    switch (mode) {
      case 'shutdown': return <Power className="w-3.5 h-3.5 text-rose-400" />;
      case 'restart': return <RotateCw className="w-3.5 h-3.5 text-blue-400" />;
      case 'sleep': return <Moon className="w-3.5 h-3.5 text-indigo-400" />;
      case 'screenoff': return <Laptop className="w-3.5 h-3.5 text-amber-400" />;
      case 'logout': return <LogOut className="w-3.5 h-3.5 text-emerald-400" />;
      case 'alarm': return <Clock className="w-3.5 h-3.5 text-pink-400" />;
      default: return <Power className="w-3.5 h-3.5 text-rose-400" />;
    }
  };

  const getModeName = (mode: PowerMode) => {
    if (lang === 'en') {
      const names: Record<PowerMode, string> = {
        shutdown: 'Shutdown',
        restart: 'Restart',
        sleep: 'Sleep',
        screenoff: 'Screen Off',
        logout: 'Log Out',
        alarm: 'Alarm'
      };
      return names[mode] || mode;
    }
    const names: Record<PowerMode, string> = {
      shutdown: '시스템 종료',
      restart: '재시동',
      sleep: '절전 모드',
      screenoff: '모니터 끄기',
      logout: '로그아웃',
      alarm: '경보 알람'
    };
    return names[mode] || mode;
  };

  const getTypeBadge = (rule: ScheduledRule) => {
    if (rule.type === 'daily') {
      return <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-medium">{lang === 'en' ? 'Daily' : '매일'}</span>;
    }
    if (rule.type === 'weekly') {
      return <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-medium">{lang === 'en' ? 'Weekly' : '요일별'}</span>;
    }
    if (rule.type === 'once') {
      return <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-medium">{lang === 'en' ? 'Once' : '1회'}</span>;
    }
    return <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-medium">{lang === 'en' ? 'Interval' : '반복'}</span>;
  };

  return (
    <AnimatePresence>
      <div className="fixed bottom-4 right-4 z-[10001] select-none pointer-events-none">
        {/* Tray Popup Card (Non-blocking, anchored to bottom-right system tray) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 30 }}
          transition={{ type: 'spring', damping: 25, stiffness: 350 }}
          className={`pointer-events-auto relative w-[380px] max-w-[calc(100vw-32px)] rounded-2xl border-2 backdrop-blur-md shadow-2xl overflow-hidden p-4 space-y-3 ${currentModalTheme.container}`}
        >
          {/* Top glowing accent line */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-indigo-500"></div>

          {/* Header */}
          <div className={`flex items-start justify-between border-b pb-2.5 pt-0.5 ${currentModalTheme.headerBorder}`}>
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30 flex-shrink-0">
                <Calendar className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <h3 className={`font-bold text-xs flex items-center gap-1.5 ${currentModalTheme.titleText}`}>
                  <span>{lang === 'en' ? "Today's Scheduled Tasks" : "오늘의 예약 작업 알림"}</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-blue-600 text-white font-mono font-bold">
                    {tasks.length}
                  </span>
                </h3>
                <p className={`text-[10px] truncate ${currentModalTheme.subText}`}>
                  {lang === 'en' 
                    ? "System Tray Briefing: Active tasks scheduled today"
                    : "시스템 트레이 브리핑: 오늘 예약된 작업 목록"}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className={`p-1 rounded-lg transition-colors cursor-pointer ${theme === 'beige' ? 'text-[#8c785c] hover:bg-[#ebe2d4]' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}
              title={lang === 'en' ? 'Close' : '닫기'}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Task List */}
          <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
            {tasks.map((task) => (
              <div
                key={task.id}
                className={`p-2 rounded-xl border flex items-center justify-between gap-2.5 transition-colors ${currentModalTheme.card}`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <div className={`p-1 rounded-md flex-shrink-0 border ${currentModalTheme.iconBg}`}>
                    {getPowerModeIcon(task.mode)}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className={`font-bold text-[11px] truncate max-w-[140px] ${currentModalTheme.cardTitle}`}>
                        {task.label || task.name || (lang === 'en' ? 'Untitled Rule' : '무제 규칙')}
                      </span>
                      {getTypeBadge(task)}
                    </div>
                    <div className={`text-[9px] flex items-center gap-1 mt-0.5 ${currentModalTheme.cardSubtext}`}>
                      <span>{getModeName(task.mode)}</span>
                      <span>•</span>
                      <span className={`font-mono font-semibold ${currentModalTheme.highlightText}`}>
                        {task.time ? `🕒 ${task.time}` : `⏱️ ${task.intervalMinutes}분 간격`}
                      </span>
                    </div>
                  </div>
                </div>

                <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
              </div>
            ))}
          </div>

          {/* Footer Buttons */}
          <div className="pt-1 flex items-center gap-2">
            <button
              onClick={onClose}
              className={`flex-1 py-1.5 rounded-xl text-[11px] font-bold transition-all cursor-pointer ${currentModalTheme.closeBtn}`}
            >
              {lang === 'en' ? `Close (${countdown}s)` : `닫기 (${countdown}초)`}
            </button>
            <button
              onClick={() => {
                onClose();
                onNavigateToScheduler();
              }}
              className="flex-1 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold flex items-center justify-center gap-1.5 transition-all shadow-md active:scale-95 cursor-pointer"
            >
              <span>{lang === 'en' ? 'Open Scheduler' : '스케줄러 열기'}</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
