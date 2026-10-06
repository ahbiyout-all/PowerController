import React, { useState, useEffect, useRef } from 'react';
import {
  Calendar,
  Clock,
  Plus,
  Trash2,
  Play,
  AlertCircle,
  Power,
  RotateCw,
  Moon,
  Laptop,
  LogOut,
  CheckSquare,
  Square,
  History,
  Timer,
  Edit2
} from 'lucide-react';
import { PowerMode, PowerSchedule, ScheduleType, ThemeType } from '../types';

interface AdvancedSchedulerProps {
  onTriggerRule: (mode: PowerMode, label: string, forceCloseApps: boolean, warningNotification: boolean) => void;
  addLog: (msg: string) => void;
  soundEnabled: boolean;
  playWarningTick: () => void;
  lang?: 'ko' | 'en';
  theme?: ThemeType;
}

const schedulerThemeConfigs = {
  dark: {
    container: 'bg-[#181a24] border-[#2d3142]/60 text-[#e1e4ed]',
    form: 'bg-[#1a1d29] border-[#2d3142]/60',
    input: 'bg-black/40 text-white border-gray-700 focus:ring-blue-500 focus:border-blue-500',
    card: 'bg-[#1a1d29] border-[#2d3142]/60 text-[#e1e4ed]',
    cardSubtext: 'text-gray-400',
    badge: 'bg-gray-800 border-gray-700 text-gray-300'
  },
  gray: {
    container: 'bg-[#242f41] border-[#475569]/60 text-[#f1f5f9]',
    form: 'bg-[#1e293b]/50 border-[#475569]/60',
    input: 'bg-[#1e293b]/70 text-[#f1f5f9] border-[#475569] focus:ring-blue-400 focus:border-blue-400',
    card: 'bg-[#1e293b]/60 border-[#475569]/65 text-[#f1f5f9]',
    cardSubtext: 'text-slate-300',
    badge: 'bg-[#475569] border-[#475569] text-slate-200'
  },
  beige: {
    container: 'bg-white border-[#dfd5c6] text-[#4a3e2b]',
    form: 'bg-[#faf6ee] border-[#dfd5c6]',
    input: 'bg-white text-[#4a3e2b] border-[#dfd5c6] focus:ring-[#8c785c] focus:border-[#8c785c]',
    card: 'bg-[#faf6ee] border-[#dfd5c6] text-[#4a3e2b]',
    cardSubtext: 'text-[#6e5d47]',
    badge: 'bg-[#ebe2d4] border-[#dfd5c6] text-[#8c785c]'
  }
};

const get_default_schedules = (lang: 'ko' | 'en'): PowerSchedule[] => [
  {
    id: 'rule-1',
    label: lang === 'en' ? 'Night standby power cutoff (Daily)' : '야간 대기 전력 차단 (매일)',
    type: 'daily',
    mode: 'sleep',
    time: '23:30',
    forceCloseApps: true,
    warningNotification: true,
    isActive: true,
    createdAt: new Date().toISOString()
  },
  {
    id: 'rule-2',
    label: lang === 'en' ? 'Sunday regular server clean assessment' : '서버 클린 일요 조기 정기 점검',
    type: 'weekly',
    mode: 'restart',
    time: '04:00',
    days: [0], // Sunday
    forceCloseApps: true,
    warningNotification: true,
    isActive: false,
    createdAt: new Date().toISOString()
  },
  {
    id: 'rule-3',
    label: lang === 'en' ? 'Screen off when idle interval loop' : '자리 비움 화면 끄기 순환 대기',
    type: 'interval',
    mode: 'screenoff',
    intervalMinutes: 45,
    forceCloseApps: false,
    warningNotification: false,
    isActive: true,
    createdAt: new Date().toISOString()
  }
];

export const POPULAR_SCHEDULE_TITLES = [
  { ko: '심야 PC 자동 종료', en: 'Midnight Auto Shutdown' },
  { ko: '퇴근 시간 전원 끄기', en: 'End of Work Shutdown' },
  { ko: '대용량 다운로드 후 종료', en: 'Post-Download Auto Shutdown' },
  { ko: '점심시간 빠른 재부팅', en: 'Lunch Break Reboot' },
  { ko: '자리 비움 절전 모드', en: 'Away / Idle Sleep Mode' },
  { ko: '새벽 정기 시스템 점검 재시작', en: 'Dawn Scheduled System Reboot' },
  { ko: '업무 시작 준비 알람', en: 'Work Start Reminder Alarm' },
  { ko: '영화/영상 시청 후 종료', en: 'Post-Movie Auto Shutdown' },
  { ko: '미사용 모니터 화면 끄기', en: 'Screen Off on Inactivity' },
  { ko: '렌더링/인코딩 완료 후 종료', en: 'Post-Rendering Auto Shutdown' }
];

export default function AdvancedScheduler({ onTriggerRule, addLog, soundEnabled, playWarningTick, lang = 'ko', theme = 'dark' }: AdvancedSchedulerProps) {
  const currentSchedTheme = schedulerThemeConfigs[theme] || schedulerThemeConfigs.dark;
  const [rules, setRules] = useState<PowerSchedule[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  // Form State fields
  const [label, setLabel] = useState('');
  const [type, setType] = useState<ScheduleType>('daily');
  const [mode, setMode] = useState<PowerMode>('shutdown');
  const [timeH, setTimeH] = useState('22');
  const [timeM, setTimeM] = useState('00');
  const [intervalMins, setIntervalMins] = useState(60);
  const [selectedDays, setSelectedDays] = useState<number[]>([1, 2, 3, 4, 5]); // Mon-Fri
  const [forceCloseApps, setForceCloseApps] = useState(true);
  const [warningNotification, setWarningNotification] = useState(true);

  // Live updates for countdown
  const [nowTime, setNowTime] = useState<Date>(new Date());
  const schedulerTimerRef = useRef<NodeJS.Timeout | null>(null);
  const formContainerRef = useRef<HTMLFormElement | null>(null);

  // Load schedules
  useEffect(() => {
    try {
      const stored = localStorage.getItem('system_power_scheduler_rules_v2');
      if (stored) {
        setRules(JSON.parse(stored));
      } else {
        const defaults = get_default_schedules(lang);
        setRules(defaults);
        localStorage.setItem('system_power_scheduler_rules_v2', JSON.stringify(defaults));
      }
    } catch (e) {
      setRules(get_default_schedules(lang));
    }
  }, [lang]);

  const saveRules = (updatedRules: PowerSchedule[]) => {
    setRules(updatedRules);
    localStorage.setItem('system_power_scheduler_rules_v2', JSON.stringify(updatedRules));
  };

  // Keep ticks accurate
  useEffect(() => {
    schedulerTimerRef.current = setInterval(() => {
      const currentNow = new Date();
      setNowTime(currentNow);
      checkAndExecuteRules(currentNow);
    }, 1000);

    return () => {
      if (schedulerTimerRef.current) {
        clearInterval(schedulerTimerRef.current);
      }
    };
  }, [rules]);

  // Check matching criteria for a rule
  const checkAndExecuteRules = (currentDate: Date) => {
    const curH = currentDate.getHours();
    const curM = currentDate.getMinutes();
    const curS = currentDate.getSeconds();
    const curDay = currentDate.getDay(); // 0 = Sun ... 6 = Sat

    // Trigger only when seconds is 0 to avoid multi-execution
    if (curS !== 0) return;

    let updatedList = [...rules];
    let listChanged = false;

    rules.forEach((rule) => {
      if (!rule.isActive) return;

      let shouldTrigger = false;
      const targetTimeStr = rule.time || '';
      const [tgtH, tgtM] = targetTimeStr.split(':').map(Number);

      if (rule.type === 'once') {
        if (curH === tgtH && curM === tgtM) {
          shouldTrigger = true;
          rule.isActive = false;
          listChanged = true;
        }
      } else if (rule.type === 'daily') {
        if (curH === tgtH && curM === tgtM) {
          shouldTrigger = true;
        }
      } else if (rule.type === 'weekly') {
        const matchesDay = rule.days?.includes(curDay);
        if (matchesDay && curH === tgtH && curM === tgtM) {
          shouldTrigger = true;
        }
      } else if (rule.type === 'interval') {
        const createdDate = new Date(rule.createdAt);
        const diffMs = currentDate.getTime() - createdDate.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const interval = rule.intervalMinutes || 30;

        if (diffMins > 0 && diffMins % interval === 0) {
          shouldTrigger = true;
        }
      }

      if (shouldTrigger) {
        rule.lastExecuted = currentDate.toLocaleString(lang === 'en' ? 'en-US' : 'ko-KR');
        listChanged = true;
        if (lang === 'en') {
          addLog(`📢 [Scheduler triggered] rule "${rule.label}" matched. Initiating virtual [${getPowerModeLabel(rule.mode)}] action.`);
        } else {
          addLog(`📢 [스케줄러 작동 트리거] "${rule.label}" 규칙 조건이 부합하여 가상 [${getPowerModeLabel(rule.mode)}]를 시뮬레이션 추진합니다.`);
        }
        
        onTriggerRule(rule.mode, rule.label, rule.forceCloseApps, rule.warningNotification);
      }
    });

    if (listChanged) {
      saveRules(updatedList);
    }
  };

  // Helper labels & styles
  const getPowerModeLabel = (m: PowerMode) => {
    switch (m) {
      case 'shutdown': return lang === 'en' ? 'Shutdown' : '시스템 종료';
      case 'restart': return lang === 'en' ? 'System Restart' : '시스템 재시작';
      case 'sleep': return lang === 'en' ? 'Standby Sleep' : '절전 대기 진입';
      case 'screenoff': return lang === 'en' ? 'Screen Off' : '화면 전원 끄기';
      case 'logout': return lang === 'en' ? 'Account Logout' : '계정 로그아웃';
      case 'alarm': return lang === 'en' ? 'Scheduler Alarm' : '예약 알람 알림';
    }
  };

  const getPowerModeColor = (m: PowerMode) => {
    switch (m) {
      case 'shutdown': return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
      case 'restart': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
      case 'sleep': return 'text-purple-500 bg-purple-500/10 border-purple-500/20';
      case 'screenoff': return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
      case 'logout': return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
      case 'alarm': return 'text-pink-500 bg-pink-500/10 border-pink-500/20';
    }
  };

  const getPowerModeIcon = (m: PowerMode) => {
    switch (m) {
      case 'shutdown': return <Power className="w-3.5 h-3.5" />;
      case 'restart': return <RotateCw className="w-3.5 h-3.5 animate-spin-slow" />;
      case 'sleep': return <Moon className="w-3.5 h-3.5" />;
      case 'screenoff': return <Laptop className="w-3.5 h-3.5" />;
      case 'logout': return <LogOut className="w-3.5 h-3.5" />;
      case 'alarm': return <Clock className="w-3.5 h-3.5" />;
    }
  };

  // Schedule type labels
  const getScheduleTypeLabel = (t: ScheduleType) => {
    switch (t) {
      case 'once': return lang === 'en' ? 'Once' : '특정 한 번';
      case 'daily': return lang === 'en' ? 'Daily' : '매일 반복';
      case 'weekly': return lang === 'en' ? 'Weekly' : '매주 특정 요일';
      case 'interval': return lang === 'en' ? 'Interval' : '주기적 타이머';
    }
  };

  // Day representation
  const getDaysLabel = (days: number[] | undefined) => {
    if (!days || days.length === 0) return lang === 'en' ? 'None' : '없음';
    const dayNames = lang === 'en' 
      ? ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
      : ['일', '월', '화', '수', '목', '금', '토'];

    if (days.length === 7) return lang === 'en' ? 'Everyday' : '매일';
    if (days.length === 5 && !days.includes(0) && !days.includes(6)) return lang === 'en' ? 'Weekdays (Mon-Fri)' : '평일(월~금)';
    return days.map(d => dayNames[d]).join(', ');
  };

  // Calculate next occurrence countdown
  const getNextOccurrenceString = (schedule: PowerSchedule): string => {
    if (!schedule.isActive) return lang === 'en' ? 'Paused' : '일시 정지됨';

    const calculatedDate = getNextOccurrenceDate(schedule);
    if (!calculatedDate) return lang === 'en' ? 'Pending calculation' : '계산 보류';

    const diffMs = calculatedDate.getTime() - nowTime.getTime();
    if (diffMs <= 0) return lang === 'en' ? 'Trigger imminent' : '곧 트리거 예상';

    const hours = Math.floor(diffMs / 3600000);
    const mins = Math.floor((diffMs % 3600000) / 60000);
    const secs = Math.floor((diffMs % 60000) / 1000);

    const parts = [];
    if (hours > 0) parts.push(`${hours}${lang === 'en' ? 'h' : '시간'}`);
    if (mins > 0) parts.push(`${mins}${lang === 'en' ? 'm' : '분'}`);
    parts.push(`${secs}${lang === 'en' ? 's' : '초'}`);

    return lang === 'en' ? `Runs in ${parts.join(' ')}` : `${parts.join(' ')} 후 실행`;
  };

  const getNextOccurrenceDate = (schedule: PowerSchedule): Date | null => {
    const targetTimeStr = schedule.time || '00:00';
    const [tgtH, tgtM] = targetTimeStr.split(':').map(Number);

    const checkDate = new Date(nowTime);

    if (schedule.type === 'once' || schedule.type === 'daily') {
      checkDate.setHours(tgtH, tgtM, 0, 0);
      if (checkDate.getTime() < nowTime.getTime()) {
        checkDate.setDate(checkDate.getDate() + 1);
      }
      return checkDate;
    }

    if (schedule.type === 'weekly') {
      const allowedDays = schedule.days || [];
      if (allowedDays.length === 0) return null;

      for (let i = 0; i <= 8; i++) {
        const prospectiveDate = new Date(nowTime);
        prospectiveDate.setDate(prospectiveDate.getDate() + i);
        prospectiveDate.setHours(tgtH, tgtM, 0, 0);

        const currentDayOfWeek = prospectiveDate.getDay();
        if (allowedDays.includes(currentDayOfWeek)) {
          if (prospectiveDate.getTime() > nowTime.getTime()) {
            return prospectiveDate;
          }
        }
      }
      return null;
    }

    if (schedule.type === 'interval') {
      const interval = schedule.intervalMinutes || 30;
      const createdDate = new Date(schedule.createdAt);
      
      const elapsedMs = nowTime.getTime() - createdDate.getTime();
      const elapsedMins = Math.floor(elapsedMs / 60000);
      
      const intervalsPassed = Math.floor(elapsedMins / interval);
      const nextIntervalCount = intervalsPassed + 1;
      
      return new Date(createdDate.getTime() + (nextIntervalCount * interval * 60000));
    }

    return null;
  };

  const resetForm = () => {
    setLabel('');
    setType('daily');
    setMode('shutdown');
    setTimeH('22');
    setTimeM('00');
    setIntervalMins(60);
    setSelectedDays([1, 2, 3, 4, 5]);
    setForceCloseApps(true);
    setWarningNotification(true);
    setEditingRuleId(null);
    setShowAddForm(false);
  };

  const handleStartEdit = (rule: PowerSchedule, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingRuleId(rule.id);
    setLabel(rule.label);
    setType(rule.type);
    setMode(rule.mode);
    if (rule.time) {
      const [h, m] = rule.time.split(':');
      setTimeH(h);
      setTimeM(m);
    }
    if (rule.days) {
      setSelectedDays(rule.days);
    }
    if (rule.intervalMinutes) {
      setIntervalMins(rule.intervalMinutes);
    }
    setForceCloseApps(!!rule.forceCloseApps);
    setWarningNotification(!!rule.warningNotification);
    setShowAddForm(true);
    addLog(lang === 'en' ? `Entering edit mode for rule: "${rule.label}"` : `🔧 스케줄러 수정 모드 진입: "${rule.label}"`);

    // Smoothly scroll the container to center on the edit form
    setTimeout(() => {
      formContainerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 80);
  };

  const handleCreateRule = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    const trimmedLabel = label.trim();
    if (!trimmedLabel) {
      setErrorMsg(lang === 'en' ? 'Please provide a schedule name description.' : '규칙 설명(예: 전원 안전 끄기)을 명시해주세요.');
      return;
    }

    if (type === 'weekly' && selectedDays.length === 0) {
      setErrorMsg(lang === 'en' ? 'Please select at least one weekday.' : '반복할 요일을 하루 이상 지정해주세요.');
      return;
    }

    if (type === 'interval' && (!intervalMins || intervalMins <= 0)) {
      setErrorMsg(lang === 'en' ? 'Interval must be at least 1 minute.' : '반복 간격은 최소 1분 이상 설정해야 합니다.');
      return;
    }

    if (editingRuleId) {
      const updated = rules.map(r => {
        if (r.id === editingRuleId) {
          return {
            ...r,
            label: trimmedLabel,
            type,
            mode,
            time: type !== 'interval' ? `${timeH.padStart(2, '0')}:${timeM.padStart(2, '0')}` : undefined,
            days: type === 'weekly' ? selectedDays : undefined,
            intervalMinutes: type === 'interval' ? intervalMins : undefined,
            forceCloseApps,
            warningNotification,
          };
        }
        return r;
      });
      saveRules(updated);
      addLog(lang === 'en' ? `Schedule rule updated: "${trimmedLabel}"` : `📅 스케줄 규칙 수정 완료: "${trimmedLabel}"`);
      resetForm();
    } else {
      const newRule: PowerSchedule = {
        id: `rule-${Date.now()}`,
        label: trimmedLabel,
        type,
        mode,
        time: type !== 'interval' ? `${timeH.padStart(2, '0')}:${timeM.padStart(2, '0')}` : undefined,
        days: type === 'weekly' ? selectedDays : undefined,
        intervalMinutes: type === 'interval' ? intervalMins : undefined,
        forceCloseApps,
        warningNotification,
        isActive: true,
        createdAt: new Date().toISOString()
      };

      const updated = [...rules, newRule];
      saveRules(updated);
      addLog(lang === 'en' ? `New schedule rule registered successfully: "${trimmedLabel}"` : `📅 새 예약 스케줄 규칙 등록 성공: "${trimmedLabel}"`);
      resetForm();
    }
  };

  const handleDeleteRule = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const filtered = rules.filter(r => r.id !== id);
    saveRules(filtered);
    addLog(lang === 'en' ? 'Schedule rule completely deleted.' : '🗑️ 스케줄 규칙을 데이터베이스에서 삭제했습니다.');
  };

  const toggleRuleActive = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = rules.map(r => {
      if (r.id === id) {
        const newState = !r.isActive;
        if (lang === 'en') {
          addLog(`Scheduler rule "${r.label}" status set to [${newState ? 'On' : 'Off'}].`);
        } else {
          addLog(`🔧 스케줄러 "${r.label}" 활성 상태를 [${newState ? '켜기' : '끄기'}] 설정했습니다.`);
        }
        return { ...r, isActive: newState };
      }
      return r;
    });
    saveRules(updated);
  };

  const handleManualTrigger = (rule: PowerSchedule, e: React.MouseEvent) => {
    e.stopPropagation();
    if (lang === 'en') {
      addLog(`⚡ Manual override triggered for schedule rule "${rule.label}".`);
    } else {
      addLog(`⚡ 사용자가 스케줄 규칙 "${rule.label}"을 즉시 가상 트리거 하였습니다.`);
    }
    onTriggerRule(rule.mode, rule.label, rule.forceCloseApps, rule.warningNotification);
  };

  const toggleDaySelection = (dayNum: number) => {
    if (selectedDays.includes(dayNum)) {
      setSelectedDays(selectedDays.filter(d => d !== dayNum));
    } else {
      setSelectedDays([...selectedDays, dayNum].sort());
    }
  };

  return (
    <div className={`rounded-xl border p-4 transition-all duration-300 flex flex-col flex-1 h-full select-none text-left ${currentSchedTheme.container}`}>
      <div className="flex items-center justify-between mb-3 border-b border-gray-100/10 pb-2.5">
        <div className="flex items-center gap-1.5">
          <Calendar className="w-4.5 h-4.5 text-blue-500" />
          <h3 className="font-display font-semibold text-sm">
            {lang === 'en' ? '📅 Adaptive Multi-Scheduler Engine' : '📅 고성능 전력 다중 스케줄러'}
          </h3>
        </div>
        
        <button
          id="btn-toggle-add-sched"
          onClick={() => {
            if (editingRuleId) {
              resetForm();
            } else {
              setShowAddForm(!showAddForm);
            }
          }}
          className={`text-xs flex items-center gap-1 ${editingRuleId ? 'bg-amber-500 hover:bg-amber-600' : 'bg-blue-500 hover:bg-blue-600'} active:scale-95 text-white px-2.5 py-1 rounded-lg font-medium cursor-pointer transition-all shadow`}
        >
          {editingRuleId ? (lang === 'en' ? 'Cancel Edit' : '수정 취소') : (showAddForm ? (lang === 'en' ? 'Collapse' : '접기') : (lang === 'en' ? 'Create Rule' : '규칙 생성'))}
          <Plus className={`w-3.5 h-3.5 transition-transform duration-200 ${showAddForm || editingRuleId ? 'rotate-45' : ''}`} />
        </button>
      </div>

      <p className="text-[11px] text-gray-500 dark:text-gray-400 mb-3 leading-relaxed">
        {lang === 'en' 
          ? 'Coordinate multiple automated computer power down operations. Multiple scheduler criteria run securely inside localized background checks.'
          : '시간/요일/단위 간격을 조율해 컴퓨터 전원 자동 오프 동작을 세대 수준으로 조율하세요. 다중 배치 제어가 로컬 캐시를 기반으로 상시 감시 전개됩니다.'}
      </p>

      {/* Scheduler rule formulation form */}
      {showAddForm && (
        <form
          ref={formContainerRef}
          onSubmit={handleCreateRule}
          className={`mb-4 p-3.5 rounded-lg border space-y-3 max-h-[350px] overflow-y-auto no-scrollbar transition-all duration-350 ${currentSchedTheme.form} ${
            editingRuleId
              ? 'border-amber-500 shadow-md shadow-amber-500/10 ring-1 ring-amber-500/30'
              : ''
          }`}
        >
          {editingRuleId && (
            <div className="bg-amber-500/10 border border-amber-500/20 text-amber-500 text-[11px] font-bold p-2 rounded-md flex items-center justify-between mb-2">
              <span>🔧 {lang === 'en' ? 'Modify Schedule Rule' : '스케줄 규칙 내용 수정 중'}</span>
              <button
                type="button"
                onClick={resetForm}
                className="hover:underline text-[10px] text-gray-400 cursor-pointer"
              >
                {lang === 'en' ? 'Reset' : '원래대로'}
              </button>
            </div>
          )}
          
          {/* Label name */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-[10px] uppercase font-bold text-gray-400">
                {lang === 'en' ? 'Schedule Title / Memo' : '스케줄 이름 (메모)'}
              </label>
              <div className="flex items-center gap-1">
                <select
                  id="select-popular-schedule-title"
                  defaultValue=""
                  onChange={(e) => {
                    if (e.target.value) {
                      setLabel(e.target.value);
                      e.target.value = '';
                    }
                  }}
                  className={`text-[10px] font-medium px-2 py-0.5 rounded border focus:outline-none cursor-pointer transition-colors ${currentSchedTheme.input}`}
                  title={lang === 'en' ? 'Choose from 10 popular schedule titles' : '자주 사용하는 10개 스케줄 제목 중 선택'}
                >
                  <option value="" disabled>
                    {lang === 'en' ? '📋 Popular Titles (10)...' : '📋 자주 쓰는 제목 (10개)...'}
                  </option>
                  {POPULAR_SCHEDULE_TITLES.map((t, idx) => (
                    <option key={idx} value={lang === 'en' ? t.en : t.ko}>
                      {idx + 1}. {lang === 'en' ? t.en : t.ko}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <input
              type="text"
              id="input-sched-label"
              list="sched-title-presets"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder={lang === 'en' ? 'e.g. Midnight Auto Shutdown' : '예: 심야 PC 자동 종료'}
              maxLength={60}
              className={`w-full text-xs px-2.5 py-1.5 rounded-md border focus:outline-none focus:ring-1 ${currentSchedTheme.input}`}
            />
            <datalist id="sched-title-presets">
              {POPULAR_SCHEDULE_TITLES.map((t, idx) => (
                <option key={idx} value={lang === 'en' ? t.en : t.ko} />
              ))}
            </datalist>
          </div>

          {/* Type Picker Tabs */}
          <div>
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
              {lang === 'en' ? 'Repeat Frequency Type' : '반복 플랜 타입'}
            </label>
            <div className="grid grid-cols-4 gap-1 text-[10px] text-center font-semibold">
              {[
                { id: 'once', label: lang === 'en' ? 'Once' : '한 번' },
                { id: 'daily', label: lang === 'en' ? 'Daily' : '매일' },
                { id: 'weekly', label: lang === 'en' ? 'Weekly' : '매주 요일' },
                { id: 'interval', label: lang === 'en' ? 'Interval' : '동작주기' }
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setType(t.id as ScheduleType)}
                  className={`py-1.5 rounded-md border cursor-pointer ${
                    type === t.id
                      ? 'bg-blue-600 border-blue-600 text-white font-bold'
                      : `${theme === 'beige' ? 'bg-[#ebe2d4] border-[#dfd5c6] text-[#4a3e2b]' : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-gray-500 hover:text-gray-200'}`
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Conditional inputs */}
          {type !== 'interval' ? (
            <div className="bg-white/40 dark:bg-black/20 p-2.5 rounded-lg border border-gray-200/50 dark:border-gray-800/40">
              <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
                {lang === 'en' ? 'Trigger Time (24 Hour Format)' : '정밀 알람 격발 시각 (24시)'}
              </label>
              <div className="flex items-center gap-2">
                <select
                  value={timeH}
                  onChange={(e) => setTimeH(e.target.value)}
                  className={`text-xs rounded-md p-1 font-mono w-16 focus:outline-none ${currentSchedTheme.input}`}
                >
                  {Array.from({ length: 24 }).map((_, i) => {
                    const ts = i.toString().padStart(2, '0');
                    return <option key={ts} value={ts}>{ts}{lang === 'en' ? 'h' : '시'}</option>;
                  })}
                </select>
                <span className="text-gray-400 font-bold">:</span>
                <select
                  value={timeM}
                  onChange={(e) => setTimeM(e.target.value)}
                  className={`text-xs rounded-md p-1 font-mono w-16 focus:outline-none ${currentSchedTheme.input}`}
                >
                  {Array.from({ length: 60 }).map((_, i) => {
                    const ts = i.toString().padStart(2, '0');
                    return <option key={ts} value={ts}>{ts}{lang === 'en' ? 'm' : '분'}</option>;
                  })}
                </select>
              </div>

              {type === 'weekly' && (
                <div className="mt-2.5">
                  <label className="block text-[9px] uppercase font-bold text-gray-400 mb-1">
                    {lang === 'en' ? 'Setup Weekly Days' : '경로 요일 설정'}
                  </label>
                  <div className="flex items-center justify-between gap-1">
                    {(lang === 'en' 
                      ? ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
                      : ['일', '월', '화', '수', '목', '금', '토']
                    ).map((nm, idx) => {
                      const active = selectedDays.includes(idx);
                      return (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => toggleDaySelection(idx)}
                          className={`flex-1 py-1 rounded-md text-[10px] border font-bold cursor-pointer transition-all ${
                            active
                              ? 'bg-blue-500/20 border-blue-500/60 text-blue-500 text-xs'
                              : `${theme === 'beige' ? 'bg-[#ebe2d4] border-[#dfd5c6] text-[#4a3e2b]' : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-805 text-gray-400 hover:text-gray-200'}`
                          }`}
                        >
                          {nm}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white/40 dark:bg-black/20 p-2.5 rounded-lg border border-gray-200/50 dark:border-gray-800/40">
              <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
                {lang === 'en' ? 'Loop Interval Sequence (Minutes)' : '작동 발생 주기 지연 (분 단위)'}
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={1}
                  value={intervalMins}
                  onChange={(e) => setIntervalMins(Math.max(1, parseInt(e.target.value) || 30))}
                  className={`text-xs rounded-md p-1 font-mono w-20 text-center font-bold focus:outline-none ${currentSchedTheme.input}`}
                />
                <span className="text-xs text-gray-400 font-medium">
                  {lang === 'en' ? 'mins interval loop' : '분 간격마다 순환 가동'}
                </span>
              </div>
            </div>
          )}

          {/* Action power state */}
          <div>
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
              {lang === 'en' ? 'Task Power Action' : '배치 시그널 전원 행동'}
            </label>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 text-[10px] font-semibold text-center">
              {[
                { id: 'shutdown' as PowerMode, label: lang === 'en' ? 'Shutdown' : '종료' },
                { id: 'restart' as PowerMode, label: lang === 'en' ? 'Reboot' : '재시동' },
                { id: 'sleep' as PowerMode, label: lang === 'en' ? 'Sleep' : '절전' },
                { id: 'screenoff' as PowerMode, label: lang === 'en' ? 'Screen O' : '화면끄기' },
                { id: 'logout' as PowerMode, label: lang === 'en' ? 'Log Out' : '로그아웃' },
                { id: 'alarm' as PowerMode, label: lang === 'en' ? 'Alarm' : '알람' }
              ].map((m) => {
                const active = mode === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setMode(m.id)}
                    className={`py-1.5 rounded-md border cursor-pointer ${
                      active
                        ? 'bg-indigo-600 border-indigo-600 text-white font-bold'
                        : `${theme === 'beige' ? 'bg-[#ebe2d4] border-[#dfd5c6] text-[#4a3e2b]' : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-gray-500 hover:text-gray-200'}`
                    }`}
                  >
                    {m.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Flags Toggles */}
          <div className="bg-white/40 dark:bg-black/20 p-2.5 rounded-lg border border-gray-200/50 dark:border-gray-800/40 space-y-2 text-[11px] font-medium text-gray-600 dark:text-gray-300">
            <div className="flex items-center justify-between cursor-pointer text-left" onClick={() => setForceCloseApps(!forceCloseApps)}>
              <span>
                {lang === 'en' ? 'Force close active background apps (/f)' : '구동 중인 파일/프로그램 강제 종료 (/f)'}
              </span>
              {forceCloseApps ? (
                <CheckSquare className="w-4.5 h-4.5 text-blue-500" />
              ) : (
                <Square className="w-4.5 h-4.5 text-gray-400" />
              )}
            </div>

            <div className="flex items-center justify-between cursor-pointer text-left" onClick={() => setWarningNotification(!warningNotification)}>
              <span>
                {lang === 'en' ? 'Sound alarm warnings 1 minute before action' : '종료 예정 1분 전 비프 경고 가동'}
              </span>
              {warningNotification ? (
                <CheckSquare className="w-4.5 h-4.5 text-blue-500" />
              ) : (
                <Square className="w-4.5 h-4.5 text-gray-400" />
              )}
            </div>
          </div>

          {errorMsg && (
            <p className="text-[10px] text-rose-500 font-mono font-medium flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errorMsg}
            </p>
          )}

          {editingRuleId ? (
            <div className="flex gap-2">
              <button
                type="submit"
                id="btn-submit-schedule"
                className="flex-1 text-xs font-bold py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-md transition-all shadow-md active:scale-95 cursor-pointer"
              >
                {lang === 'en' ? 'Save Changes' : '스케줄 규칙 수정 반영하기'}
              </button>
              <button
                type="button"
                id="btn-cancel-edit-schedule"
                onClick={resetForm}
                className="text-xs font-bold py-2 px-4.5 bg-gray-500 hover:bg-gray-600 text-white rounded-md transition-all active:scale-95 cursor-pointer"
              >
                {lang === 'en' ? 'Cancel' : '취소'}
              </button>
            </div>
          ) : (
            <button
              type="submit"
              id="btn-submit-schedule"
              className="w-full text-xs font-semibold py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-md transition-all shadow-md active:scale-95 cursor-pointer"
            >
              {lang === 'en' ? 'Add Rule to Active Schedules' : '스케줄 규칙 등록 및 감시 엔진에 합류'}
            </button>
          )}
        </form>
      )}

      {/* Rules list */}
      <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1 style-scrollbar flex-1">
        {rules.length === 0 ? (
          <div className="text-center py-10 text-xs text-gray-450 border-2 border-dashed border-gray-100/10 rounded-xl">
            {lang === 'en' ? 'No active schedules configured. Start by creating a rule above!' : '활성화된 스케줄이 없습니다. 원격 자동 제어를 구축해보세요!'}
          </div>
        ) : (
          rules.map((rule) => {
            const isThemeActive = rule.isActive;
            const modeStyle = getPowerModeColor(rule.mode);
            const modeLabel = getPowerModeLabel(rule.mode);

            return (
              <div
                key={rule.id}
                id={`rule-item-${rule.id}`}
                className={`relative p-3.5 rounded-xl border transition-all duration-300 ${currentSchedTheme.card} ${
                  isThemeActive
                    ? 'opacity-100 hover:border-blue-400'
                    : 'opacity-65'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-1 text-left">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className={`text-[10px] border px-1.5 py-0.5 rounded-md font-bold font-sans ${currentSchedTheme.badge}`}>
                        {getScheduleTypeLabel(rule.type)}
                      </span>
                      
                      <span className={`text-[10px] border px-1.5 py-0.5 rounded-md font-bold flex items-center gap-1 ${modeStyle}`}>
                        {getPowerModeIcon(rule.mode)}
                        {modeLabel}
                      </span>
                    </div>
 
                    <h4 className={`text-xs font-extrabold mt-1 uppercase tracking-tight line-clamp-1 ${theme === 'beige' ? 'text-[#4a3e2b]' : 'text-gray-100'}`}>
                      {rule.label}
                    </h4>
 
                    {/* Meta info details */}
                    <div className={`text-[10.5px] font-sans space-y-0.5 leading-snug ${currentSchedTheme.cardSubtext}`}>
                      {rule.type !== 'interval' && (
                        <p className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-blue-500 font-bold" />
                          <span>{lang === 'en' ? 'Trigger time: ' : '기동 시간: '}<strong className={`${theme === 'beige' ? 'text-[#4a3e2b]' : 'text-gray-300'}`}>{rule.time}</strong></span>
                        </p>
                      )}
                      
                      {rule.type === 'weekly' && (
                        <p>{lang === 'en' ? 'Weekdays: ' : '요일: '}<strong className={`${theme === 'beige' ? 'text-[#4a3e2b]' : 'text-gray-300'}`}>{getDaysLabel(rule.days)}</strong></p>
                      )}
                      
                      {rule.type === 'interval' && (
                        <p className="flex items-center gap-1">
                          <Timer className="w-3 h-3 text-purple-500 font-semibold" />
                          <span>{lang === 'en' ? 'Loop interval: ' : '순환 주기: '}<strong className={`${theme === 'beige' ? 'text-[#4a3e2b]' : 'text-gray-300'}`}>{lang === 'en' ? `Every ${rule.intervalMinutes} mins` : `매 ${rule.intervalMinutes}분 마다`}</strong></span>
                        </p>
                      )}

                      {/* Display warning/f badges */}
                      <div className="flex items-center gap-2 text-[9px] text-gray-400/80 mt-1 uppercase font-mono">
                        {rule.forceCloseApps && <span className="bg-rose-500/5 px-1 rounded text-red-400 border border-red-950/20">{lang === 'en' ? 'Force Close' : '강제종료(/f)'}</span>}
                        {rule.warningNotification && <span className="bg-yellow-500/5 px-1 rounded text-yellow-500 border border-yellow-950/20">{lang === 'en' ? 'Audio Warning' : '소리경고온'}</span>}
                      </div>
                    </div>
                  </div>

                  {/* Switch and interactive icons on right */}
                  <div className="flex flex-col items-end gap-2.5">
                    {/* Toggle Slide Switch */}
                    <button
                      id={`btn-toggle-sched-on-${rule.id}`}
                      onClick={(e) => toggleRuleActive(rule.id, e)}
                      className={`relative w-8.5 h-5 rounded-full transition-colors cursor-pointer outline-none focus:outline-none ${
                        isThemeActive ? 'bg-blue-500 shadow-sm shadow-blue-500/25' : 'bg-gray-300 dark:bg-gray-805'
                      }`}
                    >
                      <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-md transition-all duration-200 ${
                        isThemeActive ? 'left-4' : 'left-0.5'
                      }`} />
                    </button>

                    {/* Bottom Utility buttons */}
                    <div className="flex items-center gap-1 flex-wrap justify-end">
                      {/* Execute test button */}
                      <button
                        id={`btn-sched-trigger-${rule.id}`}
                        onClick={(e) => handleManualTrigger(rule, e)}
                        className="flex items-center gap-1 px-1.5 py-1 rounded bg-blue-500/10 hover:bg-blue-500/20 text-blue-500 dark:text-blue-400 hover:text-blue-600 border border-blue-500/10 text-[10px] font-bold cursor-pointer transition-colors shadow-sm"
                        title={lang === 'en' ? 'Test rule now' : '예약 조건을 즉시 가상 실행해 봅니다.'}
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>{lang === 'en' ? 'Test' : '테스트'}</span>
                      </button>

                      {/* Edit action button */}
                      <button
                        id={`btn-sched-edit-${rule.id}`}
                        onClick={(e) => handleStartEdit(rule, e)}
                        className="flex items-center gap-1 px-1.5 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 dark:text-amber-400 hover:text-amber-600 border border-amber-500/10 text-[10px] font-bold cursor-pointer transition-colors shadow-sm"
                        title={lang === 'en' ? 'Edit rule parameters' : '예약 설정 편집 수정'}
                      >
                        <Edit2 className="w-3 h-3" />
                        <span>{lang === 'en' ? 'Edit' : '수정'}</span>
                      </button>

                      {/* Trash action button */}
                      <button
                        id={`btn-sched-delete-${rule.id}`}
                        onClick={(e) => handleDeleteRule(rule.id, e)}
                        className="flex items-center gap-1 px-1.5 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 dark:text-rose-400 hover:text-rose-600 border border-rose-500/10 text-[10px] font-bold cursor-pointer transition-colors shadow-sm"
                        title={lang === 'en' ? 'Delete safety rule' : '인덱스 데이터 영구 파기'}
                      >
                        <Trash2 className="w-3 h-3" />
                        <span>{lang === 'en' ? 'Delete' : '삭제'}</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Subfooter: countdown banner */}
                <div className="mt-2.5 pt-2 border-t border-gray-100/10 flex items-center justify-between text-[10px] font-mono leading-none">
                  <div className="flex items-center gap-1 text-gray-400">
                    <History className="w-3 h-3" />
                    <span>{lang === 'en' ? 'Last run: ' : '최종 기동: '}<span className="text-gray-500">{rule.lastExecuted || (lang === 'en' ? 'Never' : '한 번도 실행 없음')}</span></span>
                  </div>

                  <span className={`font-semibold  ${isThemeActive ? 'text-blue-500 dark:text-blue-400 font-semibold animate-pulse' : 'text-gray-400/50'}`}>
                    {getNextOccurrenceString(rule)}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
