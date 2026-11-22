import React, { useState } from 'react';
import { Archive, Copy, Check, Laptop, ShieldAlert, Sparkles, FileCode2, Package } from 'lucide-react';
import { APP_VERSION } from '../types';
import type { AppLang } from '../utils/i18n';
import { generatePythonScript, generateInnoSetupScript } from '../utils/scriptGenerators';

interface PackagerGuideProps {
  lang?: AppLang;
}

export default function PackagerGuide({ lang = 'ko' }: PackagerGuideProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [desktopName, setDesktopName] = useState('PowerController');
  const [activeScriptTab, setActiveScriptTab] = useState<'python' | 'inno'>('python');

  const safeName = desktopName.replace(/[^a-zA-Z0-9_-]/g, '') || 'PowerController';

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const pythonScriptCode = generatePythonScript(lang, safeName, APP_VERSION);
  const innoSetupCode = generateInnoSetupScript(lang, safeName, APP_VERSION);

  const pyInstallerCommand =
    lang === 'en'
      ? `# 1. Install runtime dependencies for GUI tray & packaging\npip install pyinstaller pystray pillow\n\n# 2. Bundle standalone Windows executable (.exe) without console window\npython -m PyInstaller --onefile --noconsole --name="${safeName}" main.py`
      : `# 1. 트레이 아이콘 및 단일 파일 빌드에 필요한 필수 패키지 설치\npip install pyinstaller pystray pillow\n\n# 2. 콘솔 창 없이 단독 실행되는 Windows 실행 파일(.exe) 생성\npython -m PyInstaller --onefile --noconsole --name="${safeName}" main.py`;

  const innoCompileCommand =
    lang === 'en'
      ? `; Compile installer wizard using Inno Setup 6 CLI (ISCC)\n"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe" /DMyAppVersion=${APP_VERSION} ${safeName}.iss`
      : `; Inno Setup 6 CLI 컴파일러(ISCC)를 사용하여 설치 마법사 빌드\n"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe" /DMyAppVersion=${APP_VERSION} ${safeName}.iss`;

  const currentScriptText = activeScriptTab === 'python' ? pythonScriptCode : innoSetupCode;
  const currentCompileCommand = activeScriptTab === 'python' ? pyInstallerCommand : innoCompileCommand;

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/40 dark:bg-gray-900/40 p-4 space-y-4 text-left select-none">
      <div className="flex items-center justify-between gap-2 pb-2 border-b border-gray-200/50 dark:border-gray-800 flex-wrap">
        <div className="flex items-center gap-2">
          <Archive className="w-4.5 h-4.5 text-blue-500" />
          <h3 className="font-display font-semibold text-sm text-gray-800 dark:text-gray-100">
            {lang === 'en'
              ? 'Python & Inno Setup Script Packager Suite'
              : '파이썬(Python) 및 Inno Setup 패키지 빌더 스위트'}
          </h3>
        </div>
        <span className="text-[11px] font-mono text-gray-500 dark:text-gray-400">
          {lang === 'en' ? 'Comments & Labels: English (EN)' : '주석 및 레이블: 한국어 (KO)'}
        </span>
      </div>

      <div className="space-y-4">
        {/* Dynamic naming for customized installers */}
        <div className="p-3 bg-blue-100/10 border border-blue-500/15 rounded-lg flex items-center justify-between gap-3 flex-wrap">
          <div className="space-y-1">
            <label
              htmlFor="input-desktop-name"
              className="block text-[11px] font-bold text-blue-400"
            >
              {lang === 'en' ? 'Target Application Name' : '빌드할 프로그램 이름 설정'}
            </label>
            <input
              type="text"
              id="input-desktop-name"
              value={desktopName}
              onChange={(e) => setDesktopName(e.target.value.replace(/[^a-zA-Z0-9_-]/g, '') || 'PowerController')}
              className="text-xs bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-200 font-mono"
              placeholder="PowerController"
            />
          </div>
          <Laptop className="w-8 h-8 text-blue-500/30 flex-shrink-0" />
        </div>

        {/* Informational Warning */}
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 flex gap-2.5">
          <ShieldAlert className="w-4.5 h-4.5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="text-[11px] text-amber-600 dark:text-amber-400 leading-normal">
            <strong>{lang === 'en' ? 'Why Python + Inno Setup is lightweight and reliable:' : '왜 파이썬(Python)과 Inno Setup 조합이 가장 안전하고 가벼울까요?'}</strong>
            <br />
            {lang === 'en'
              ? 'Chromium-wrapped desktop apps exceed 130MB in raw size. Tkinter Python builds compact native binaries (~8MB), and Inno Setup 6 packages multi-language wizards with silent firewall registration.'
              : 'Electron 등 Chromium 내장 앱은 파일 크기가 130MB를 넘지만, Tkinter 기반 Python 코드는 약 8MB 내외로 가볍고 빠르며 Inno Setup 6 스크립트로 다국어 설치 마법사 및 방화벽 규칙을 자동 구성할 수 있습니다.'}
          </div>
        </div>

        {/* Official Windows PC Release Center */}
        <div className="p-3.5 rounded-lg bg-blue-500/10 border border-blue-500/20 space-y-3">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <h4 className="text-[12px] font-bold text-blue-600 dark:text-blue-400 flex items-center gap-1.5 font-sans">
              <span>🚀</span>
              {lang === 'en' ? 'Official Windows PC Deployment & Release Center' : '공식 Windows PC 배포 및 설치 지원 센터'}
            </h4>
            <a
              href="https://github.com/AhBiYout-all/PowerController/releases"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] font-bold px-2.5 py-1 rounded bg-blue-600 text-white hover:bg-blue-500 transition-colors whitespace-nowrap shrink-0"
            >
              GitHub Releases
            </a>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-[10.5px]">
            <div className="p-2.5 rounded bg-gray-100 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 space-y-1">
              <div className="font-bold text-gray-900 dark:text-gray-100 flex items-center gap-1">
                <span>💻</span> {lang === 'en' ? 'Windows Official Installer (.exe)' : 'Windows 공식 설치 마법사 (.exe)'}
              </div>
              <p className="text-gray-500 dark:text-gray-400 text-[10px]">
                {lang === 'en' ? 'Inno Setup 6 multi-language installer with silent firewall rules' : 'Inno Setup 6 다국어 설치 마법사 및 방화벽 규칙 자동 등록'}
              </p>
              <div className="font-mono text-[10px] text-emerald-500 font-semibold tabular-nums">
                {safeName}_Setup_v{APP_VERSION}.exe
              </div>
            </div>
            <div className="p-2.5 rounded bg-gray-100 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 space-y-1">
              <div className="font-bold text-gray-900 dark:text-gray-100 flex items-center gap-1">
                <span>📡</span> {lang === 'en' ? 'Remote PC Network Commander' : '사내망 원격 PC 통합 제어 타워'}
              </div>
              <p className="text-gray-500 dark:text-gray-400 text-[10px]">
                {lang === 'en' ? 'Standalone network scheduler for LAN remote power control' : '사내 PC 원격 종료/재시작/절전 관제 콘솔'}
              </p>
              <div className="font-mono text-[10px] text-blue-500 font-semibold">
                PowerNetworkScheduler.exe
              </div>
            </div>
          </div>
        </div>

        {/* Script Format Selector Tabs: Python (.py) vs Inno Setup (.iss) */}
        <div className="flex items-center gap-1.5 p-1 bg-gray-200/70 dark:bg-gray-950 rounded-lg border border-gray-300/60 dark:border-gray-800">
          <button
            type="button"
            onClick={() => setActiveScriptTab('python')}
            className={`flex-1 py-1.5 px-3 rounded-md text-xs font-bold flex items-center justify-center gap-1.5 transition-colors cursor-pointer whitespace-nowrap ${
              activeScriptTab === 'python'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <FileCode2 className="w-3.5 h-3.5" />
            <span>{lang === 'en' ? `Python GUI Script (${safeName}.py)` : `파이썬 GUI 스크립트 (main.py)`}</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveScriptTab('inno')}
            className={`flex-1 py-1.5 px-3 rounded-md text-xs font-bold flex items-center justify-center gap-1.5 transition-colors cursor-pointer whitespace-nowrap ${
              activeScriptTab === 'inno'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <Package className="w-3.5 h-3.5" />
            <span>{lang === 'en' ? `Inno Setup 6 Script (${safeName}.iss)` : `Inno Setup 6 설치 스크립트 (.iss)`}</span>
          </button>
        </div>

        {/* Step 1: Dynamically Generated Source Script */}
        <div className="space-y-1.5 text-left">
          <div className="flex items-center justify-between text-xs flex-wrap gap-2">
            <span className="font-semibold text-gray-700 dark:text-gray-300">
              {activeScriptTab === 'python'
                ? lang === 'en'
                  ? `1. Generated Python GUI Script (${safeName}.py)`
                  : `1. 동적 생성된 파이썬 GUI 스크립트 (${safeName}.py)`
                : lang === 'en'
                ? `1. Generated Inno Setup 6 Script (${safeName}.iss)`
                : `1. 동적 생성된 Inno Setup 6 설치 스크립트 (${safeName}.iss)`}
            </span>
            <button
              id="btn-copy-generated-script"
              onClick={() => handleCopy('generatedScript', currentScriptText)}
              className="text-[11px] text-blue-600 dark:text-blue-400 flex items-center gap-1 hover:underline cursor-pointer font-bold whitespace-nowrap shrink-0"
            >
              {copiedId === 'generatedScript' ? (
                <Check className="w-3.5 h-3.5 text-green-500" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
              {copiedId === 'generatedScript'
                ? lang === 'en'
                  ? 'Copied!'
                  : '복사됨!'
                : lang === 'en'
                ? 'Copy Entire Script'
                : '스크립트 전체 복사'}
            </button>
          </div>
          <p className="text-[10.5px] text-gray-500 dark:text-gray-400 leading-normal font-sans">
            {activeScriptTab === 'python'
              ? lang === 'en'
                ? `Save this localized script as "main.py" or "${safeName}.py". Inline # comments and UI labels automatically match English.`
                : `아래 코드를 메모장이나 에디터에 붙여넣고 "main.py"로 저장하세요. 내부 # 주석과 모든 UI 레이블이 한국어로 자동 구성됩니다.`
              : lang === 'en'
              ? `Save this script as "${safeName}.iss" for Inno Setup Compiler 6. Default wizard language, license path, and inline ; comments automatically match English.`
              : `아래 코드를 "${safeName}.iss"로 저장한 뒤 Inno Setup 6로 컴파일하세요. 기본 마법사 언어, 라이선스 파일 및 ; 주석이 한국어로 자동 반영됩니다.`}
          </p>
          <pre className="text-[10.5px] font-mono p-3 bg-gray-950 rounded-md border border-gray-800 overflow-x-auto whitespace-pre text-slate-200 max-h-72 select-text">
            {currentScriptText}
          </pre>
        </div>

        {/* Step 2: Compile Command */}
        <div className="space-y-1.5 pt-2 border-t border-dashed border-gray-200/50 dark:border-gray-800/40 text-left">
          <div className="flex items-center justify-between text-xs flex-wrap gap-2">
            <span className="font-semibold text-gray-700 dark:text-gray-300">
              {activeScriptTab === 'python'
                ? lang === 'en'
                  ? '2. Standalone Executable Build Command (PyInstaller)'
                  : '2. 단일 EXE 실행 파일 컴파일 명령 (PyInstaller)'
                : lang === 'en'
                ? '2. Installer Build Command (Inno Setup 6 ISCC)'
                : '2. 설치 마법사(.exe) 컴파일 명령 (Inno Setup 6 ISCC)'}
            </span>
            <button
              id="btn-copy-compile-cmd"
              onClick={() => handleCopy('compileCmd', currentCompileCommand)}
              className="text-[11px] text-teal-600 dark:text-teal-400 flex items-center gap-1 hover:underline cursor-pointer font-bold whitespace-nowrap shrink-0"
            >
              {copiedId === 'compileCmd' ? (
                <Check className="w-3.5 h-3.5 text-green-500" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
              {copiedId === 'compileCmd'
                ? lang === 'en'
                  ? 'Copied!'
                  : '복사됨!'
                : lang === 'en'
                ? 'Copy Command'
                : '명령어 복사'}
            </button>
          </div>
          <pre className="text-[11px] font-mono p-2.5 bg-gray-950 text-emerald-400 rounded-md border border-gray-900 overflow-x-auto whitespace-pre no-scrollbar select-text">
            {currentCompileCommand}
          </pre>

          <div className="flex items-start gap-1.5 p-2 rounded bg-indigo-50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/30 text-left">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500 mt-0.5 flex-shrink-0" />
            <span className="text-[10.5px] text-indigo-700 dark:text-indigo-400 leading-relaxed font-sans">
              {activeScriptTab === 'python'
                ? lang === 'en'
                  ? `Once compiled, find your standalone portable binary "${safeName}.exe" inside the "dist" directory.`
                  : `빌드가 완료되면 dist 폴더 내부에 단독 실행 가능한 ${safeName}.exe 파일이 생성됩니다.`
                : lang === 'en'
                ? `Inno Setup outputs "${safeName}_Setup_v${APP_VERSION}.exe" inside the "dist" directory with pre-configured firewall rules.`
                : `컴파일이 완료되면 dist 폴더에 방화벽 규칙이 자동 등록되는 ${safeName}_Setup_v${APP_VERSION}.exe 설치 파일이 생성됩니다.`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
