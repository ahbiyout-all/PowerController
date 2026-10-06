import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Lightbulb, 
  Clock, 
  Moon, 
  Power, 
  RotateCw, 
  Laptop, 
  Zap, 
  CheckCircle, 
  ArrowRight,
  ShieldCheck,
  Flame,
  Coffee,
  X
} from 'lucide-react';
import { PowerMode, ThemeType } from '../types';

export interface RecommendationPreset {
  id: string;
  category: 'efficiency' | 'health' | 'security' | 'night';
  titleKo: string;
  titleEn: string;
  descKo: string;
  descEn: string;
  mode: PowerMode;
  targetType: 'timer' | 'schedule';
  defaultMinutes?: number;
  defaultTime?: string; // HH:MM
  icon: any;
  badgeKo: string;
  badgeEn: string;
  highlight?: boolean;
}

interface SmartAdvisorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyRecommendation: (rec: RecommendationPreset) => void;
  lang?: 'ko' | 'en';
  theme?: ThemeType;
}

const recommendations: RecommendationPreset[] = [
  {
    id: 'rec-movie',
    category: 'night',
    titleKo: '영화 / OTT 감상 후 자동 종료 (2시간)',
    titleEn: 'Movie & Netflix Auto Shutdown (2 Hours)',
    descKo: '영화나 드라마 시청 중 잠들어도 2시간 후 PC가 알아서 전원을 완전 차단하여 불필요한 전기 소모를 막습니다.',
    descEn: 'Automatically shuts down your computer 2 hours later so you can watch movies in bed without worrying.',
    mode: 'shutdown',
    targetType: 'timer',
    defaultMinutes: 120,
    icon: Moon,
    badgeKo: '인기 1위',
    badgeEn: 'Top Pick',
    highlight: true
  },
  {
    id: 'rec-lunch',
    category: 'efficiency',
    titleKo: '점심시간 쾌속 메모리 청소 재시작 (1시간 후)',
    titleEn: 'Lunch Break Memory Flush Restart (1 Hour)',
    descKo: '점심시간 동안 시스템 메모리 누수를 깔끔하게 해소하고 최적 상태로 리부트합니다.',
    descEn: 'Reboots your PC during lunch break to flush RAM cache and boost peak afternoon performance.',
    mode: 'restart',
    targetType: 'timer',
    defaultMinutes: 60,
    icon: RotateCw,
    badgeKo: '성능 최적화',
    badgeEn: 'Performance'
  },
  {
    id: 'rec-bedtime',
    category: 'night',
    titleKo: '심야 취침 예약 자동 절전 (밤 11:30)',
    titleEn: 'Night Bedtime Auto Sleep (11:30 PM)',
    descKo: '매일 밤 취침 시각에 맞춰 조용히 절전 모드로 전환하여 작업 상태를 유지한 채 대기 전력을 절감합니다.',
    descEn: 'Switches computer to Sleep mode every night at 11:30 PM to save electricity while keeping apps intact.',
    mode: 'sleep',
    targetType: 'schedule',
    defaultTime: '23:30',
    icon: Sparkles,
    badgeKo: '전력 절감',
    badgeEn: 'Energy Saver'
  },
  {
    id: 'rec-workend',
    category: 'security',
    titleKo: '퇴근 정시 시스템 완전 소각 종료 (오후 6:00)',
    titleEn: 'Workday End Auto Shutdown (6:00 PM)',
    descKo: '퇴근 시간에 자동으로 실행 중인 모든 앱을 안전하게 종료하고 보안을 강화합니다.',
    descEn: 'Schedules complete system shutdown at 6:00 PM to ensure corporate PC security after hours.',
    mode: 'shutdown',
    targetType: 'schedule',
    defaultTime: '18:00',
    icon: ShieldCheck,
    badgeKo: '보안 권장',
    badgeEn: 'Security'
  },
  {
    id: 'rec-meeting',
    category: 'efficiency',
    titleKo: '회의 및 미팅 시 즉시 모니터 절전 (15분 후)',
    titleEn: 'Meeting Screen Off Mode (15 Mins)',
    descKo: '자리를 비우거나 회의실로 이동할 때 15분 후 모니터 화면만 꺼서 OLED 번인과 전력 낭비를 방지합니다.',
    descEn: 'Turns off monitor displays after 15 minutes of inactivity to protect displays and preserve privacy.',
    mode: 'screenoff',
    targetType: 'timer',
    defaultMinutes: 15,
    icon: Laptop,
    badgeKo: '디스플레이 보호',
    badgeEn: 'Display Saver'
  },
  {
    id: 'rec-pomodoro',
    category: 'health',
    titleKo: '집중 근무 50분 휴식 알람 타이머',
    titleEn: '50-Min Focus Work Break Alarm',
    descKo: '50분 집중 작업 후 휴식 알람을 울려 눈의 피로를 풀고 바른 자세 스트레칭을 돕습니다.',
    descEn: 'Triggers a notification alarm every 50 minutes to remind you to stretch and take eye breaks.',
    mode: 'alarm',
    targetType: 'timer',
    defaultMinutes: 50,
    icon: Coffee,
    badgeKo: '건강 케어',
    badgeEn: 'Health'
  }
];

const modalThemeStyles = {
  dark: {
    overlay: 'bg-black/75 backdrop-blur-sm',
    box: 'bg-[#181a24] border-[#2d3142] text-white shadow-2xl',
    header: 'border-b border-[#2d3142]/80 bg-[#14161f]',
    subtext: 'text-gray-400',
    card: 'bg-[#1e2230] border-[#2d3142] hover:border-blue-500/80 text-white',
    cardActive: 'bg-blue-950/40 border-blue-500/80 ring-1 ring-blue-500/50',
    cardDesc: 'text-gray-400',
    badge: 'bg-gray-800 border-gray-700 text-gray-300',
    applyBtn: 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30',
    tabActive: 'bg-blue-600 text-white',
    tabInactive: 'bg-gray-800/80 text-gray-400 hover:bg-gray-700'
  },
  gray: {
    overlay: 'bg-black/70 backdrop-blur-sm',
    box: 'bg-[#242f41] border-[#475569] text-[#f1f5f9] shadow-2xl',
    header: 'border-b border-[#475569]/80 bg-[#1e293b]',
    subtext: 'text-slate-300',
    card: 'bg-[#1e293b] border-[#475569]/70 hover:border-blue-400 text-[#f1f5f9]',
    cardActive: 'bg-blue-900/30 border-blue-400 ring-1 ring-blue-400/50',
    cardDesc: 'text-slate-300',
    badge: 'bg-[#475569] border-[#475569] text-slate-200',
    applyBtn: 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30',
    tabActive: 'bg-blue-600 text-white',
    tabInactive: 'bg-[#1e293b] text-slate-300 hover:bg-[#334155]'
  },
  beige: {
    overlay: 'bg-black/50 backdrop-blur-sm',
    box: 'bg-[#faf6ee] border-[#dfd5c6] text-[#4a3e2b] shadow-2xl',
    header: 'border-b border-[#dfd5c6] bg-[#ebe2d4]',
    subtext: 'text-[#6e5d47]',
    card: 'bg-white border-[#dfd5c6] hover:border-[#8c785c] text-[#4a3e2b]',
    cardActive: 'bg-[#faf3e8] border-[#8c785c] ring-1 ring-[#8c785c]/50',
    cardDesc: 'text-[#6e5d47]',
    badge: 'bg-[#ebe2d4] border-[#dfd5c6] text-[#8c785c]',
    applyBtn: 'bg-[#8c785c] hover:bg-[#7a684e] text-white shadow-md',
    tabActive: 'bg-[#8c785c] text-white',
    tabInactive: 'bg-[#ebe2d4] text-[#6e5d47] hover:bg-[#dfd5c6]'
  }
};

export default function SmartAdvisorModal({
  isOpen,
  onClose,
  onApplyRecommendation,
  lang = 'ko',
  theme = 'dark'
}: SmartAdvisorModalProps) {
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'night' | 'efficiency' | 'health' | 'security'>('all');
  const [appliedId, setAppliedId] = useState<string | null>(null);

  const t = modalThemeStyles[theme] || modalThemeStyles.dark;

  if (!isOpen) return null;

  const filteredRecs = recommendations.filter(
    r => selectedCategory === 'all' || r.category === selectedCategory
  );

  const handleApply = (rec: RecommendationPreset) => {
    setAppliedId(rec.id);
    onApplyRecommendation(rec);
    setTimeout(() => {
      setAppliedId(null);
      onClose();
    }, 450);
  };

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 ${t.overlay}`}>
      <div 
        className={`w-full max-w-lg rounded-2xl border flex flex-col max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200 ${t.box}`}
      >
        {/* Header */}
        <div className={`p-4 flex items-center justify-between select-none ${t.header}`}>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Lightbulb className="w-5 h-5 text-amber-400 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold tracking-tight">
                  {lang === 'en' ? 'Smart Power Advisor' : '스마트 전원 추천 어드바이저'}
                </h3>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-500 border border-amber-500/30">
                  {lang === 'en' ? 'AI Auto Recommend' : '상황별 맞춤 추천'}
                </span>
              </div>
              <p className={`text-xs mt-0.5 ${t.subtext}`}>
                {lang === 'en' 
                  ? 'Select a smart preset to apply optimal power schedule or timer instantly.'
                  : '생활 패턴과 PC 사용 목적에 최적화된 추천 전원 시나리오를 원클릭으로 즉시 적용합니다.'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-black/10 dark:hover:bg-white/10 transition-colors text-gray-400 hover:text-gray-200 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Category Tabs */}
        <div className="px-4 py-2 border-b border-gray-500/10 flex items-center gap-1.5 overflow-x-auto no-scrollbar select-none text-xs">
          {[
            { id: 'all', labelKo: '전체 추천', labelEn: 'All Scenarios' },
            { id: 'night', labelKo: '🌙 야간/취침', labelEn: '🌙 Bedtime' },
            { id: 'efficiency', labelKo: '⚡ 성능/절전', labelEn: '⚡ Efficiency' },
            { id: 'security', labelKo: '🛡️ 퇴근/보안', labelEn: '🛡️ Security' },
            { id: 'health', labelKo: '☕ 건강/휴식', labelEn: '☕ Health' }
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id as any)}
              className={`px-2.5 py-1 rounded-full font-bold text-[11.5px] transition-all cursor-pointer shrink-0 ${
                selectedCategory === cat.id ? t.tabActive : t.tabInactive
              }`}
            >
              {lang === 'en' ? cat.labelEn : cat.labelKo}
            </button>
          ))}
        </div>

        {/* Recommendation Cards List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5 [scrollbar-width:thin]">
          {filteredRecs.map((rec) => {
            const IconComponent = rec.icon;
            const isApplied = appliedId === rec.id;

            return (
              <div
                key={rec.id}
                className={`p-3.5 rounded-xl border transition-all duration-200 flex flex-col gap-2.5 ${t.card} ${
                  rec.highlight ? 'ring-1 ring-amber-500/30' : ''
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-black/10 dark:bg-white/10 flex items-center justify-center shrink-0 mt-0.5">
                      <IconComponent className="w-4 h-4 text-amber-500" />
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <h4 className="text-xs font-bold leading-tight">
                          {lang === 'en' ? rec.titleEn : rec.titleKo}
                        </h4>
                        <span className={`text-[9.5px] px-1.5 py-0.5 rounded font-semibold border ${t.badge}`}>
                          {lang === 'en' ? rec.badgeEn : rec.badgeKo}
                        </span>
                      </div>
                      <p className={`text-[11px] mt-1 leading-relaxed ${t.cardDesc}`}>
                        {lang === 'en' ? rec.descEn : rec.descKo}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1 border-t border-gray-500/10 text-xs">
                  <div className="flex items-center gap-2 font-mono text-[11px]">
                    <span className="px-1.5 py-0.5 rounded bg-black/15 dark:bg-white/10 font-semibold text-blue-500 dark:text-blue-400">
                      {rec.targetType === 'timer' 
                        ? (lang === 'en' ? `⏳ Delay: ${rec.defaultMinutes}m` : `⏳ 지연: ${rec.defaultMinutes}분`)
                        : (lang === 'en' ? `⏰ Schedule: ${rec.defaultTime}` : `⏰ 예약: ${rec.defaultTime}`)}
                    </span>
                    <span className="text-gray-400 font-sans">
                      {rec.mode === 'shutdown' && (lang === 'en' ? '🔴 Shutdown' : '🔴 시스템 종료')}
                      {rec.mode === 'restart' && (lang === 'en' ? '🔵 Restart' : '🔵 재시작')}
                      {rec.mode === 'sleep' && (lang === 'en' ? '🌙 Sleep' : '🌙 절전 모드')}
                      {rec.mode === 'screenoff' && (lang === 'en' ? '💻 Screen Off' : '💻 화면 끄기')}
                      {rec.mode === 'alarm' && (lang === 'en' ? '⏰ Alarm' : '⏰ 알람')}
                    </span>
                  </div>

                  <button
                    onClick={() => handleApply(rec)}
                    disabled={isApplied}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${t.applyBtn}`}
                  >
                    {isApplied ? (
                      <>
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-300" />
                        <span>{lang === 'en' ? 'Applied!' : '적용 완료!'}</span>
                      </>
                    ) : (
                      <>
                        <Zap className="w-3.5 h-3.5" />
                        <span>{lang === 'en' ? 'Apply Now' : '즉시 적용'}</span>
                        <ArrowRight className="w-3 h-3" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className={`p-3 px-4 border-t border-gray-500/10 flex items-center justify-between text-xs select-none ${t.header}`}>
          <span className={`text-[11px] ${t.subtext}`}>
            💡 {lang === 'en' ? 'Presets automatically configure timer and start trigger.' : '선택하신 추천 시나리오에 맞춰 즉시 타이머 입력창에 세팅됩니다.'}
          </span>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded bg-black/10 dark:bg-white/10 hover:bg-black/20 text-xs font-semibold cursor-pointer"
          >
            {lang === 'en' ? 'Close' : '닫기'}
          </button>
        </div>
      </div>
    </div>
  );
}
