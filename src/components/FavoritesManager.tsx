import React, { useState, useEffect } from 'react';
import { Star, Plus, Trash2, Edit2, ShieldAlert, Clock, Power, Play, RotateCw, Moon, Laptop, LogOut } from 'lucide-react';
import { FavoritePreset, PowerMode, ThemeType } from '../types';

interface FavoritesProps {
  onFavSelect: (mode: PowerMode, durationSeconds: number) => void;
  lang?: 'ko' | 'en';
  theme?: ThemeType;
}

const favThemeConfigs = {
  dark: {
    container: 'bg-[#181a24] border-[#2d3142]/60 text-[#e1e4ed]',
    form: 'bg-[#1a1d29] border-[#2d3142]/60',
    input: 'bg-black/40 text-white border-gray-700 focus:ring-blue-500',
    card: 'bg-[#1a1d29] border-[#2d3142]/60 hover:border-blue-500 text-[#e1e4ed]',
    cardText: 'text-gray-100 font-semibold',
    cardBadge: 'bg-gray-800 border-gray-700 text-gray-200'
  },
  gray: {
    container: 'bg-[#242f41] border-[#475569] text-[#f8fafc]',
    form: 'bg-[#1e293b] border-[#475569]',
    input: 'bg-[#1e293b] text-[#f8fafc] border-[#475569] focus:ring-blue-400',
    card: 'bg-[#1e293b] border-[#475569] hover:border-blue-400 text-[#f8fafc]',
    cardText: 'text-slate-100 font-bold',
    cardBadge: 'bg-[#475569] border-[#475569] text-slate-100 font-semibold'
  },
  beige: {
    container: 'bg-[#fdfbf7] border-[#c8bcaa] text-[#2c2217]',
    form: 'bg-[#f5eee4] border-[#c8bcaa]',
    input: 'bg-white text-[#2c2217] border-[#c8bcaa] focus:ring-[#6e5d47] font-semibold',
    card: 'bg-[#f5eee4] border-[#c8bcaa] hover:border-[#584835] text-[#2c2217]',
    cardText: 'text-[#2c2217] font-extrabold',
    cardBadge: 'bg-[#e8ded0] border-[#c8bcaa] text-[#5c4d38] font-bold'
  }
};

const get_default_favorites = (lang: 'ko' | 'en'): FavoritePreset[] => [
  { id: 'fav-1', label: lang === 'ko' ? '영화 종료 예약 (2시간)' : 'Movie Shutdown Timer (2h)', mode: 'shutdown', durationSeconds: 7200 },
  { id: 'fav-2', label: lang === 'ko' ? '점심시간 고속 재기동' : 'Lunch Break Quick Restart', mode: 'restart', durationSeconds: 3600 },
  { id: 'fav-3', label: lang === 'ko' ? '야간 즉시 절전 타이머 (30분)' : 'Night Sleep Bedtime (30m)', mode: 'sleep', durationSeconds: 1800 },
  { id: 'fav-4', label: lang === 'ko' ? '회의 미팅 화면 끄기 (15분)' : 'Meeting Mode Screen Off (15m)', mode: 'screenoff', durationSeconds: 900 },
  { id: 'fav-5', label: lang === 'ko' ? '작업 휴식 계정 로그아웃' : 'Log out for break (2m)', mode: 'logout', durationSeconds: 120 }
];

const get_mode_meta = (lang: 'ko' | 'en'): Record<PowerMode, { label: string; bg: string; border: string; text: string; icon: any; glow: string }> => ({
  shutdown: { label: lang === 'en' ? 'Shutdown' : '종료', bg: 'bg-rose-500/10 dark:bg-rose-950/20', border: 'border-rose-500/30 dark:border-rose-500/20', text: 'text-rose-500', icon: Power, glow: 'group-hover:border-rose-400' },
  restart: { label: lang === 'en' ? 'Restart' : '재시작', bg: 'bg-blue-500/10 dark:bg-blue-950/20', border: 'border-blue-500/30 dark:border-blue-500/20', text: 'text-blue-500', icon: RotateCw, glow: 'group-hover:border-blue-400' },
  sleep: { label: lang === 'en' ? 'Sleep' : '절전', bg: 'bg-purple-500/10 dark:bg-purple-950/20', border: 'border-purple-500/30 dark:border-purple-500/20', text: 'text-purple-500', icon: Moon, glow: 'group-hover:border-purple-400' },
  screenoff: { label: lang === 'en' ? 'Screen Off' : '화면끄기', bg: 'bg-amber-500/10 dark:bg-amber-950/20', border: 'border-amber-500/30 dark:border-amber-500/20', text: 'text-amber-500', icon: Laptop, glow: 'group-hover:border-amber-400' },
  logout: { label: lang === 'en' ? 'Logout' : '로그아웃', bg: 'bg-emerald-500/10 dark:bg-emerald-950/20', border: 'border-emerald-500/30 dark:border-emerald-500/20', text: 'text-emerald-500', icon: LogOut, glow: 'group-hover:border-emerald-400' },
  alarm: { label: lang === 'en' ? 'Alarm' : '알람', bg: 'bg-pink-500/10 dark:bg-pink-950/20', border: 'border-pink-500/30 dark:border-pink-500/20', text: 'text-pink-500', icon: Clock, glow: 'group-hover:border-pink-400' },
});

export default function FavoritesManager({ onFavSelect, lang = 'ko', theme = 'dark' }: FavoritesProps) {
  const currentFavTheme = favThemeConfigs[theme] || favThemeConfigs.dark;
  const [favorites, setFavorites] = useState<FavoritePreset[]>([]);
  const [newLabel, setNewLabel] = useState('');
  const [newMode, setNewMode] = useState<PowerMode>('shutdown');
  const [hours, setHours] = useState(0);
  const [minutes, setMinutes] = useState(15);
  const [seconds, setSeconds] = useState(0);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingFavId, setEditingFavId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const mode_meta = get_mode_meta(lang);

  // Load from local storage
  useEffect(() => {
    try {
      const stored = localStorage.getItem('system_power_favorites');
      if (stored) {
        setFavorites(JSON.parse(stored));
      } else {
        const defaults = get_default_favorites(lang);
        setFavorites(defaults);
        localStorage.setItem('system_power_favorites', JSON.stringify(defaults));
      }
    } catch (e) {
      setFavorites(get_default_favorites(lang));
    }
  }, [lang]);

  // Save to local storage helper
  const saveFavorites = (updatedList: FavoritePreset[]) => {
    setFavorites(updatedList);
    localStorage.setItem('system_power_favorites', JSON.stringify(updatedList));
  };

  const resetFavForm = () => {
    setNewLabel('');
    setHours(0);
    setMinutes(15);
    setSeconds(0);
    setEditingFavId(null);
    setShowAddForm(false);
    setErrorMsg('');
  };

  const handleStartEdit = (fav: FavoritePreset, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent launching
    setEditingFavId(fav.id);
    setNewLabel(fav.label);
    setNewMode(fav.mode);
    const h = Math.floor(fav.durationSeconds / 3600);
    const m = Math.floor((fav.durationSeconds % 3600) / 60);
    const s = fav.durationSeconds % 60;
    setHours(h);
    setMinutes(m);
    setSeconds(s);
    setShowAddForm(true);
  };

  const handleAddFavorite = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    const totalSeconds = (hours * 3600) + (minutes * 60) + seconds;
    if (totalSeconds <= 0) {
      setErrorMsg(lang === 'en' ? 'Please set time greater than 0 seconds.' : '시간을 0초 이상으로 설정해주세요.');
      return;
    }

    const trimmedLabel = newLabel.trim();
    if (!trimmedLabel) {
      setErrorMsg(lang === 'en' ? 'Please enter a name for the favorite.' : '즐겨찾기 이름을 입력해주세요.');
      return;
    }

    if (editingFavId) {
      const updated = favorites.map(f => {
        if (f.id === editingFavId) {
          return {
            ...f,
            label: trimmedLabel,
            mode: newMode,
            durationSeconds: totalSeconds
          };
        }
        return f;
      });
      saveFavorites(updated);
      resetFavForm();
    } else {
      const newFav: FavoritePreset = {
        id: `fav-${Date.now()}`,
        label: trimmedLabel,
        mode: newMode,
        durationSeconds: totalSeconds
      };

      const updated = [newFav, ...favorites];
      saveFavorites(updated);
      resetFavForm();
    }
  };

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Avoid triggering the timer launch
    const filtered = favorites.filter(fav => fav.id !== id);
    saveFavorites(filtered);
  };

  const formatDuration = (totalSec: number) => {
    const h = Math.floor(totalSec / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;

    const parts = [];
    if (h > 0) parts.push(`${h}${lang === 'en' ? 'h' : '시간'}`);
    if (m > 0) parts.push(`${m}${lang === 'en' ? 'm' : '분'}`);
    if (s > 0) parts.push(`${s}${lang === 'en' ? 's' : '초'}`);
    return parts.join(' ') || (lang === 'en' ? '0s' : '0초');
  };

  const quickSet = (lbl: string, h: number, m: number, s: number) => {
    setNewLabel(lbl);
    setHours(h);
    setMinutes(m);
    setSeconds(s);
  };

  return (
    <div className={`rounded-xl border p-4 transition-all duration-300 ${currentFavTheme.container}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5">
          <Star className="w-4.5 h-4.5 text-yellow-500 fill-yellow-500" />
          <h3 className="font-display font-semibold text-sm">
            {lang === 'en' ? 'Saved Favorites' : '자주 쓰는 시간 (즐겨찾기)'}
          </h3>
        </div>
        
        <button
          id="btn-toggle-add-fav"
          onClick={() => setShowAddForm(!showAddForm)}
          className="text-xs flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline font-medium cursor-pointer"
        >
          {showAddForm ? (lang === 'en' ? 'Collapse' : '접기') : (lang === 'en' ? 'Add New' : '추가하기')}
          <Plus className={`w-3.5 h-3.5 transition-transform duration-200 ${showAddForm ? 'rotate-45' : ''}`} />
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleAddFavorite} className={`mb-4 p-3.5 rounded-lg border space-y-3 ${currentFavTheme.form}`}>
          <div>
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1.5">
              {lang === 'en' ? 'Select Power Action Mode' : '동작 모드 선택'}
            </label>
            <div className="grid grid-cols-5 gap-1 text-[10.5px]">
              {(Object.keys(mode_meta) as PowerMode[]).map((m) => {
                const meta = mode_meta[m];
                const Icon = meta.icon;
                const isSelected = newMode === m;
                return (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setNewMode(m)}
                    className={`py-2 px-1 rounded-lg font-semibold border flex flex-col items-center justify-center gap-1 cursor-pointer transition-all ${
                      isSelected
                        ? `${meta.bg} ${meta.border} ${meta.text} scale-[1.03] font-bold`
                        : `${theme === 'beige' ? 'bg-[#ebe2d4] border-[#dfd5c6] text-[#4a3e2b]' : 'bg-white dark:bg-gray-900 border-gray-200/60 dark:border-gray-850/60 text-gray-500 dark:text-gray-400'} hover:text-gray-800 dark:hover:text-gray-200`
                    }`}
                  >
                    <Icon className="w-4 h-4 animate-pulse" />
                    <span className="text-[9.5px] leading-none">{meta.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
              {lang === 'en' ? 'Favorite Name / Memo' : '즐겨찾기 별칭 (메모)'}
            </label>
            <input
              type="text"
              id="input-fav-label"
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              placeholder={lang === 'en' ? 'e.g. Turn off after movie' : '예: 영화 다 보면 종료'}
              maxLength={22}
              className={`w-full text-xs px-2.5 py-1.5 rounded-md border focus:outline-none focus:ring-1 ${currentFavTheme.input}`}
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
              {lang === 'en' ? 'Target Timer Duration' : '목표 시간 설정'}
            </label>
            <div className="flex items-center gap-1.5">
              <div className="flex flex-col items-center">
                <input
                  type="number"
                  id="input-fav-h"
                  min={0}
                  max={23}
                  value={hours}
                  onChange={(e) => setHours(Math.max(0, parseInt(e.target.value) || 0))}
                  className={`w-12 text-center text-xs p-1 rounded-md border focus:outline-none ${currentFavTheme.input}`}
                />
                <span className="text-[9px] text-gray-400 mt-0.5">{lang === 'en' ? 'Hours' : '시간'}</span>
              </div>
              <span className="text-gray-400 text-xs">:</span>
              <div className="flex flex-col items-center">
                <input
                  type="number"
                  id="input-fav-m"
                  min={0}
                  max={59}
                  value={minutes}
                  onChange={(e) => setMinutes(Math.max(0, parseInt(e.target.value) || 0))}
                  className={`w-12 text-center text-xs p-1 rounded-md border focus:outline-none ${currentFavTheme.input}`}
                />
                <span className="text-[9px] text-gray-400 mt-0.5">{lang === 'en' ? 'Mins' : '분'}</span>
              </div>
              <span className="text-gray-400 text-xs">:</span>
              <div className="flex flex-col items-center">
                <input
                  type="number"
                  id="input-fav-s"
                  min={0}
                  max={59}
                  value={seconds}
                  onChange={(e) => setSeconds(Math.max(0, parseInt(e.target.value) || 0))}
                  className={`w-12 text-center text-xs p-1 rounded-md border focus:outline-none ${currentFavTheme.input}`}
                />
                <span className="text-[9px] text-gray-400 mt-0.5">{lang === 'en' ? 'Secs' : '초'}</span>
              </div>

              {/* Quick helper shortcuts */}
              <div className="flex flex-wrap gap-1 ml-auto">
                <button
                  type="button"
                  id="btn-quick-30m"
                  onClick={() => quickSet(lang === 'en' ? '30m Nap sleep' : '30분간 취침', 0, 30, 0)}
                  className="px-1.5 py-0.5 border border-dashed rounded text-[9px] hover:bg-gray-100 dark:hover:bg-gray-900 text-gray-500 cursor-pointer"
                >
                  30m
                </button>
                <button
                  type="button"
                  id="btn-quick-1h"
                  onClick={() => quickSet(lang === 'en' ? 'Movie Time (90m)' : '영화 1편 (90분)', 1, 30, 0)}
                  className="px-1.5 py-0.5 border border-dashed rounded text-[9px] hover:bg-gray-100 dark:hover:bg-gray-900 text-gray-500 cursor-pointer"
                >
                  90m
                </button>
                <button
                  type="button"
                  id="btn-quick-2h"
                  onClick={() => quickSet(lang === 'en' ? 'Deep sleep shutdown' : '완비수면 종료', 2, 0, 0)}
                  className="px-1.5 py-0.5 border border-dashed rounded text-[9px] hover:bg-gray-100 dark:hover:bg-gray-900 text-gray-500 cursor-pointer"
                >
                  2h
                </button>
              </div>
            </div>
          </div>

          {errorMsg && (
            <p className="text-[10px] text-rose-500 font-medium flex items-center gap-1">
              <ShieldAlert className="w-3 h-3" /> {errorMsg}
            </p>
          )}

          {editingFavId ? (
            <div className="flex gap-2">
              <button
                type="submit"
                id="btn-submit-fav"
                className="flex-1 text-xs font-semibold py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-md transition-all cursor-pointer shadow shadow-purple-500/20"
              >
                {lang === 'en' ? 'Save Changes' : '즐겨찾기 수정 완료'}
              </button>
              <button
                type="button"
                id="btn-cancel-fav"
                onClick={resetFavForm}
                className="text-xs font-semibold py-2 px-4.5 bg-gray-500 dark:bg-gray-800 hover:bg-gray-600 text-white rounded-md transition-all cursor-pointer"
              >
                {lang === 'en' ? 'Cancel' : '취소'}
              </button>
            </div>
          ) : (
            <button
              type="submit"
              id="btn-submit-fav"
              className="w-full text-xs font-semibold py-2 bg-blue-600 dark:bg-blue-500 hover:bg-blue-500 text-white rounded-md transition-all cursor-pointer shadow shadow-blue-500/20"
            >
              {lang === 'en' ? 'Create Favorite' : '즐겨찾기 잠금 폴더에 생성'}
            </button>
          )}
        </form>
      )}

      {favorites.length === 0 ? (
        <div className="text-center py-6 text-xs text-gray-400">
          {lang === 'en' ? 'No favorites registered. Keep your frequent configurations here!' : '등록된 즐겨찾기 목록이 없습니다. 자주 쓰는 시간을 잠금해두세요!'}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-2">
          {favorites.map((fav) => {
            const meta = mode_meta[fav.mode] || mode_meta.shutdown;
            const Icon = meta.icon;
            return (
              <div
                key={fav.id}
                id={`fav-card-${fav.id}`}
                onClick={() => onFavSelect(fav.mode, fav.durationSeconds)}
                className={`group flex items-center justify-between p-2.5 rounded-lg border transition-all cursor-pointer select-none ${currentFavTheme.card}`}
                title={lang === 'en' ? 'Click to trigger this timer.' : '클릭 시 즉시 이 타이머를 실행합니다.'}
              >
                <div className="flex items-center gap-2">
                  <div className={`p-1.5 rounded-md ${meta.bg} ${meta.text}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  
                  <div className="text-left">
                    <h4 className={`text-xs font-semibold uppercase tracking-tight line-clamp-1 ${currentFavTheme.cardText}`}>
                      {fav.label}
                    </h4>
                    <div className="flex items-center gap-1.5 text-[10px] text-gray-400 mt-0.5">
                      <span className={`font-mono px-1.5 py-0.5 rounded border ${currentFavTheme.cardBadge}`}>
                        {meta.label}
                      </span>
                      <span>•</span>
                      <span className="font-semibold text-blue-500 dark:text-blue-400 font-mono text-[10.5px]">{formatDuration(fav.durationSeconds)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <span className="opacity-0 group-hover:opacity-100 transition-opacity text-[10.5px] font-semibold text-blue-600 dark:text-blue-400 flex items-center gap-0.5 mr-1 bg-blue-50/55 dark:bg-blue-950/30 px-1.5 py-0.5 rounded border border-blue-100 dark:border-blue-900/40 pointer-events-none">
                    <Play className="w-2.5 h-2.5 fill-blue-600 dark:fill-blue-400" />
                    {lang === 'en' ? 'Trigger Now' : '즉시 타이머 시작'}
                  </span>
                  
                  <button
                    id={`btn-edit-fav-${fav.id}`}
                    onClick={(e) => handleStartEdit(fav, e)}
                    className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-955 text-gray-400 hover:text-amber-500 transition-colors"
                    title={lang === 'en' ? 'Edit Favorite' : '즐겨찾기 수정'}
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>

                  <button
                    id={`btn-delete-fav-${fav.id}`}
                    onClick={(e) => handleDelete(fav.id, e)}
                    className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-955 text-gray-400 hover:text-rose-500 transition-colors"
                    title={lang === 'en' ? 'Delete Favorite' : '즐겨찾기 삭제'}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
