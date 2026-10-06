import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Play, Pause, RotateCcw, Power, Clock, Maximize2, 
  RotateCw, Moon, Laptop, LogOut, Sliders, Eye, Type,
  ChevronDown, ChevronUp, Sparkles, Terminal, Activity, Layers
} from 'lucide-react';
import { PowerMode, TimerState } from '../types';

export type CompactWidgetDesign = 'standard' | 'cyber_hud' | 'minimal_bar' | 'retro_led' | 'clean_card';

interface CompactWidgetProps {
  lang: 'ko' | 'en';
  widgetDesign: CompactWidgetDesign;
  setWidgetDesign: (design: CompactWidgetDesign) => void;
  widgetWidth: number;
  setWidgetWidth: (w: number) => void;
  clockFontSize: number;
  setClockFontSize: (s: number) => void;
  timerFontSize: number;
  setTimerFontSize: (s: number) => void;
  widgetOpacity: number;
  handleWidgetOpacityChange: (op: number) => void;
  showCurrentTimeCompact: boolean;
  handleShowCurrentTimeCompactChange: (show: boolean) => void;
  selectedFont: string;
  handleFontChange: (font: string) => void;
  powerMode: PowerMode;
  handleModeChange: (mode: PowerMode) => void;
  timerState: TimerState;
  secondsRemaining: number;
  totalSeconds: number;
  inputH: number;
  inputM: number;
  inputS: number;
  setInputH: (h: number) => void;
  setInputM: (m: number) => void;
  setInputS: (s: number) => void;
  handleStartTimer: () => void;
  handlePauseTimer: () => void;
  handleResumeTimer: () => void;
  handleResetTimer: () => void;
  handleTimerComplete: () => void;
  handleQuickPreset: (mins: number) => void;
  toggleAlwaysOnTop: () => void;
  isWarningActive: boolean;
  currentThemeConfig: any;
  formatTimeStr: (s: number) => string;
  getPowerModeKorean: (m: PowerMode) => string;
}

export default function CompactWidget({
  lang,
  widgetDesign,
  setWidgetDesign,
  widgetWidth,
  setWidgetWidth,
  clockFontSize,
  setClockFontSize,
  timerFontSize,
  setTimerFontSize,
  widgetOpacity,
  handleWidgetOpacityChange,
  showCurrentTimeCompact,
  handleShowCurrentTimeCompactChange,
  selectedFont,
  handleFontChange,
  powerMode,
  handleModeChange,
  timerState,
  secondsRemaining,
  totalSeconds,
  inputH,
  inputM,
  inputS,
  setInputH,
  setInputM,
  setInputS,
  handleStartTimer,
  handlePauseTimer,
  handleResumeTimer,
  handleResetTimer,
  handleTimerComplete,
  handleQuickPreset,
  toggleAlwaysOnTop,
  isWarningActive,
  currentThemeConfig,
  formatTimeStr,
  getPowerModeKorean,
}: CompactWidgetProps) {
  const [showConfigDrawer, setShowConfigDrawer] = useState<boolean>(false);

  const currentTimeFormatted = new Date().toLocaleTimeString(lang === 'en' ? 'en-US' : 'ko-KR', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  const getStrokeDashOffset = () => {
    if (totalSeconds === 0) return 0;
    const circumference = 2 * Math.PI * 66;
    const progress = secondsRemaining / totalSeconds;
    return circumference * (1 - progress);
  };

  const actionItems = [
    { id: 'shutdown' as PowerMode, icon: Power, labelKo: '종료', labelEn: 'Shutdown', color: 'rose' },
    { id: 'restart' as PowerMode, icon: RotateCw, labelKo: '재시동', labelEn: 'Restart', color: 'blue' },
    { id: 'sleep' as PowerMode, icon: Moon, labelKo: '절전', labelEn: 'Sleep', color: 'indigo' },
    { id: 'screenoff' as PowerMode, icon: Laptop, labelKo: '화면끔', labelEn: 'Screen Off', color: 'amber' },
    { id: 'logout' as PowerMode, icon: LogOut, labelKo: '로그아웃', labelEn: 'Log Out', color: 'emerald' },
    { id: 'alarm' as PowerMode, icon: Clock, labelKo: '알람', labelEn: 'Alarm', color: 'pink' },
  ];

  const designOptions: { id: CompactWidgetDesign; labelKo: string; labelEn: string; icon: any }[] = [
    { id: 'standard', labelKo: '네온 링', labelEn: 'Neon Ring', icon: Sparkles },
    { id: 'cyber_hud', labelKo: '사이버 HUD', labelEn: 'Cyber HUD', icon: Terminal },
    { id: 'minimal_bar', labelKo: '슬림 바', labelEn: 'Slim Bar', icon: Layers },
    { id: 'retro_led', labelKo: '레트로 LED', labelEn: 'Retro LED', icon: Clock },
    { id: 'clean_card', labelKo: '클린 카드', labelEn: 'Clean Card', icon: Activity },
  ];

  // Drawer for quick size & font customizer
  const renderConfigDrawer = () => (
    <AnimatePresence>
      {showConfigDrawer && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="border-t border-gray-500/15 bg-black/40 p-3 text-[13.5px] space-y-2.5 overflow-hidden"
        >
          {/* Design Style Selector */}
          <div>
            <span className="block font-bold text-gray-400 mb-1">
              🎨 {lang === 'en' ? 'Widget Design' : '창 디자인 스타일'}
            </span>
            <div className="grid grid-cols-5 gap-1">
              {designOptions.map((opt) => {
                const Icon = opt.icon;
                const active = widgetDesign === opt.id;
                return (
                  <button
                    key={opt.id}
                    onClick={() => setWidgetDesign(opt.id)}
                    className={`py-1 rounded text-center font-bold flex flex-col items-center gap-0.5 transition-colors ${
                      active ? 'bg-blue-600 text-white shadow' : 'bg-gray-800/80 hover:bg-gray-700 text-gray-400'
                    }`}
                  >
                    <Icon className="w-3 h-3" />
                    <span className="text-[13.5px] truncate">{lang === 'en' ? opt.labelEn : opt.labelKo}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Window Width Slider */}
          <div>
            <div className="flex items-center justify-between text-gray-400 font-medium mb-1">
              <span>↔️ {lang === 'en' ? 'Window Width' : '상단창 가로 크기'}</span>
              <span className="font-mono text-blue-400 font-bold">{widgetWidth}px</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[13.5px] text-gray-500">260</span>
              <input
                type="range"
                min={260}
                max={440}
                step={10}
                value={widgetWidth}
                onChange={(e) => setWidgetWidth(parseInt(e.target.value, 10))}
                className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <span className="text-[13.5px] text-gray-500">440</span>
            </div>
          </div>

          {/* Clock & Timer Font Size Sliders */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <div className="flex items-center justify-between text-gray-400 font-medium mb-1">
                <span>🕒 {lang === 'en' ? 'Clock Size' : '시계 크기'}</span>
                <span className="font-mono text-blue-400 font-bold">{clockFontSize}px</span>
              </div>
              <input
                type="range"
                min={8}
                max={28}
                step={1}
                value={clockFontSize}
                onChange={(e) => setClockFontSize(parseInt(e.target.value, 10))}
                className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
            <div>
              <div className="flex items-center justify-between text-gray-400 font-medium mb-1">
                <span>⏱️ {lang === 'en' ? 'Timer Size' : '타이머 크기'}</span>
                <span className="font-mono text-blue-400 font-bold">{timerFontSize}px</span>
              </div>
              <input
                type="range"
                min={16}
                max={38}
                step={1}
                value={timerFontSize}
                onChange={(e) => setTimerFontSize(parseInt(e.target.value, 10))}
                className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
          </div>

          {/* Opacity & Current Time Toggle */}
          <div className="flex items-center justify-between pt-1 border-t border-gray-700/50">
            <div className="flex items-center gap-1.5 text-gray-400">
              <Eye className="w-3 h-3 text-blue-400" />
              <span>{widgetOpacity}%</span>
              <input
                type="range"
                min={20}
                max={100}
                step={5}
                value={widgetOpacity}
                onChange={(e) => handleWidgetOpacityChange(parseInt(e.target.value, 10))}
                className="w-16 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            <label className="flex items-center gap-1.5 cursor-pointer text-gray-300">
              <input
                type="checkbox"
                checked={showCurrentTimeCompact}
                onChange={(e) => handleShowCurrentTimeCompactChange(e.target.checked)}
                className="rounded accent-blue-500"
              />
              <span>{lang === 'en' ? 'Show Clock' : '시계 표시'}</span>
            </label>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  // Common Action Controls (Start/Pause/Reset)
  const renderControlButtons = () => (
    <div className="grid grid-cols-2 gap-2">
      {timerState === 'idle' ? (
        <button
          onClick={handleStartTimer}
          className="col-span-2 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-[13.5px] font-bold transition-transform active:scale-95 flex items-center justify-center gap-1.5 shadow-md"
        >
          <Play className="w-3.5 h-3.5 fill-white" />
          {lang === 'en' ? 'Start Timer' : '타이머 가동 시작'}
        </button>
      ) : (
        <>
          {timerState === 'running' ? (
            <button
              onClick={handlePauseTimer}
              className="py-2 bg-amber-500 hover:bg-amber-400 text-white rounded-xl text-[13.5px] font-semibold flex items-center justify-center gap-1 shadow"
            >
              <Pause className="w-3.5 h-3.5" />
              {lang === 'en' ? 'Pause' : '일시정지'}
            </button>
          ) : (
            <button
              onClick={handleResumeTimer}
              className="py-2 bg-green-600 hover:bg-green-500 text-white rounded-xl text-[13.5px] font-semibold flex items-center justify-center gap-1 shadow"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              {lang === 'en' ? 'Resume' : '재개'}
            </button>
          )}
          <button
            onClick={handleResetTimer}
            className={`py-2 bg-gray-500/20 hover:bg-gray-500/30 rounded-xl text-[13.5px] font-semibold border border-gray-500/25 flex items-center justify-center gap-1 ${currentThemeConfig.text}`}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            {lang === 'en' ? 'Reset' : '리셋'}
          </button>
          <button
            onClick={handleTimerComplete}
            className="col-span-2 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-[13.5px] font-bold flex items-center justify-center gap-1 shadow-sm"
          >
            <Power className="w-3 h-3" />
            {lang === 'en' ? 'Trigger Action Now' : '즉시 예약 동작 격발'}
          </button>
        </>
      )}
    </div>
  );

  // Time dialing input for idle state
  const renderDialerInput = () => (
    timerState === 'idle' && (
      <div className="flex items-center justify-center gap-1.5 text-white my-1">
        <input
          type="number"
          min={0}
          max={23}
          value={inputH}
          onChange={(e) => setInputH(Math.min(23, Math.max(0, parseInt(e.target.value) || 0)))}
          className="w-10 text-center text-[13.5px] p-1 rounded border border-gray-600 bg-black/40 font-mono font-semibold"
        />
        <span>:</span>
        <input
          type="number"
          min={0}
          max={59}
          value={inputM}
          onChange={(e) => setInputM(Math.min(59, Math.max(0, parseInt(e.target.value) || 0)))}
          className="w-10 text-center text-[13.5px] p-1 rounded border border-gray-600 bg-black/40 font-mono font-semibold"
        />
        <span>:</span>
        <input
          type="number"
          min={0}
          max={59}
          value={inputS}
          onChange={(e) => setInputS(Math.min(59, Math.max(0, parseInt(e.target.value) || 0)))}
          className="w-10 text-center text-[13.5px] p-1 rounded border border-gray-600 bg-black/40 font-mono font-semibold"
        />
      </div>
    )
  );

  // Quick preset bar
  const renderQuickPresets = () => (
    <div className="grid grid-cols-3 gap-1">
      <button onClick={() => handleQuickPreset(10)} className="py-1 text-[13.5px] border border-gray-500/10 rounded hover:bg-white/5 text-gray-400 cursor-pointer">{lang === 'en' ? '10m' : '10분'}</button>
      <button onClick={() => handleQuickPreset(30)} className="py-1 text-[13.5px] border border-gray-500/10 rounded hover:bg-white/5 text-gray-400 cursor-pointer">{lang === 'en' ? '30m' : '30분'}</button>
      <button onClick={() => handleQuickPreset(60)} className="py-1 text-[13.5px] border border-gray-500/10 rounded hover:bg-white/5 text-gray-400 cursor-pointer">{lang === 'en' ? '1h' : '1시간'}</button>
    </div>
  );

  // =========================================================================
  // DESIGN 1: STANDARD NEON RING
  // =========================================================================
  if (widgetDesign === 'standard') {
    return (
      <motion.div
        layout
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: widgetOpacity / 100, scale: 1 }}
        style={{ width: `${widgetWidth}px` }}
        className={`rounded-2xl overflow-hidden shadow-2xl border-2 flex flex-col max-h-[calc(100vh-2rem)] transition-all duration-300 ease-in-out ${
          isWarningActive 
            ? 'border-red-500/95 shadow-red-500/30 ring-4 ring-red-500/15' 
            : 'border-blue-500/80 shadow-blue-500/10'
        } ${currentThemeConfig.windowBg} ${selectedFont}`}
      >
        {/* Header bar */}
        <div className={`shrink-0 text-white text-[13.5px] py-2 px-3 font-semibold flex items-center justify-between transition-all duration-300 ease-in-out ${
          isWarningActive 
            ? 'bg-gradient-to-r from-red-600 to-rose-700 animate-pulse' 
            : 'bg-gradient-to-r from-blue-700 via-indigo-700 to-slate-800'
        }`}>
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-md overflow-hidden ring-1 ring-cyan-400/40 shadow-sm flex-shrink-0 bg-slate-950">
              <img src="/PowerController.png" alt="Icon" className="w-full h-full object-cover scale-105" />
            </div>
            <span className="font-bold tracking-tight">{isWarningActive ? '🚨 1분 미만 임박' : (lang === 'en' ? 'Compact Power Widget' : '컴팩트 전원 위젯')}</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowConfigDrawer(!showConfigDrawer)}
              className="p-1 rounded hover:bg-white/20 text-white transition-colors"
              title={lang === 'en' ? 'Widget Customizer' : '위젯 크기 및 디자인 조절'}
            >
              <Sliders className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={toggleAlwaysOnTop}
              className="p-1 rounded hover:bg-white/20 text-white transition-colors"
              title={lang === 'en' ? 'Maximize to main window' : '전체 창으로 복귀'}
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {renderConfigDrawer()}

        {/* Middle Content Container */}
        <div className="flex-1 min-h-0 p-3.5 space-y-3 overflow-y-auto flex flex-col transition-all duration-300 ease-in-out">
          {/* Action selection */}
          <div className="shrink-0 grid grid-cols-6 gap-1 bg-black/30 p-1.5 rounded-xl border border-white/5 transition-all duration-300 ease-in-out">
            {actionItems.map((item) => {
              const Icon = item.icon;
              const active = powerMode === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleModeChange(item.id)}
                  className={`py-2 rounded-lg flex flex-col items-center justify-center gap-1 transition-all duration-200 cursor-pointer ${
                    active
                      ? 'bg-gradient-to-b from-blue-500 to-indigo-600 text-white font-bold shadow-md shadow-blue-900/40 ring-1 ring-blue-400/50 scale-105'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                  title={lang === 'en' ? item.labelEn : item.labelKo}
                >
                  <Icon className="w-4.5 h-4.5 stroke-[2.2]" />
                </button>
              );
            })}
          </div>

          {/* Circular dial visualizer */}
          <div className="flex-1 min-h-0 flex flex-col items-center justify-center py-2 bg-black/10 rounded-xl transition-all duration-300 ease-in-out">
            <div className="relative w-32 h-32 flex items-center justify-center shrink-0">
              <svg className="absolute inset-0 w-full h-full -rotate-90">
                <circle cx="64" cy="64" r="56" className="stroke-gray-600/20 fill-none" strokeWidth="5" />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  className={`fill-none transition-all duration-1000 ${
                    powerMode === 'shutdown' ? 'stroke-rose-500' : 'stroke-blue-500'
                  }`}
                  strokeWidth="5"
                  strokeDasharray={2 * Math.PI * 56}
                  strokeDashoffset={getStrokeDashOffset() * (112 / 132)}
                  strokeLinecap="round"
                />
              </svg>
              <div className="flex flex-col items-center justify-center text-center z-10 px-1">
                {showCurrentTimeCompact && (
                  <span 
                    style={{ fontSize: `${clockFontSize}px` }} 
                    className="font-mono font-semibold text-gray-300 leading-none mb-1 transition-all duration-300 ease-in-out"
                  >
                    🕒 {currentTimeFormatted}
                  </span>
                )}
                <span 
                  style={{ fontSize: `${timerFontSize}px` }} 
                  className="font-mono font-bold tracking-tight text-white tabnum leading-none transition-all duration-300 ease-in-out"
                >
                  {formatTimeStr(secondsRemaining)}
                </span>
                <span className="text-[13.5px] font-semibold px-2 py-0.5 rounded-full mt-1 bg-blue-500/20 text-blue-300 transition-all duration-300 ease-in-out">
                  {getPowerModeKorean(powerMode)}
                </span>
              </div>
            </div>
            {renderDialerInput()}
          </div>
        </div>

        {/* Bottom Toolbar */}
        <div className="shrink-0 px-3.5 pb-3.5 space-y-2 transition-all duration-300 ease-in-out">
          {renderControlButtons()}
          {renderQuickPresets()}
        </div>
      </motion.div>
    );
  }

  // =========================================================================
  // DESIGN 2: CYBER HUD (Sci-Fi Digital)
  // =========================================================================
  if (widgetDesign === 'cyber_hud') {
    return (
      <motion.div
        layout
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: widgetOpacity / 100, scale: 1 }}
        style={{ width: `${widgetWidth}px` }}
        className="rounded-xl overflow-hidden shadow-2xl border-2 border-cyan-500/80 bg-gray-950 text-cyan-400 font-mono select-none flex flex-col max-h-[calc(100vh-2rem)] transition-all duration-300 ease-in-out"
      >
        {/* HUD Top Bar */}
        <div className="shrink-0 bg-cyan-950/70 border-b border-cyan-500/30 px-3 py-1.5 flex items-center justify-between text-[13.5px] font-bold transition-all duration-300 ease-in-out">
          <div className="flex items-center gap-1.5 text-cyan-300">
            <Terminal className="w-3.5 h-3.5" />
            <span>SYS.HUD // {getPowerModeKorean(powerMode).toUpperCase()}</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowConfigDrawer(!showConfigDrawer)}
              className="p-1 rounded hover:bg-cyan-800/40 text-cyan-300"
              title={lang === 'en' ? 'HUD Options' : 'HUD 설정'}
            >
              <Sliders className="w-3 h-3" />
            </button>
            <button
              onClick={toggleAlwaysOnTop}
              className="p-1 rounded hover:bg-cyan-800/40 text-cyan-300"
            >
              <Maximize2 className="w-3 h-3" />
            </button>
          </div>
        </div>

        {renderConfigDrawer()}

        {/* Middle Content Container */}
        <div className="flex-1 min-h-0 p-3 space-y-3 overflow-y-auto flex flex-col transition-all duration-300 ease-in-out">
          {/* Cyber Digital Display with Corner Brackets */}
          <div className="flex-1 min-h-0 relative p-3 bg-cyan-950/20 border border-cyan-500/30 rounded-lg text-center flex flex-col items-center justify-center transition-all duration-300 ease-in-out">
            <span className="absolute -top-1 -left-1 text-[13.5px] text-cyan-400">┌</span>
            <span className="absolute -top-1 -right-1 text-[13.5px] text-cyan-400">┐</span>
            <span className="absolute -bottom-1 -left-1 text-[13.5px] text-cyan-400">└</span>
            <span className="absolute -bottom-1 -right-1 text-[13.5px] text-cyan-400">┘</span>

            {showCurrentTimeCompact && (
              <div 
                style={{ fontSize: `${clockFontSize}px` }} 
                className="text-cyan-400/80 tracking-widest mb-1 transition-all duration-300 ease-in-out"
              >
                CLOCK: {currentTimeFormatted}
              </div>
            )}

            <div 
              style={{ fontSize: `${timerFontSize}px` }}
              className="font-bold text-cyan-300 tracking-wider text-shadow-cyan transition-all duration-300 ease-in-out"
            >
              [ {formatTimeStr(secondsRemaining)} ]
            </div>

            {/* Linear Progress Bar */}
            <div className="w-full bg-cyan-950 h-1.5 rounded-full mt-2 overflow-hidden border border-cyan-800 shrink-0">
              <div
                className="bg-cyan-400 h-full transition-all duration-500"
                style={{ width: `${totalSeconds ? (secondsRemaining / totalSeconds) * 100 : 0}%` }}
              />
            </div>

            {renderDialerInput()}
          </div>

          {/* Mode Selector */}
          <div className="shrink-0 grid grid-cols-6 gap-1">
            {actionItems.map((item) => {
              const Icon = item.icon;
              const active = powerMode === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleModeChange(item.id)}
                  className={`py-1.5 rounded border text-[13.5px] font-bold flex flex-col items-center transition-all duration-300 ${
                    active 
                      ? 'border-cyan-400 bg-cyan-500/20 text-cyan-200 shadow-[0_0_8px_rgba(6,182,212,0.4)]' 
                      : 'border-cyan-900/50 bg-black/40 text-gray-500 hover:text-cyan-400'
                  }`}
                >
                  <Icon className="w-3 h-3" />
                </button>
              );
            })}
          </div>
        </div>

        {/* Bottom Toolbar */}
        <div className="shrink-0 px-3 pb-3 space-y-2 transition-all duration-300 ease-in-out">
          {renderControlButtons()}
          {renderQuickPresets()}
        </div>
      </motion.div>
    );
  }

  // =========================================================================
  // DESIGN 3: MINIMAL SLIM BAR (Horizontal floating strip)
  // =========================================================================
  if (widgetDesign === 'minimal_bar') {
    return (
      <motion.div
        layout
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: widgetOpacity / 100, scale: 1 }}
        style={{ width: `${widgetWidth}px` }}
        className="rounded-full shadow-2xl border border-blue-500/50 bg-gray-900/95 px-3 py-2 text-white flex items-center justify-between gap-2 select-none transition-all duration-300 ease-in-out"
      >
        {/* Mode icon indicator */}
        <div 
          onClick={() => {
            const nextIdx = (actionItems.findIndex(a => a.id === powerMode) + 1) % actionItems.length;
            handleModeChange(actionItems[nextIdx].id);
          }}
          className={`shrink-0 px-2 py-1 rounded-full text-[13.5px] font-bold flex items-center gap-1 cursor-pointer transition-colors ${
            powerMode === 'shutdown' ? 'bg-rose-600 text-white' : 'bg-blue-600 text-white'
          }`}
          title={lang === 'en' ? 'Click to cycle mode' : '클릭하여 전원 동작 변경'}
        >
          <Power className="w-3 h-3" />
          <span>{getPowerModeKorean(powerMode)}</span>
        </div>

        {/* Center / Middle Content: Clock & Timer */}
        <div className="flex-1 min-h-0 flex items-center justify-center gap-2 font-mono transition-all duration-300 ease-in-out">
          {showCurrentTimeCompact && (
            <span style={{ fontSize: `${clockFontSize}px` }} className="text-gray-400 transition-all duration-300 ease-in-out">
              {currentTimeFormatted}
            </span>
          )}
          <span style={{ fontSize: `${timerFontSize}px` }} className="font-bold text-white tabnum transition-all duration-300 ease-in-out">
            {formatTimeStr(secondsRemaining)}
          </span>
        </div>

        {/* Bottom / Right Toolbar */}
        <div className="shrink-0 flex items-center gap-1 transition-all duration-300 ease-in-out">
          {timerState === 'running' ? (
            <button
              onClick={handlePauseTimer}
              className="p-1.5 rounded-full bg-amber-500 hover:bg-amber-400 text-white"
              title="Pause"
            >
              <Pause className="w-3 h-3" />
            </button>
          ) : (
            <button
              onClick={handleStartTimer}
              className="p-1.5 rounded-full bg-green-600 hover:bg-green-500 text-white"
              title="Start"
            >
              <Play className="w-3 h-3 fill-white" />
            </button>
          )}

          <button
            onClick={handleResetTimer}
            className="p-1.5 rounded-full bg-gray-800 hover:bg-gray-700 text-gray-300"
            title="Reset"
          >
            <RotateCcw className="w-3 h-3" />
          </button>

          <button
            onClick={() => setShowConfigDrawer(!showConfigDrawer)}
            className="p-1.5 rounded-full hover:bg-gray-800 text-gray-400"
            title="Options"
          >
            <Sliders className="w-3 h-3" />
          </button>

          <button
            onClick={toggleAlwaysOnTop}
            className="p-1.5 rounded-full hover:bg-gray-800 text-gray-400"
            title="Maximize"
          >
            <Maximize2 className="w-3 h-3" />
          </button>
        </div>
      </motion.div>
    );
  }

  // =========================================================================
  // DESIGN 4: RETRO LED MATRIX (Classic Amber Digital Clock)
  // =========================================================================
  if (widgetDesign === 'retro_led') {
    return (
      <motion.div
        layout
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: widgetOpacity / 100, scale: 1 }}
        style={{ width: `${widgetWidth}px` }}
        className="rounded-2xl overflow-hidden shadow-2xl border-4 border-[#2b2416] bg-[#140f07] text-[#f59e0b] select-none flex flex-col max-h-[calc(100vh-2rem)] transition-all duration-300 ease-in-out"
      >
        {/* Retro Header */}
        <div className="shrink-0 bg-[#1f170b] border-b border-[#3d2c10] px-3 py-1.5 flex items-center justify-between text-[13.5px] font-bold tracking-widest text-[#d97706] transition-all duration-300 ease-in-out">
          <span>DIGITAL POWER CONTROLLER // LED-7S</span>
          <div className="flex items-center gap-1">
            <button onClick={() => setShowConfigDrawer(!showConfigDrawer)} className="p-1 hover:text-white">
              <Sliders className="w-3 h-3" />
            </button>
            <button onClick={toggleAlwaysOnTop} className="p-1 hover:text-white">
              <Maximize2 className="w-3 h-3" />
            </button>
          </div>
        </div>

        {renderConfigDrawer()}

        {/* Middle Content Container */}
        <div className="flex-1 min-h-0 p-3.5 space-y-3 overflow-y-auto flex flex-col transition-all duration-300 ease-in-out">
          {/* LED Panel Bezel */}
          <div className="flex-1 min-h-0 p-3 bg-[#0a0703] border-2 border-[#2b200b] rounded-xl text-center shadow-inner flex flex-col items-center justify-center transition-all duration-300 ease-in-out">
            {showCurrentTimeCompact && (
              <div 
                style={{ fontSize: `${clockFontSize}px` }} 
                className="font-mono text-[#b45309] tracking-widest mb-1 transition-all duration-300 ease-in-out"
              >
                CLOCK: {currentTimeFormatted}
              </div>
            )}
            <div 
              style={{ fontSize: `${timerFontSize}px` }} 
              className="font-mono font-extrabold tracking-widest text-[#fbbf24] drop-shadow-[0_0_10px_rgba(245,158,11,0.5)] transition-all duration-300 ease-in-out"
            >
              {formatTimeStr(secondsRemaining)}
            </div>
            <div className="text-[13.5px] font-bold uppercase tracking-wider text-[#d97706] mt-1 transition-all duration-300 ease-in-out">
              [ {getPowerModeKorean(powerMode)} ]
            </div>
            {renderDialerInput()}
          </div>

          {/* Push-button action row */}
          <div className="shrink-0 grid grid-cols-6 gap-1">
            {actionItems.map((item) => {
              const active = powerMode === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleModeChange(item.id)}
                  className={`py-1 rounded border text-[13.5px] font-bold transition-all duration-300 ${
                    active ? 'border-[#f59e0b] bg-[#f59e0b]/20 text-[#fbbf24]' : 'border-[#3d2c10] text-[#78511a] hover:text-[#d97706]'
                  }`}
                >
                  {lang === 'en' ? item.labelEn.slice(0, 4) : item.labelKo.slice(0, 2)}
                </button>
              );
            })}
          </div>
        </div>

        {/* Bottom Toolbar */}
        <div className="shrink-0 px-3.5 pb-3.5 space-y-2 transition-all duration-300 ease-in-out">
          {renderControlButtons()}
          {renderQuickPresets()}
        </div>
      </motion.div>
    );
  }

  // =========================================================================
  // DESIGN 5: CLEAN CARD (Modern Minimalist Card)
  // =========================================================================
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: widgetOpacity / 100, scale: 1 }}
      style={{ width: `${widgetWidth}px` }}
      className={`rounded-2xl overflow-hidden shadow-2xl border border-gray-500/20 flex flex-col max-h-[calc(100vh-2rem)] transition-all duration-300 ease-in-out ${currentThemeConfig.windowBg} ${selectedFont}`}
    >
      {/* Clean Top Bar */}
      <div className="shrink-0 p-4 pb-2 flex items-center justify-between border-b border-gray-500/10 transition-all duration-300 ease-in-out">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-500" />
          <span className="font-bold text-[13.5px]">{lang === 'en' ? 'Power Widget' : '전원 관리 미니창'}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowConfigDrawer(!showConfigDrawer)}
            className="p-1 rounded-lg hover:bg-gray-500/10 text-gray-400"
            title="Options"
          >
            <Sliders className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={toggleAlwaysOnTop}
            className="p-1 rounded-lg hover:bg-gray-500/10 text-gray-400"
            title="Maximize"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {renderConfigDrawer()}

      {/* Middle Content Container */}
      <div className="flex-1 min-h-0 p-4 space-y-3 overflow-y-auto flex flex-col transition-all duration-300 ease-in-out">
        {/* Mode pill & Clock */}
        <div className="shrink-0 flex items-center justify-between px-1">
          <span className={`text-[13.5px] font-bold px-2 py-0.5 rounded-full transition-all duration-300 ${
            powerMode === 'shutdown' ? 'bg-rose-500/15 text-rose-400' : 'bg-blue-500/15 text-blue-400'
          }`}>
            {getPowerModeKorean(powerMode)}
          </span>
          {showCurrentTimeCompact && (
            <span style={{ fontSize: `${clockFontSize}px` }} className="font-mono text-gray-400 transition-all duration-300 ease-in-out">
              {currentTimeFormatted}
            </span>
          )}
        </div>

        {/* Main Countdown Display */}
        <div className="flex-1 min-h-0 text-center py-2 flex flex-col items-center justify-center transition-all duration-300 ease-in-out">
          <div 
            style={{ fontSize: `${timerFontSize}px` }}
            className="font-bold tracking-tight font-mono text-white transition-all duration-300 ease-in-out"
          >
            {formatTimeStr(secondsRemaining)}
          </div>
          {renderDialerInput()}
        </div>
      </div>

      {/* Bottom Toolbar */}
      <div className="shrink-0 px-4 pb-4 space-y-2 transition-all duration-300 ease-in-out">
        {renderControlButtons()}
        {renderQuickPresets()}
      </div>
    </motion.div>
  );
}
