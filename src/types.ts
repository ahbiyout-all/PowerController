/**
 * Types for the Power Shutdown & Restart Controller app
 */

export const APP_VERSION = '2.9.2';
export const APP_RELEASE_DATE = '2026-09-26';
export const DEFAULT_PORT = 3032;
export const DEVELOPER_NAME = 'AhBiYout';
export const GITHUB_REPO_OWNER = 'AhBiYout-all';
export const GITHUB_REPO_NAME = 'PowerController';
export const GITHUB_REPO_URL = `https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}`;
export const GITHUB_RELEASES_URL = `https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/releases`;
export const OFFICIAL_BLOG_URL = 'https://ahbiyoutvibe.blogspot.com/';
export const COMPANY_URL = 'https://www.cisnet.co.kr';

export type PowerMode = 'shutdown' | 'restart' | 'sleep' | 'screenoff' | 'logout' | 'alarm';

export type TimerState = 'idle' | 'running' | 'paused' | 'complete';

export type ThemeType = 'dark' | 'gray' | 'white' | 'beige';

export type SoundTheme = 'classic' | 'marimba' | 'crystal' | 'scifi' | 'westminster' | 'urgent' | 'bubble';

export type ExplorerFolder = 'timer' | 'scheduler' | 'packager' | 'command' | 'favorites' | 'logs';

export interface FavoritePreset {
  id: string;
  label: string;
  mode: PowerMode;
  durationSeconds: number;
}

export interface HistoryLog {
  id: string;
  mode: PowerMode;
  scheduledTime: Date; // date triggered or configured
  status: 'completed' | 'cancelled' | 'pending';
}

export type ScheduleType = 'once' | 'daily' | 'weekly' | 'interval';

export interface PowerSchedule {
  id: string;
  label: string;
  type: ScheduleType;
  mode: PowerMode;
  time?: string; // "HH:MM" form
  days?: number[]; // [0-6] 0 = Sunday, 1 = Monday ... 6 = Saturday
  intervalMinutes?: number; // e.g., repeat every 90 minutes
  forceCloseApps: boolean; // shutdown with /f
  warningNotification: boolean; // warn 1 min prior
  isActive: boolean;
  lastExecuted?: string; // timestamp string
  createdAt: string;
}
