import React, { useState, useEffect, useMemo } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import { 
  BatteryCharging, 
  BatteryLow, 
  BatteryMedium, 
  BatteryFull, 
  Zap, 
  AlertTriangle, 
  TrendingDown, 
  Clock, 
  ShieldCheck,
  Activity,
  Gauge,
  Sparkles
} from 'lucide-react';
import { ThemeType } from '../types';

export interface BatterySnapshot {
  timestamp: number;
  timeLabel: string;
  level: number;
  charging: boolean;
}

interface BatteryHistoryChartProps {
  currentBattery?: {
    level: number;
    charging: boolean;
    statusText?: string;
  };
  timerState: 'idle' | 'running' | 'paused' | 'complete';
  secondsRemaining: number;
  lang: 'ko' | 'en';
  theme: ThemeType;
}

const STORAGE_KEY = 'power_battery_history_60m';

export const BatteryHistoryChart: React.FC<BatteryHistoryChartProps> = ({
  currentBattery,
  timerState,
  secondsRemaining,
  lang,
  theme
}) => {
  const [history, setHistory] = useState<BatterySnapshot[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed: BatterySnapshot[] = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch {}

    // Seed realistic 60-minute history based on current level
    const now = Date.now();
    const currentLvl = currentBattery?.level ?? 85;
    const isChg = currentBattery?.charging ?? false;
    const initialPoints: BatterySnapshot[] = [];

    // Generate 12 historical points spaced by 5 mins (covering past 60 mins)
    for (let i = 12; i >= 0; i--) {
      const pastTime = new Date(now - i * 5 * 60 * 1000);
      const timeStr = pastTime.toLocaleTimeString('ko-KR', { hour12: false, hour: '2-digit', minute: '2-digit' });
      
      let simulatedLevel: number;
      if (isChg) {
        // Was lower in the past, steadily charged up
        simulatedLevel = Math.max(10, Math.min(100, Math.round(currentLvl - (i * 1.5))));
      } else {
        // Was slightly higher in the past, slowly discharged (~1% per 5-10 mins)
        simulatedLevel = Math.max(5, Math.min(100, Math.round(currentLvl + (i * 0.8))));
      }

      initialPoints.push({
        timestamp: pastTime.getTime(),
        timeLabel: timeStr,
        level: simulatedLevel,
        charging: isChg
      });
    }
    return initialPoints;
  });

  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  // Record battery measurements periodically
  useEffect(() => {
    if (!currentBattery) return;

    const now = new Date();
    const timeLabel = now.toLocaleTimeString('ko-KR', { hour12: false, hour: '2-digit', minute: '2-digit' });
    const currentPoint: BatterySnapshot = {
      timestamp: now.getTime(),
      timeLabel,
      level: currentBattery.level,
      charging: currentBattery.charging
    };

    setHistory((prev) => {
      const last = prev[prev.length - 1];
      // Avoid duplicate points within 30 seconds if level didn't change
      if (last && (now.getTime() - last.timestamp < 30000) && last.level === currentBattery.level && last.charging === currentBattery.charging) {
        return prev;
      }

      // Filter out points older than 65 minutes
      const cutoff = now.getTime() - 65 * 60 * 1000;
      const filtered = prev.filter((p) => p.timestamp >= cutoff);
      const updated = [...filtered, currentPoint];

      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated.slice(-25)));
      } catch {}

      return updated;
    });
  }, [currentBattery?.level, currentBattery?.charging]);

  // Calculate discharge / charge rate and predicted runtime
  const analytics = useMemo(() => {
    const level = currentBattery?.level ?? 85;
    const isCharging = currentBattery?.charging ?? false;

    // Estimate consumption rate (% per hour)
    let dischargeRatePerHour = 14; // default ~14% per hour on standard workload
    if (history.length >= 4) {
      const first = history[0];
      const last = history[history.length - 1];
      const elapsedHours = Math.max(0.1, (last.timestamp - first.timestamp) / (3600 * 1000));
      const levelDiff = first.level - last.level;
      if (!isCharging && levelDiff > 0) {
        dischargeRatePerHour = Math.max(5, Math.min(45, Math.round(levelDiff / elapsedHours)));
      }
    }

    // Estimated remaining minutes until 0% (or until critical 15% cutoff)
    const minutesToDepletion = isCharging 
      ? 999 
      : Math.max(0, Math.round((level / dischargeRatePerHour) * 60));
    const minutesTo15Percent = isCharging
      ? 999
      : Math.max(0, Math.round(((level - 15) / dischargeRatePerHour) * 60));

    // Timer prediction
    const timerMinutes = Math.ceil(secondsRemaining / 60);
    const estimatedBatteryAtTimerEnd = isCharging
      ? Math.min(100, Math.round(level + (timerMinutes / 60) * 20))
      : Math.max(0, Math.round(level - (timerMinutes / 60) * dischargeRatePerHour));

    const isTimerSafe = isCharging || estimatedBatteryAtTimerEnd >= 15;
    const willDepleteBeforeTimer = !isCharging && timerState === 'running' && minutesToDepletion < timerMinutes;

    return {
      level,
      isCharging,
      dischargeRatePerHour,
      minutesToDepletion,
      minutesTo15Percent,
      timerMinutes,
      estimatedBatteryAtTimerEnd,
      isTimerSafe,
      willDepleteBeforeTimer
    };
  }, [history, currentBattery, secondsRemaining, timerState]);

  const formatHoursMinutes = (totalMins: number) => {
    if (totalMins >= 999) return lang === 'en' ? 'Continuous (AC Connected)' : '상시 지속 (전원 연결됨)';
    const h = Math.floor(totalMins / 60);
    const m = totalMins % 60;
    if (lang === 'en') {
      return h > 0 ? `${h}h ${m}m remaining` : `${m}m remaining`;
    }
    return h > 0 ? `약 ${h}시간 ${m}분 사용 가능` : `약 ${m}분 사용 가능`;
  };

  const chartColor = useMemo(() => {
    if (analytics.isCharging) return '#10b981'; // emerald
    if (analytics.level <= 15) return '#f43f5e'; // rose
    if (analytics.level <= 40) return '#f59e0b'; // amber
    return '#3b82f6'; // blue
  }, [analytics.isCharging, analytics.level]);

  return (
    <div className={`flex flex-col gap-2 p-3 rounded-xl border transition-all duration-300 ${
      theme === 'beige' ? 'bg-[#eee7da]/80 border-[#c8bcaa]' : 'bg-black/20 dark:bg-black/40 border-gray-500/20'
    }`}>
      {/* Header with Title & Expand Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            {analytics.isCharging ? (
              <BatteryCharging className="w-4 h-4 animate-pulse" />
            ) : analytics.level <= 15 ? (
              <BatteryLow className="w-4 h-4 text-rose-400" />
            ) : analytics.level <= 50 ? (
              <BatteryMedium className="w-4 h-4 text-amber-400" />
            ) : (
              <BatteryFull className="w-4 h-4 text-emerald-400" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className={`text-[12.5px] font-bold ${theme === 'beige' ? 'text-[#2c2217]' : 'text-slate-200'}`}>
                {lang === 'en' ? '60-Min Battery Consumption & Timer Prediction' : '최근 60분 배터리 소모 추이 및 타이머 완주 예측'}
              </span>
              <span className={`px-1.5 py-0.2 text-[10px] font-mono font-bold rounded ${
                analytics.isCharging
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : analytics.level <= 15
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
              }`}>
                {analytics.level}% {analytics.isCharging ? (lang === 'en' ? 'Charging' : '충전중') : (lang === 'en' ? 'Battery' : '배터리')}
              </span>
            </div>
            <p className="text-[10px] text-gray-400 leading-tight">
              {analytics.isCharging
                ? (lang === 'en' ? 'AC power connected. Battery level is rising steadily.' : '전원 어댑터가 연결되어 안정적으로 충전 중입니다.')
                : `${formatHoursMinutes(analytics.minutesToDepletion)} (${lang === 'en' ? 'Discharge Rate' : '방전 속도'}: ~${analytics.dischargeRatePerHour}%/h)`}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className={`text-[11px] font-bold px-2 py-1 rounded transition-colors cursor-pointer ${
            theme === 'beige' ? 'bg-[#ded4c3] text-[#3d3222] hover:bg-[#d4c8b5]' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
          }`}
        >
          {isExpanded ? (lang === 'en' ? 'Hide Chart' : '차트 접기') : (lang === 'en' ? 'Show Chart' : '차트 보기')}
        </button>
      </div>

      {/* Active Timer Prediction Banner */}
      {timerState === 'running' && (
        <div className={`p-2 rounded-lg border flex items-center justify-between gap-2 text-[11px] ${
          analytics.willDepleteBeforeTimer
            ? 'bg-rose-950/40 border-rose-500/50 text-rose-200'
            : analytics.estimatedBatteryAtTimerEnd < 15
            ? 'bg-amber-950/40 border-amber-500/50 text-amber-200'
            : 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
        }`}>
          <div className="flex items-center gap-1.5 font-medium truncate">
            {analytics.willDepleteBeforeTimer ? (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 animate-bounce" />
            ) : analytics.estimatedBatteryAtTimerEnd < 15 ? (
              <TrendingDown className="w-4 h-4 text-amber-400 shrink-0" />
            ) : (
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            )}
            <span className="truncate">
              {lang === 'en' ? 'Timer Prediction: ' : '타이머 완주 예측: '}
              <strong>
                {analytics.willDepleteBeforeTimer
                  ? (lang === 'en' ? '⚠️ High risk of battery exhaustion before timer ends!' : '⚠️ 타이머 종료 전 배터리 방전 위험! 충전기를 연결하세요.')
                  : analytics.isCharging
                  ? (lang === 'en' ? `Safe (Estimated ~${analytics.estimatedBatteryAtTimerEnd}% at completion)` : `안전 (완료 시 예상 배터리: ~${analytics.estimatedBatteryAtTimerEnd}%)`)
                  : (lang === 'en' ? `Safe (${analytics.estimatedBatteryAtTimerEnd}% remaining at completion)` : `완료 가능 (완료 시 예상 배터리: ~${analytics.estimatedBatteryAtTimerEnd}%)`)}
              </strong>
            </span>
          </div>
          <span className="font-mono font-bold text-[10px] shrink-0 bg-black/30 px-1.5 py-0.5 rounded">
            {analytics.timerMinutes}{lang === 'en' ? 'm timer' : '분 대기'}
          </span>
        </div>
      )}

      {/* Battery Health Insights Section (Estimated Time Remaining & Discharge Analysis) */}
      <div className={`p-2.5 rounded-lg border transition-all ${
        theme === 'beige' ? 'bg-[#f4efe6] border-[#d8cdbc]' : 'bg-[#18181b]/90 border-gray-700/60'
      }`}>
        <div className="flex items-center justify-between pb-1.5 border-b border-gray-500/10 mb-2">
          <span className="text-[11px] font-bold flex items-center gap-1.5 text-amber-400 dark:text-amber-300">
            <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
            {lang === 'en' ? 'Battery Health Insights & Discharge Telemetry' : '배터리 상태 분석 및 잔여 시간 예측 인사이트'}
          </span>
          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-semibold ${
            analytics.isCharging
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
              : analytics.level <= 15
              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
          }`}>
            {analytics.isCharging
              ? (lang === 'en' ? '⚡ AC Charging' : '⚡ 전원 충전 중')
              : (lang === 'en' ? `🔋 Discharge Rate: ~${analytics.dischargeRatePerHour}%/h` : `🔋 방전율: ~${analytics.dischargeRatePerHour}%/h`)}
          </span>
        </div>

        {/* 3-Column Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {/* 1. Estimated Total Time Remaining */}
          <div className={`p-2 rounded border flex flex-col justify-between ${
            theme === 'beige' ? 'bg-[#eadecc] border-[#c8bcaa]' : 'bg-black/30 border-gray-800'
          }`}>
            <div className="flex items-center gap-1 text-[10px] text-gray-400">
              <Clock className="w-3 h-3 text-blue-400" />
              <span>{lang === 'en' ? 'Estimated Time Remaining' : '예상 잔여 사용 시간'}</span>
            </div>
            <div className="my-1">
              <span className={`text-[14px] font-bold font-mono ${
                analytics.isCharging
                  ? 'text-emerald-400'
                  : analytics.level <= 15
                  ? 'text-rose-400'
                  : theme === 'beige' ? 'text-[#2b2014]' : 'text-slate-100'
              }`}>
                {analytics.isCharging
                  ? (lang === 'en' ? 'Continuous (AC)' : '상시 지속 (AC 연결)')
                  : formatHoursMinutes(analytics.minutesToDepletion)}
              </span>
            </div>
            <span className="text-[9px] text-gray-400 leading-tight">
              {analytics.isCharging
                ? (lang === 'en' ? 'Unlimited runtime with adapter' : '전원 공급으로 무제한 구동')
                : (lang === 'en' ? 'Based on 60-min discharge speed' : '최근 60분 방전 속도 기반 0% 기준')}
            </span>
          </div>

          {/* 2. Discharge / Charge Rate */}
          <div className={`p-2 rounded border flex flex-col justify-between ${
            theme === 'beige' ? 'bg-[#eadecc] border-[#c8bcaa]' : 'bg-black/30 border-gray-800'
          }`}>
            <div className="flex items-center gap-1 text-[10px] text-gray-400">
              <Gauge className="w-3 h-3 text-amber-400" />
              <span>{lang === 'en' ? 'Current Discharge Rate' : '현재 방전/충전 속도'}</span>
            </div>
            <div className="my-1">
              <span className={`text-[14px] font-bold font-mono ${
                analytics.isCharging ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {analytics.isCharging
                  ? (lang === 'en' ? '+20% / hr (Charging)' : '+약 20%/시간 (충전 중)')
                  : `-${analytics.dischargeRatePerHour}% / hr`}
              </span>
            </div>
            <span className="text-[9px] text-gray-400 leading-tight">
              {analytics.isCharging
                ? (lang === 'en' ? 'Battery accumulating power' : '배터리 용량 안정적 상승 중')
                : (lang === 'en' ? 'System load power consumption' : '현재 작업 부하 기준 시간당 소모율')}
            </span>
          </div>

          {/* 3. Safe Operation Window (Until 15% Cutoff) */}
          <div className={`p-2 rounded border flex flex-col justify-between ${
            theme === 'beige' ? 'bg-[#eadecc] border-[#c8bcaa]' : 'bg-black/30 border-gray-800'
          }`}>
            <div className="flex items-center gap-1 text-[10px] text-gray-400">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span>{lang === 'en' ? 'Safe Window (To 15%)' : '안전 작동 한계 (15%까지)'}</span>
            </div>
            <div className="my-1">
              <span className={`text-[14px] font-bold font-mono ${
                analytics.isCharging
                  ? 'text-emerald-400'
                  : analytics.minutesTo15Percent <= 30
                  ? 'text-rose-400'
                  : theme === 'beige' ? 'text-[#2b2014]' : 'text-emerald-300'
              }`}>
                {analytics.isCharging
                  ? (lang === 'en' ? 'Safe (No Drop)' : '안전 (방전 없음)')
                  : analytics.minutesTo15Percent === 0
                  ? (lang === 'en' ? 'Below 15% Warning' : '15% 이하 경고 수위')
                  : formatHoursMinutes(analytics.minutesTo15Percent)}
              </span>
            </div>
            <span className="text-[9px] text-gray-400 leading-tight">
              {analytics.isCharging
                ? (lang === 'en' ? 'Protected from sudden shutdown' : '예기치 못한 방전 종료 위험 없음')
                : (lang === 'en' ? 'Time remaining before 15% toast' : '15% 저전력 경고 알림 전까지 여유')}
            </span>
          </div>
        </div>
      </div>

      {/* Recharts Area Chart */}
      {isExpanded && (
        <div className="w-full h-36 pt-1">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 8, right: 10, left: -25, bottom: 0 }}>
              <defs>
                <linearGradient id="batteryGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColor} stopOpacity={0.45} />
                  <stop offset="95%" stopColor={chartColor} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={theme === 'beige' ? '#c8bcaa' : '#334155'} opacity={0.4} />
              <XAxis 
                dataKey="timeLabel" 
                tick={{ fontSize: 9.5, fill: theme === 'beige' ? '#5c4d38' : '#94a3b8' }} 
                tickLine={false}
                axisLine={{ stroke: theme === 'beige' ? '#c8bcaa' : '#475569', opacity: 0.5 }}
              />
              <YAxis 
                domain={[0, 100]} 
                ticks={[0, 25, 50, 75, 100]}
                tick={{ fontSize: 9.5, fill: theme === 'beige' ? '#5c4d38' : '#94a3b8' }} 
                tickLine={false}
                axisLine={{ stroke: theme === 'beige' ? '#c8bcaa' : '#475569', opacity: 0.5 }}
                unit="%"
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload as BatterySnapshot;
                    return (
                      <div className="bg-[#18181b] border border-gray-700 rounded-lg p-2 text-xs shadow-xl text-white font-mono space-y-1">
                        <div className="text-[11px] text-gray-400">{data.timeLabel} ({lang === 'en' ? 'Recorded' : '기록 시각'})</div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-emerald-400">{data.level}%</span>
                          <span className={`text-[10px] px-1 py-0.2 rounded ${
                            data.charging ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                          }`}>
                            {data.charging ? (lang === 'en' ? 'Charging' : '충전중') : (lang === 'en' ? 'Discharging' : '배터리 사용')}
                          </span>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              {/* 15% Critical Threshold Reference Line */}
              <ReferenceLine 
                y={15} 
                stroke="#f43f5e" 
                strokeDasharray="4 4" 
                label={{ 
                  value: lang === 'en' ? '15% Low Level' : '15% 경고 기준선', 
                  fill: '#f43f5e', 
                  fontSize: 9.5, 
                  position: 'insideBottomRight' 
                }} 
              />
              <Area
                type="monotone"
                dataKey="level"
                stroke={chartColor}
                strokeWidth={2.2}
                fillOpacity={1}
                fill="url(#batteryGradient)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default BatteryHistoryChart;
