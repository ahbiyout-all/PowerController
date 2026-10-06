import React, { useState } from 'react';
import { Terminal, Copy, Check, Info, ShieldAlert } from 'lucide-react';
import { PowerMode, ThemeType } from '../types';

interface CommandCopierProps {
  mode: PowerMode;
  durationSeconds: number;
  lang?: 'ko' | 'en';
  theme?: ThemeType;
}

const copierThemeConfigs = {
  dark: {
    container: 'bg-white/50 dark:bg-gray-900/40 border-gray-200 dark:border-gray-800 text-[#e1e4ed]',
    controls: 'bg-gray-50/50 dark:bg-gray-950/50 border-gray-200/50 dark:border-gray-800/40',
    item: 'bg-gray-50 dark:bg-gray-950 border-gray-100 dark:border-gray-900 hover:border-gray-200 dark:hover:border-gray-800 text-gray-700 dark:text-gray-300',
    badge: 'bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400',
    pre: 'text-blue-600 dark:text-blue-400 bg-white/20 dark:bg-black/30 border-gray-100/50 dark:border-gray-900/30',
    warning: 'bg-amber-50 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900/30 text-amber-700 dark:text-amber-400'
  },
  gray: {
    container: 'bg-[#242f41] border-[#475569] text-[#f8fafc]',
    controls: 'bg-[#1e293b] border-[#475569] text-slate-100',
    item: 'bg-[#1e293b] border-[#475569] text-[#f8fafc] hover:border-blue-400',
    badge: 'bg-[#475569] text-slate-100 font-semibold',
    pre: 'text-blue-300 bg-slate-950 border-[#475569] font-mono font-bold',
    warning: 'bg-[#334155] border-[#475569] text-[#f8fafc]'
  },
  beige: {
    container: 'bg-[#fdfbf7] border-[#c8bcaa] text-[#2c2217]',
    controls: 'bg-[#f5eee4] border-[#c8bcaa]',
    item: 'bg-[#f5eee4] border-[#c8bcaa] text-[#2c2217] hover:border-[#584835]',
    badge: 'bg-[#e8ded0] text-[#5c4d38] font-bold',
    pre: 'text-[#1e3a8a] bg-white border-[#c8bcaa] font-mono font-bold',
    warning: 'bg-[#fffbeb] border-[#fde68a] text-[#7c2d12]'
  }
};

export default function CommandCopier({ mode, durationSeconds, lang = 'ko', theme = 'dark' }: CommandCopierProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [forceClose, setForceClose] = useState<boolean>(true);
  const [customSeconds, setCustomSeconds] = useState<number | null>(null);

  const secondsToUse = customSeconds !== null ? customSeconds : durationSeconds;
  const minutes = Math.ceil(secondsToUse / 60);

  const getCommands = () => {
    const fFlag = forceClose ? ' /f' : '';
    
    switch (mode) {
      case 'shutdown':
        return [
          {
            id: 'cmd',
            name: lang === 'en' ? 'Windows CMD (Command Prompt)' : 'Windows CMD (명령 프롬프트)',
            code: secondsToUse === 0 ? `shutdown /s${fFlag} /t 0` : `shutdown /s${fFlag} /t ${secondsToUse}`,
            desc: lang === 'en' ? `Forces system shutdown after designated ${secondsToUse}s.` : `지정 시간(${secondsToUse}초) 후 시스템 강제 종료.`
          },
          {
            id: 'ps',
            name: 'PowerShell (Admin)',
            code: `Start-Process shutdown -ArgumentList "/s"${forceClose ? ', "/f"' : ''}, "/t", "${secondsToUse}" -Verb RunAs`,
            desc: lang === 'en' ? 'Forces system shutdown safely with administrator privilege configuration.' : '어드민 권한으로 셰이핑하여 안전한 시스템 전원 다운.'
          },
          {
            id: 'bash',
            name: 'macOS / Linux Terminal',
            code: secondsToUse === 0 ? 'sudo shutdown -h now' : `sudo shutdown -h +${minutes}`,
            desc: lang === 'en' ? `Unix-like shell delayed shutdown script (after ${minutes}m).` : `유닉스 계열 지연 종료 스크립트 (${minutes}분 후).`
          }
        ];
      case 'restart':
        return [
          {
            id: 'cmd',
            name: lang === 'en' ? 'Windows CMD (Command Prompt)' : 'Windows CMD (명령 프롬프트)',
            code: secondsToUse === 0 ? `shutdown /r${fFlag} /t 0` : `shutdown /r${fFlag} /t ${secondsToUse}`,
            desc: lang === 'en' ? `Forces system reboot cycle after scheduled ${secondsToUse}s.` : `지정 시간(${secondsToUse}초) 후 시스템 안정 재기동.`
          },
          {
            id: 'ps',
            name: 'PowerShell (Admin)',
            code: `Start-Process shutdown -ArgumentList "/r"${forceClose ? ', "/f"' : ''}, "/t", "${secondsToUse}" -Verb RunAs`,
            desc: lang === 'en' ? 'Forces system reboot safely backed by administrator execution policies.' : '안정적인 윈도우 마운트 지연 재부팅 커맨드.'
          },
          {
            id: 'bash',
            name: 'macOS / Linux Terminal',
            code: secondsToUse === 0 ? 'sudo shutdown -r now' : `sudo shutdown -r +${minutes}`,
            desc: lang === 'en' ? `Unix-like shell delayed warm reboot script (after ${minutes}m).` : `유닉스 지延迟 계열 시스템 안전 재부팅 (${minutes}분 후).`
          }
        ];
      case 'sleep':
        return [
          {
            id: 'cmd',
            name: lang === 'en' ? 'Windows CMD (Command Prompt)' : 'Windows CMD (명령 프롬프트)',
            code: secondsToUse === 0 
              ? `rundll32.exe powrprof.dll,SetSuspendState 0,1,0` 
              : `timeout /t ${secondsToUse} && rundll32.exe powrprof.dll,SetSuspendState 0,1,0`,
            desc: lang === 'en' ? 'Enters low-power Sleep mode (Suspend) after delay timer.' : '대기 타이밍 이후 저전력 절전 모드(Suspend) 진입.'
          },
          {
            id: 'ps',
            name: 'PowerShell (Admin)',
            code: secondsToUse === 0
              ? `Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)`
              : `Start-Sleep -Seconds ${secondsToUse}; Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)`,
            desc: lang === 'en' ? 'Calls Windows Forms API directly to invoke system standby sleep.' : '윈도우 폼 API를 다이렉트로 호출하여 절전으로 즉시 전환.'
          },
          {
            id: 'bash',
            name: 'macOS / Linux Terminal',
            code: secondsToUse === 0 ? 'pmset sleepnow' : `sleep ${secondsToUse} && pmset sleepnow`,
            desc: lang === 'en' ? 'Controls low-power sleep state under Unix/Mac power manager.' : '시스템 슬립 파워 매니저 제어 명령.'
          }
        ];
      case 'screenoff':
        return [
          {
            id: 'cmd',
            name: lang === 'en' ? 'Windows CMD (Command Prompt)' : 'Windows CMD (명령 프롬프트)',
            code: secondsToUse === 0
              ? `powershell -Command "(Add-Type '[DllImport(\\"user32.dll\\")]public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);' -Name a -PassThru)::SendMessage(-1,0x0112,0xF170,2)"`
              : `timeout /t ${secondsToUse} && powershell -Command "(Add-Type '[DllImport(\\"user32.dll\\")]public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);' -Name a -PassThru)::SendMessage(-1,0x0112,0xF170,2)"`,
            desc: lang === 'en' ? 'Transmits monitor hardware backlight cutoff signals (Screen Off).' : '디스플레이 하드웨어 비활성화 신호 전송 (화면 끄기).'
          },
          {
            id: 'ps',
            name: 'PowerShell (Admin)',
            code: secondsToUse === 0
              ? `(Add-Type '[DllImport("user32.dll")]public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);' -Name a -PassThru)::SendMessage(-1,0x0112,0xF170,2)`
              : `Start-Sleep -Seconds ${secondsToUse}; (Add-Type '[DllImport("user32.dll")]public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);' -Name a -PassThru)::SendMessage(-1,0x0112,0xF170,2)`,
            desc: lang === 'en' ? 'Loads user32 WinApi module to execute display screen hardware sleep.' : 'SendMessage API 헤더를 로드하여 모니터 정전식 전원 Off.'
          },
          {
            id: 'bash',
            name: 'macOS / Linux Terminal',
            code: secondsToUse === 0 ? 'pmset displaysleepnow' : `sleep ${secondsToUse} && pmset displaysleepnow`,
            desc: lang === 'en' ? 'Triggers display sleep via power manager on macOS.' : 'macOS 환경 가변 모니터 전원 분리 명령.'
          }
        ];
      case 'logout':
        return [
          {
            id: 'cmd',
            name: lang === 'en' ? 'Windows CMD (Command Prompt)' : 'Windows CMD (명령 프롬프트)',
            code: secondsToUse === 0 ? `shutdown /l` : `timeout /t ${secondsToUse} && shutdown /l`,
            desc: lang === 'en' ? 'Safely terminates interactive user workspace session profiles.' : '현재 로그인된 유저 세션을 디태치하고 잠금 화면으로 아웃.'
          },
          {
            id: 'ps',
            name: 'PowerShell (Admin)',
            code: secondsToUse === 0 ? `shutdown -l` : `Start-Sleep -Seconds ${secondsToUse}; shutdown -l`,
            desc: lang === 'en' ? 'Sends session logoff signals suitable for corporate compliance models.' : '오피스/회사 등 보안 필수 환경에서 세션 로그오프 지정.'
          },
          {
            id: 'bash',
            name: 'macOS Terminal / Logout',
            code: secondsToUse === 0 ? 'pkill -u $USER' : `sleep ${secondsToUse} && pkill -u $USER`,
            desc: lang === 'en' ? 'Safely terminates workspace processes linked to target user ID.' : '현재 디바이스의 특정 유비쿼터스 유저 강제 세션 해체.'
          }
        ];
      default:
        return [];
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getModeLabel = () => {
    switch (mode) {
      case 'shutdown': return lang === 'en' ? 'Shutdown' : '시스템 종료';
      case 'restart': return lang === 'en' ? 'Reboot' : '시스템 재시작';
      case 'sleep': return lang === 'en' ? 'Sleep' : '절전 모드 진입';
      case 'screenoff': return lang === 'en' ? 'Screen Off' : '모니터 화면 끄기';
      case 'logout': return lang === 'en' ? 'Logout' : '계정 로그아웃';
      default: return lang === 'en' ? 'Power Command' : '전원 명령';
    }
  };

  const currentCopierTheme = copierThemeConfigs[theme] || copierThemeConfigs.dark;

  return (
    <div className={`rounded-xl border p-4 transition-all duration-300 ${currentCopierTheme.container}`}>
      <div className="flex items-center gap-2 mb-3">
        <Terminal className="w-5 h-5 text-blue-500" />
        <h3 className="font-display font-semibold text-sm">
          {lang === 'en' ? 'Copy Host Power CLI Script' : '로컬 PC 제어 파워 커맨드 복사'}
        </h3>
        <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${currentCopierTheme.badge}`}>
          EXE / CLI Script
        </span>
      </div>

      <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 leading-relaxed">
        {lang === 'en' 
          ? 'Due to sandbox security restrictions, web apps cannot directly trigger host hardware power actions. Instead, copy the tailored scripts below and execute them in your terminal!'
          : '보안 정책 상 웹 iFrame에서는 로컬 장비를 직접 끌 수 없습니다. 아래 커맨드를 복사해 터미널에 붙여넣어 실제 제어해 보세요!'}
      </p>

      {/* Interactive Command Tuning Controls */}
      <div className={`grid grid-cols-2 gap-3 p-2.5 mb-4 rounded-lg border text-xs text-left ${currentCopierTheme.controls}`}>
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="checkbox-force-close"
            checked={forceClose}
            onChange={(e) => setForceClose(e.target.checked)}
            className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 bg-gray-100 border-gray-300 dark:bg-gray-800 dark:border-gray-700 cursor-pointer"
          />
          <label htmlFor="checkbox-force-close" className="font-medium text-gray-700 dark:text-gray-300 cursor-pointer select-none">
            {lang === 'en' ? 'Force Close Apps (/f)' : '작업 강제 종료 (/f) 적용'}
          </label>
        </div>

        <div className="flex items-center gap-1.5 justify-end">
          <span className="text-gray-400 text-[11px]">{lang === 'en' ? 'Delay Config:' : '딜레이 설정:'}</span>
          <button
            type="button"
            id="delay-btn-now"
            onClick={() => setCustomSeconds(0)}
            className={`px-2 py-0.5 rounded text-[10px] border font-semibold ${
              customSeconds === 0
                ? 'bg-blue-500 border-blue-500 text-white'
                : `${theme === 'beige' ? 'bg-[#ebe2d4] border-[#dfd5c6] text-[#8c785c]' : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-gray-400 hover:text-gray-200'}`
            }`}
          >
            {lang === 'en' ? 'Instant' : '즉시 실행'}
          </button>
          <button
            type="button"
            id="delay-btn-timer"
            onClick={() => setCustomSeconds(null)}
            className={`px-2 py-0.5 rounded text-[10px] border font-semibold ${
              customSeconds === null
                ? 'bg-blue-500 border-blue-500 text-white'
                : `${theme === 'beige' ? 'bg-[#ebe2d4] border-[#dfd5c6] text-[#8c785c]' : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-gray-400 hover:text-gray-200'}`
            }`}
          >
            {lang === 'en' ? 'Sync Timer' : '타이머 동기화'}
          </button>
        </div>
      </div>

      <div className="space-y-3 text-left">
        {getCommands().map((cmd) => (
          <div key={cmd.id} className={`relative group rounded-lg p-2.5 border transition-all duration-300 ${currentCopierTheme.item}`}>
            <div className="flex items-center justify-between mb-1">
              <span className={`text-[11px] font-bold block ${theme === 'beige' ? 'text-[#4a3e2b]' : 'text-gray-200'}`}>
                {cmd.name}
              </span>
              <button
                id={`btn-copy-${cmd.id}`}
                onClick={() => handleCopy(cmd.id, cmd.code)}
                className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-805 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 transition-colors cursor-pointer"
                title={lang === 'en' ? 'Copy Command' : '명령어 복사'}
              >
                {copiedId === cmd.id ? (
                  <Check className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
            
            <pre className={`font-mono text-[11px] overflow-x-auto whitespace-pre no-scrollbar pr-8 py-1.5 font-medium px-1.5 rounded border ${currentCopierTheme.pre}`}>
              {cmd.code}
            </pre>
            
            <p className="text-[10.5px] text-gray-400 dark:text-gray-500 mt-1 flex items-center gap-1">
              <Info className="w-3 h-3 flex-shrink-0" />
              <span>{cmd.desc}</span>
            </p>
          </div>
        ))}
      </div>

      <div className={`mt-3 flex items-start gap-1.5 p-2 rounded border text-left ${currentCopierTheme.warning}`}>
        <ShieldAlert className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400 mt-0.5 flex-shrink-0" />
        <span className="text-[10px] text-amber-700 dark:text-amber-400 leading-tight">
          {lang === 'en' 
            ? `When the web widget timer expires, it will automatically launch the custom ${getModeLabel()} full-screen virtual power simulation.`
            : `웹 위젯 타이머 만기 시 ${getModeLabel()} 풀스크린 가상 전력 시뮬레이션으로 자동 돌입합니다.`}
        </span>
      </div>
    </div>
  );
}
