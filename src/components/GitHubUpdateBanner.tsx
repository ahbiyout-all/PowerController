import React, { useState, useEffect } from 'react';
import {
  APP_VERSION,
  APP_RELEASE_DATE,
  GITHUB_REPO_OWNER,
  GITHUB_REPO_NAME,
  GITHUB_REPO_URL,
  GITHUB_RELEASES_URL
} from '../types';
import {
  Download,
  ExternalLink,
  RefreshCw,
  Copy,
  Check,
  Sparkles,
  ShieldCheck,
  Clock,
  Github,
  X,
  AlertCircle
} from 'lucide-react';

export interface ReleaseInfo {
  tagName: string;
  name: string;
  publishedAt: string;
  htmlUrl: string;
  body: string;
  downloadUrl?: string;
}

function parseSemver(ver: string): number[] {
  const clean = ver.replace(/^[vV]/, '').trim();
  const parts = clean.split('.').map(p => parseInt(p, 10) || 0);
  while (parts.length < 3) parts.push(0);
  return parts.slice(0, 3);
}

export function isNewer(latestVer: string, currentVer: string): boolean {
  const l = parseSemver(latestVer);
  const c = parseSemver(currentVer);
  for (let i = 0; i < 3; i++) {
    if (l[i] > c[i]) return true;
    if (l[i] < c[i]) return false;
  }
  return false;
}

interface UpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang?: 'ko' | 'en';
  latestRelease?: ReleaseInfo | null;
  onRefresh?: () => void;
  isChecking?: boolean;
}

export const UpdateModal: React.FC<UpdateModalProps> = ({
  isOpen,
  onClose,
  lang = 'ko',
  latestRelease,
  onRefresh,
  isChecking = false
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const currentVer = `v${APP_VERSION}`;
  const latestVer = latestRelease?.tagName || `v${APP_VERSION}`;
  const hasUpdate = isNewer(latestVer, APP_VERSION);
  const releaseName = latestRelease?.name || `PowerController ${latestVer}`;
  const releaseDate = latestRelease?.publishedAt
    ? new Date(latestRelease.publishedAt).toLocaleDateString(lang === 'en' ? 'en-US' : 'ko-KR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    : APP_RELEASE_DATE;

  const installerFilename = `PowerController_Setup_${latestVer}.exe`;
  const downloadUrl =
    latestRelease?.downloadUrl ||
    `https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/releases/download/${latestVer}/${installerFilename}`;
  const repoFullUrl = `https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}`;
  const releasesFullUrl = `https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/releases`;

  const handleCopyRepoUrl = () => {
    navigator.clipboard.writeText(repoFullUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden text-slate-100 flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Top Gradient Header */}
        <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 p-5 text-white flex items-start justify-between relative overflow-hidden">
          <div className="absolute -right-6 -bottom-6 w-32 h-32 bg-white/10 rounded-full blur-2xl pointer-events-none" />
          
          <div className="flex items-center gap-3 z-10">
            <div className="w-11 h-11 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center shadow-inner border border-white/30 text-2xl">
              🚀
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/25 border border-white/40 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-amber-300 animate-spin" />
                  {hasUpdate ? (lang === 'en' ? 'New Update Available' : '새 업데이트 발견') : (lang === 'en' ? 'Version Information' : '버전 및 업데이트 정보')}
                </span>
                {hasUpdate && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500 text-white animate-pulse">
                    {lang === 'en' ? 'UPDATE' : '업데이트 권장'}
                  </span>
                )}
              </div>
              <h2 className="text-lg font-bold text-white mt-1 flex items-center gap-1.5">
                PowerController {hasUpdate ? latestVer : currentVer}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="z-10 p-1.5 text-white/80 hover:text-white rounded-lg hover:bg-white/20 transition cursor-pointer"
            title={lang === 'en' ? 'Close' : '닫기'}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4 overflow-y-auto flex-1 text-xs sm:text-sm">
          {/* 1. Version Comparison Card */}
          <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 block">
                {lang === 'en' ? 'Installed Version' : '현재 설치된 버전'}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold text-slate-200 font-mono">
                  {currentVer}
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {lang === 'en' ? 'Current' : '현재 앱'}
                </span>
              </div>
            </div>

            <div className="space-y-1 border-l border-slate-800/80 pl-3">
              <span className="text-[11px] font-semibold text-slate-400 block">
                {lang === 'en' ? 'Latest Release Version' : 'GitHub 최신 릴리스'}
              </span>
              <div className="flex items-center gap-2">
                <span className={`text-base font-bold font-mono ${hasUpdate ? 'text-emerald-400' : 'text-blue-400'}`}>
                  {latestVer}
                </span>
                {hasUpdate ? (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 font-bold">
                    {lang === 'en' ? 'New' : '최신 버전'}
                  </span>
                ) : (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-700">
                    {lang === 'en' ? 'Up to date' : '최신 상태'}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* 2. GitHub Repository & Path Information Card */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Github className="w-4 h-4 text-slate-400" />
                {lang === 'en' ? 'Official GitHub Repository' : '공식 깃허브(GitHub) 저장소 및 배포 경로'}
              </span>
              <button
                onClick={handleCopyRepoUrl}
                className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer border border-slate-700"
                title={lang === 'en' ? 'Copy URL' : 'URL 복사'}
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span className="text-emerald-400 font-semibold">{lang === 'en' ? 'Copied' : '복사됨'}</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3 text-slate-400" />
                    <span>{lang === 'en' ? 'Copy URL' : '주소 복사'}</span>
                  </>
                )}
              </button>
            </div>

            <div className="p-2 rounded-lg bg-slate-900 border border-slate-800/80 font-mono text-[11px] text-blue-300 break-all select-all">
              {repoFullUrl}
            </div>

            <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-1">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-500" />
                {lang === 'en' ? 'Release Date: ' : '릴리스 출시일: '}
                <strong className="text-slate-300">{releaseDate}</strong>
              </span>
              <a
                href={releasesFullUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 underline flex items-center gap-1"
              >
                <span>{lang === 'en' ? 'View Releases History' : '전체 릴리스 이력 보기'}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* 3. Patch Notes & Changelog Area */}
          <div className="space-y-1.5">
            <span className="font-semibold text-slate-300 text-xs block">
              {lang === 'en' ? 'Release Details & Changelog' : '주요 변경 내역 및 패치 노트'}
            </span>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 max-h-36 overflow-y-auto font-mono whitespace-pre-wrap leading-relaxed shadow-inner">
              {latestRelease?.body ||
                (lang === 'en'
                  ? `• Official Windows Installer (Inno Setup 6) release.\n• High-precision hardware timer & background sleep guard.\n• Multi-level silent process force kill & file unlock pipeline.\n• Single Source of Truth versioning synchronization (v${APP_VERSION}).`
                  : `• Windows 공식 설치 마법사(Inno Setup 6) 릴리스.\n• 초정밀 하드웨어 타이머 및 백그라운드 절전 가드 탑재.\n• 원격 무인 설치 시 프로세스 무음 강제 종료 및 파일 락 자동 해제.\n• 3단계 SemVer 규약 및 버전 정보 일괄 동기화(v${APP_VERSION}).`)}
            </div>
          </div>
        </div>

        {/* Action Buttons Footer */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex flex-col sm:flex-row gap-2.5">
          {/* Main Download / Update Button */}
          <a
            href={downloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-center text-xs sm:text-sm transition flex items-center justify-center gap-2 shadow-lg shadow-blue-600/30 cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>
              {lang === 'en'
                ? `Download Windows Installer (${installerFilename})`
                : `Windows 공식 설치 프로그램 다운로드 (${installerFilename})`}
            </span>
          </a>

          <div className="flex gap-2">
            {/* Refresh Check Button */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isChecking}
                className="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition text-xs font-semibold flex items-center gap-1.5 border border-slate-700 disabled:opacity-50 cursor-pointer"
                title={lang === 'en' ? 'Check for updates again' : '업데이트 다시 확인'}
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isChecking ? 'animate-spin text-blue-400' : ''}`} />
                <span className="hidden sm:inline">{lang === 'en' ? 'Check Again' : '다시 확인'}</span>
              </button>
            )}

            {/* GitHub Releases Web Button */}
            <a
              href={latestRelease?.htmlUrl || releasesFullUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition text-xs font-semibold flex items-center gap-1.5 border border-slate-700"
            >
              <Github className="w-3.5 h-3.5" />
              <span>{lang === 'en' ? 'GitHub' : '깃허브'}</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>

            {/* Close / Later Button */}
            <button
              onClick={onClose}
              className="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition text-xs font-medium border border-slate-700 cursor-pointer"
            >
              {lang === 'en' ? 'Close' : '닫기'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export const GitHubUpdateBanner: React.FC<{ lang?: 'ko' | 'en' }> = ({ lang = 'ko' }) => {
  const [latestRelease, setLatestRelease] = useState<ReleaseInfo | null>(null);
  const [hasUpdate, setHasUpdate] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const checkUpdate = async () => {
    setIsChecking(true);
    try {
      const res = await fetch(`https://api.github.com/repos/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/releases/latest`, {
        headers: { Accept: 'application/vnd.github.v3+json' },
      });
      if (res.ok) {
        const data = await res.json();
        const tag = (data.tag_name || '').trim();
        const release: ReleaseInfo = {
          tagName: tag,
          name: data.name || tag,
          publishedAt: data.published_at || '',
          htmlUrl: data.html_url || GITHUB_RELEASES_URL,
          body: data.body || '',
          downloadUrl: `https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/releases/download/${tag}/PowerController_Setup_${tag}.exe`,
        };
        setLatestRelease(release);
        if (isNewer(tag, APP_VERSION)) {
          setHasUpdate(true);
          setDismissed(false);
          // Auto open modal on detection
          setShowModal(true);
        }
      }
    } catch {
      // Offline or rate limited - ignore silently
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkUpdate();
  }, []);

  return (
    <>
      {/* Real-time Update Notification Top Bar if update found */}
      {hasUpdate && !dismissed && latestRelease && (
        <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white px-4 py-2 text-xs flex items-center justify-between shadow-md z-40 relative animate-in fade-in slide-in-from-top-2 duration-300">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-white/20 text-white font-bold text-[11px] animate-pulse">
              🔔
            </span>
            <span className="font-semibold">
              {lang === 'en'
                ? `New update available: ${latestRelease.tagName} (Current: v${APP_VERSION})`
                : `새로운 최신 버전이 출시되었습니다: ${latestRelease.tagName} (현재 실행 중: v${APP_VERSION})`}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowModal(true)}
              className="px-2.5 py-1 rounded bg-white text-indigo-700 font-bold hover:bg-slate-100 transition shadow-sm text-[11px] cursor-pointer flex items-center gap-1"
            >
              <span>🚀</span>
              <span>{lang === 'en' ? 'Update Details' : '업데이트 팝업 열기'}</span>
            </button>
            <a
              href={latestRelease.htmlUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-2.5 py-1 rounded bg-white/20 hover:bg-white/30 text-white font-medium transition text-[11px]"
            >
              GitHub ➔
            </a>
            <button
              onClick={() => setDismissed(true)}
              title={lang === 'en' ? 'Dismiss' : '닫기'}
              className="p-1 hover:bg-white/20 rounded text-white/80 hover:text-white transition cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Full Update Notification Popup Modal */}
      <UpdateModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        lang={lang}
        latestRelease={latestRelease}
        onRefresh={checkUpdate}
        isChecking={isChecking}
      />
    </>
  );
};
