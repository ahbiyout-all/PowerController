import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Power, RotateCcw, ShieldCheck, Loader2, Moon, Laptop, LogOut, RotateCw, Clock } from 'lucide-react';
import { PowerMode } from '../types';

interface PowerSimulatorProps {
  mode: PowerMode;
  onClose: () => void;
  onRestartSimulation: () => void;
  lang?: 'ko' | 'en';
  forceClose?: boolean;
}

export default function PowerSimulator({ mode, onClose, onRestartSimulation, lang = 'ko', forceClose = true }: PowerSimulatorProps) {
  const [step, setStep] = useState<number>(0);
  const [complete, setComplete] = useState<boolean>(false);
  const [autoCloseSec, setAutoCloseSec] = useState<number>(10);

  // Helper labels for UI display
  const getSimMeta = () => {
    switch (mode) {
      case 'alarm':
        return {
          title: lang === 'en' ? 'Scheduler Alarm Triggered!' : '스케줄러 예약 알람 작동 중!',
          icon: Clock,
          color: 'text-pink-400',
          finalDesc: lang === 'en' ? 'The scheduled alarm notification was completed successfully.' : '예약된 스케줄러 사운드 알람이 성공적으로 마무리되었습니다.',
          lastStepTitle: lang === 'en' ? 'Alarm Chime Complete' : '알람 챠임 멜로디 연주 완료',
          lastStepDesc: lang === 'en' ? 'Auditory warning buzzer pulse played and screen alerts safely dispatched.' : '경고 신호 멜로디 및 화면 시각 알림 기믹을 정상 분출 완료하였습니다.'
        };
      case 'shutdown':
        return {
          title: lang === 'en' ? 'Virtual System Shutting Down...' : '가상 시스템 종료 중',
          icon: Power,
          color: 'text-red-400',
          finalDesc: lang === 'en' ? 'The computer has safely completed the virtual power shutdown process.' : '컴퓨터가 가상 전원 차단(Shutdown) 프로세스를 안전하게 마쳤습니다.',
          lastStepTitle: lang === 'en' ? 'Virtual Power System Offline' : '가상 전원 계통 오프라인',
          lastStepDesc: lang === 'en' ? 'Main kernel buzzer feedback received and ACPI complete shutdown pulse activated.' : '메인 커널 버저 피드백 수신 및 ACPI 완전 차단 펄스를 가동시켰습니다.'
        };
      case 'restart':
        return {
          title: lang === 'en' ? 'Virtual System Rebooting...' : '가상 시스템 다시 시작 중',
          icon: RotateCw,
          color: 'text-blue-400',
          finalDesc: lang === 'en' ? 'The computer has successfully executed the virtual hardware reboot cycle.' : '컴퓨터가 가상 하드웨어 재부팅(Reboot) 사이클을 성공적으로 도출했습니다.',
          lastStepTitle: lang === 'en' ? 'Hardware Cold Reboot' : '하드웨어 콜드 리부트',
          lastStepDesc: lang === 'en' ? 'CPU register reset pin triggered and virtual memory binding region wiped.' : 'CPU 레지스터 리셋 핀 트리거 및 가상 메모리 바인딩 영역 삭제 완료.'
        };
      case 'sleep':
        return {
          title: lang === 'en' ? 'Entering Virtual Sleep Mode...' : '가상 절전 모드 전환 중',
          icon: Moon,
          color: 'text-purple-400',
          finalDesc: lang === 'en' ? 'The computer has safely entered the standby/virtual sleep state.' : '컴퓨터가 대기 가습/가상 슬립 상태(Sleep / Suspend)에 무사히 진입했습니다.',
          lastStepTitle: lang === 'en' ? 'Low Power Cache Preservation' : '저전력 보존 캐싱',
          lastStepDesc: lang === 'en' ? 'Session pointers packed to RAM and active housing energy supply cut off.' : '세션 포인터를 RAM 영역에 압축 보관하고 대전 하우징 전력을 차단 중입니다.'
        };
      case 'screenoff':
        return {
          title: lang === 'en' ? 'Turning Off Virtual Display...' : '가상 화면 끄기 동작 중',
          icon: Laptop,
          color: 'text-amber-400',
          finalDesc: lang === 'en' ? 'The computer monitor display output has been deactivated.' : '컴퓨터 모니터 디스플레이(Screen Off) 출력이 영구적으로 비활성화되었습니다.',
          lastStepTitle: lang === 'en' ? 'Display Dev Blackout' : '화면 가독 장비 블랙아웃',
          lastStepDesc: lang === 'en' ? 'Monitor LCD backlight driver signal interruption pulse injected.' : '모니터 LCD 백라이트 드라이버 가용 신호 중단 펄스를 주입하였습니다.'
        };
      case 'logout':
        return {
          title: lang === 'en' ? 'Logging Out Virtual Session...' : '가상 세션 로그아웃 중',
          icon: LogOut,
          color: 'text-emerald-400',
          finalDesc: lang === 'en' ? 'The current user session profile has been safely closed and locks console active.' : '현재 사용자의 가상 암호 프로필 정보가 파괴되고 잠금 콘솔로 세션 전환되었습니다.',
          lastStepTitle: lang === 'en' ? 'User Credentials Detachment' : '사용자 자격 증명 탈착',
          lastStepDesc: lang === 'en' ? 'Tokens completely invalidated. Updating Desktop Window Manager login reflectors.' : '토큰 무효화 완료. 데스크톱 윈도우 관리자(DWM) 로그인 리플렉터를 갱신합니다.'
        };
      default:
        return {
          title: lang === 'en' ? 'Restoring System Power...' : '가상 전원 복구 중',
          icon: Power,
          color: 'text-gray-400',
          finalDesc: lang === 'en' ? 'Selected diagnostic simulation action finished normally.' : '지정한 동작 시뮬레이션이 모두 정상 마감되었습니다.',
          lastStepTitle: lang === 'en' ? 'Sequence Wrap Up' : '시퀀스 마무리',
          lastStepDesc: lang === 'en' ? 'System assets recursively collected and control panel indicators restored.' : '시스템 자원을 초기화 수렴 처리하고 제어판을 마킹 복구했습니다.'
        };
    }
  };

  const meta = getSimMeta();

  const steps = [
    { 
      title: lang === 'en' ? 'Scanning Running Background Virtual Apps' : '실행 중인 백그라운드 가상 앱 검사', 
      desc: lang === 'en' ? 'Terminating temporary background threads and locking active handles gracefully...' : '더미 메모리에서 구동 중인 임시 스레드와 핸들을 안전하게 취소하는 중...' 
    },
    { 
      title: lang === 'en' ? 'Saving System Cache and Disk Syncing' : '시스템 캐시 및 I/O 동기화 세이빙', 
      desc: lang === 'en' ? 'Issuing virtual buffer sync commands to prevent partition table write misses...' : '가상 버퍼 테이블 쓰기 누락 방지를 위해 I/O 디스크 플러시 명령 실행...' 
    },
    { 
      title: lang === 'en' ? 'Expiring Interactive Security Credentials' : '사용자 보안 토큰 만료 정지', 
      desc: lang === 'en' ? 'De-authorizing web synapse tokens and isolating volatile cookies safely...' : '현재 연결된 웹 시냅스의 권한 프로필 및 임시 캐시 세션을 비휘발 분리...' 
    },
    { 
      title: meta.lastStepTitle, 
      desc: meta.lastStepDesc 
    }
  ];

  useEffect(() => {
    if (step < steps.length) {
      const timer = setTimeout(() => {
        setStep(prev => prev + 1);
      }, 1200);
      return () => clearTimeout(timer);
    } else {
      setComplete(true);
    }
  }, [step, steps.length]);

  useEffect(() => {
    if (!complete) return;
    
    if (autoCloseSec > 0) {
      const timer = setTimeout(() => {
        setAutoCloseSec(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      onClose();
    }
  }, [complete, autoCloseSec, onClose]);

  const CurrentIcon = meta.icon;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#070e17] text-white select-none">
        {/* Soft custom color-glowing background ambient light */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-[130px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[130px]" />

        {!complete ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="z-10 flex flex-col items-center max-w-md w-full px-6 text-center"
          >
            {/* Elegant Spinning Gear / Circle */}
            <div className="relative w-24 h-24 mb-6 flex items-center justify-center bg-white/5 rounded-full border border-white/10 backdrop-blur-md shadow-2xl">
              <Loader2 className={`w-12 h-12 ${meta.color} animate-spin`} />
              <div className={`absolute inset-0 border border-t-transparent ${meta.color} rounded-full animate-ping opacity-25`} />
            </div>

            {/* Title representing mode */}
            <h2 className="font-display font-extrabold text-2xl tracking-tight mb-1.5 flex items-center gap-2 justify-center">
              <CurrentIcon className={`w-6 h-6 ${meta.color} animate-pulse`} />
              <span>{meta.title}</span>
            </h2>
            <p className="text-gray-400 font-semibold text-[11px] mb-3 uppercase tracking-widest font-mono">
              Virtual Device Power state: {mode}
            </p>

            {forceClose && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1 mb-6 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-400 text-[10px] font-bold">
                <span>⚡ {lang === 'en' ? 'Force Close Running Apps (/f) Active' : '실행 중인 앱 강제 종료 플래그 (/f) 적용됨'}</span>
              </div>
            )}

            {/* Sequence Status Bar */}
            <div className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-left backdrop-blur-lg mb-8">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-blue-400 uppercase font-mono">
                  {lang === 'en' ? `Step ${Math.min(step + 1, steps.length)} / ${steps.length}` : `동작 단계 ${Math.min(step + 1, steps.length)} / ${steps.length}`}
                </span>
                <span className="text-[10.5px] text-gray-400 font-mono">
                  {Math.round((Math.min(step, steps.length) / steps.length) * 100)}% {lang === 'en' ? 'Completed' : '진행됨'}
                </span>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden mb-3">
                <motion.div
                  className="h-full bg-blue-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${(Math.min(step, steps.length) / steps.length) * 100}%` }}
                  transition={{ duration: 0.4 }}
                />
              </div>

              {step < steps.length ? (
                <div>
                  <h4 className="text-sm font-semibold mb-0.5 text-gray-200">{steps[step].title}</h4>
                  <p className="text-[11.5px] text-gray-400 leading-relaxed font-sans">{steps[step].desc}</p>
                </div>
              ) : (
                <div>
                  <h4 className="text-sm font-semibold mb-0.5 text-gray-200">{lang === 'en' ? 'Awaiting Final Signal' : '최종 시그널 대기'}</h4>
                  <p className="text-[11.5px] text-gray-400 leading-relaxed">
                    {lang === 'en' ? 'Waiting for return of virtual hardware sync registers...' : '모든 가상 하드웨어 동기화 신호의 복귀를 대기 중...'}
                  </p>
                </div>
              )}
            </div>

            {/* Instant Emergency Force Cancel */}
            <button
              id="btn-simulation-cancel"
              onClick={onClose}
              className="px-5 py-2.5 bg-white/10 hover:bg-white/15 active:scale-95 border border-white/10 hover:border-white/20 rounded-xl text-xs font-semibold tracking-wide transition-all cursor-pointer"
            >
              {lang === 'en' ? 'Emergency Simulation Cancel (Safely Restore)' : '시뮬레이션 긴급 제동 (작업 공간 복구)'}
            </button>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="z-10 flex flex-col items-center max-w-sm w-full px-6 text-center"
          >
            <div className="w-20 h-20 bg-green-500/10 border border-green-500/30 rounded-full flex items-center justify-center text-green-400 mb-5 shadow-lg shadow-green-500/5 animate-bounce">
              <ShieldCheck className="w-10 h-10" />
            </div>

            <h3 className="font-display font-bold text-xl mb-2 text-gray-100">
              {lang === 'en' ? 'Simulation Completed' : '가상 제어 완료'}
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed px-2 mb-2 font-sans">
              {meta.finalDesc}
            </p>
            <p className="text-[11px] text-amber-400 font-medium mb-8 animate-pulse">
              {lang === 'en' 
                ? `Automatically returning to main screen in ${autoCloseSec} seconds...` 
                : `${autoCloseSec}초 후 자동으로 메인 화면으로 복구됩니다...`}
            </p>

            <div className="flex gap-2.5 w-full">
              <button
                id="btn-sim-reset"
                onClick={onRestartSimulation}
                className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 active:scale-95 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-lg shadow-blue-600/30 font-display"
              >
                <Power className="w-3.5 h-3.5" />
                {lang === 'en' ? 'Design New Timer' : '새 예약 설계하기'}
              </button>
              <button
                id="btn-sim-exit"
                onClick={onClose}
                className="flex-1 py-3 bg-white/10 hover:bg-white/15 active:scale-95 border border-white/10 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-1.5 cursor-pointer font-display"
              >
                {lang === 'en' ? 'Close Main Window' : '메인 창 닫기'}
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </AnimatePresence>
  );
}
