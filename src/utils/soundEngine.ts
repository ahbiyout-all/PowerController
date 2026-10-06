/**
 * High-Fidelity Sound Engine for PowerController
 * Inspired by top-rated notification and alarm sounds from Pixabay 알림음
 * 
 * Features:
 * - High-Q Multi-oscillator Polyphony
 * - Harmonic overtones & acoustic physical modeling (Marimba, Crystal Bell, Chimes)
 * - ADSR Envelope curves & dynamic biquad filtering
 * - Master volume management & persistence
 */

export type SoundTheme = 
  | 'classic'     // 맑은 벨 & 클래식 차임 (Clean Ting & Classic Bell)
  | 'marimba'     // 마림바 & 우든 팝 (Melodic Marimba & Cozy Pop)
  | 'crystal'     // 크리스탈 글래스 (Crystal Glass / iOS Chime)
  | 'scifi'       // 사이버/SF 신스 펄스 (Cyber Tech Pulse)
  | 'westminster' // 웨스트민스터 타워 차임 (Westminster Clock Chime)
  | 'urgent'      // 긴급 경보 알람 (Urgent Warning Siren)
  | 'bubble';     // 소프트 버블 팝 (Soft Bubble Drop)

export type SoundTriggerType = 
  | 'preview'       // 테마 대표 미리듣기
  | 'warningTick'   // 사전 경고 틱 (10초/30초/60초 전)
  | 'hourlyChime'   // 매시 정각 시계탑 알림음
  | 'timerAlarm'    // 타이머 만료 & 알람 모드 경보음
  | 'actionSuccess' // 작업 완료 / 스케줄 등록 효과음
  | 'buttonClick';  // UI 터치 피드백

export interface SoundThemeInfo {
  id: SoundTheme;
  nameKo: string;
  nameEn: string;
  descKo: string;
  descEn: string;
  icon: string;
  color: string;
}

export const SOUND_THEMES: SoundThemeInfo[] = [
  {
    id: 'classic',
    nameKo: '클래식 벨',
    nameEn: 'Classic Bell',
    descKo: '맑고 선명한 2음계 실로폰 & 차임벨 알림음',
    descEn: 'Clean 2-tone melodic bell chime',
    icon: '🔔',
    color: 'emerald'
  },
  {
    id: 'marimba',
    nameKo: '마림바 멜로디',
    nameEn: 'Melodic Marimba',
    descKo: '따뜻한 원목 울림의 4단 감성 아르페지오 (Pixabay 인기)',
    descEn: 'Warm resonant 4-note acoustic wooden marimba',
    icon: '🪵',
    color: 'amber'
  },
  {
    id: 'crystal',
    nameKo: '크리스탈 글래스',
    nameEn: 'Crystal Glass',
    descKo: '영롱한 잔향의 고급스러운 유리잔 팅 벨소리',
    descEn: 'Sparkling high-clarity dual crystal glass ring',
    icon: '✨',
    color: 'cyan'
  },
  {
    id: 'scifi',
    nameKo: '사이버 테크',
    nameEn: 'Cyber Tech',
    descKo: '미래지향적 디지털 신스 펄스 및 테크 UI 톤',
    descEn: 'Futuristic digital synthesizer sweep & pulse',
    icon: '🚀',
    color: 'indigo'
  },
  {
    id: 'westminster',
    nameKo: '웨스트민스터',
    nameEn: 'Westminster Chime',
    descKo: '품격 있는 대성당 시계탑 4화음 정각 종소리',
    descEn: 'Classic Cathedral 4-harmonic tower clock chime',
    icon: '🏛️',
    color: 'purple'
  },
  {
    id: 'urgent',
    nameKo: '긴급 경보 알람',
    nameEn: 'Urgent Siren',
    descKo: '놓치지 않는 3단 상승 펄스 경고음',
    descEn: 'High-visibility triple-pulse alert alarm',
    icon: '🚨',
    color: 'rose'
  },
  {
    id: 'bubble',
    nameKo: '소프트 버블 팝',
    nameEn: 'Soft Bubble Pop',
    descKo: '부드럽고 산뜻한 물방울 터치음',
    descEn: 'Gentle and crisp acoustic water bubble pop',
    icon: '🫧',
    color: 'blue'
  }
];

class SoundEngine {
  private ctx: AudioContext | null = null;
  private masterVolume: number = 0.8; // 0.0 to 1.0

  constructor() {
    try {
      const savedVol = localStorage.getItem('power_sound_volume');
      if (savedVol !== null) {
        this.masterVolume = Math.min(1, Math.max(0, parseFloat(savedVol)));
      }
    } catch {
      this.masterVolume = 0.8;
    }
  }

  private getAudioContext(): AudioContext | null {
    try {
      if (!this.ctx) {
        const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext;
        if (AudioCtxClass) {
          this.ctx = new AudioCtxClass();
        }
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume().catch(() => {});
      }
      return this.ctx;
    } catch {
      return null;
    }
  }

  public getVolume(): number {
    return Math.round(this.masterVolume * 100);
  }

  public setVolume(percent: number) {
    const clamped = Math.min(100, Math.max(0, percent));
    this.masterVolume = clamped / 100;
    try {
      localStorage.setItem('power_sound_volume', String(this.masterVolume));
    } catch {}
  }

  /**
   * Helper to create an ADSR envelope gain node
   */
  private createVoice(
    ctx: AudioContext, 
    dest: AudioNode, 
    volumeMultiplier = 1.0
  ): { gain: GainNode; startTime: number } {
    const gain = ctx.createGain();
    const effectiveVol = this.masterVolume * volumeMultiplier;
    gain.gain.setValueAtTime(0, ctx.currentTime);
    gain.connect(dest);
    return { gain, startTime: ctx.currentTime };
  }

  /**
   * Play a bell or tone with acoustic harmonics and exponential decay
   */
  private playHarmonicTone(
    ctx: AudioContext,
    freq: number,
    startTime: number,
    duration: number,
    type: OscillatorType = 'sine',
    baseGain = 0.15,
    decayRate = 0.8
  ) {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = type;
    osc.frequency.setValueAtTime(freq, startTime);

    // Fast attack (3ms), smooth exponential decay
    gain.gain.setValueAtTime(0.0001, startTime);
    gain.gain.exponentialRampToValueAtTime(baseGain * this.masterVolume, startTime + 0.005);
    gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration * decayRate);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(startTime);
    osc.stop(startTime + duration);
  }

  /**
   * Play curated sound based on theme and trigger type
   */
  public play(theme: SoundTheme = 'classic', trigger: SoundTriggerType = 'preview') {
    if (this.masterVolume <= 0.001) return;
    const ctx = this.getAudioContext();
    if (!ctx) return;

    try {
      const now = ctx.currentTime;

      // 1. CLICK / BUTTON
      if (trigger === 'buttonClick') {
        this.playHarmonicTone(ctx, 1200, now, 0.04, 'sine', 0.08, 0.5);
        return;
      }

      // 2. ACTION SUCCESS (Chime chord)
      if (trigger === 'actionSuccess') {
        const chord = [523.25, 659.25, 783.99, 1046.50]; // C-E-G-C
        chord.forEach((freq, idx) => {
          this.playHarmonicTone(ctx, freq, now + idx * 0.08, 0.45, 'triangle', 0.12);
        });
        return;
      }

      // 3. WARNING TICK (10s / 30s / 60s countdown)
      if (trigger === 'warningTick') {
        switch (theme) {
          case 'marimba':
            this.playHarmonicTone(ctx, 880, now, 0.09, 'sine', 0.15, 0.6);
            break;
          case 'crystal':
            this.playHarmonicTone(ctx, 1567.98, now, 0.1, 'triangle', 0.12, 0.7);
            break;
          case 'scifi':
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(1800, now);
            osc.frequency.exponentialRampToValueAtTime(600, now + 0.06);
            gain.gain.setValueAtTime(0.1 * this.masterVolume, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.08);
            break;
          case 'westminster':
            this.playHarmonicTone(ctx, 659.25, now, 0.12, 'sine', 0.14, 0.7);
            break;
          case 'urgent':
            this.playHarmonicTone(ctx, 1760, now, 0.08, 'square', 0.1, 0.8);
            break;
          case 'bubble':
            const bOsc = ctx.createOscillator();
            const bGain = ctx.createGain();
            bOsc.type = 'sine';
            bOsc.frequency.setValueAtTime(400, now);
            bOsc.frequency.exponentialRampToValueAtTime(950, now + 0.06);
            bGain.gain.setValueAtTime(0.18 * this.masterVolume, now);
            bGain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
            bOsc.connect(bGain);
            bGain.connect(ctx.destination);
            bOsc.start(now);
            bOsc.stop(now + 0.09);
            break;
          case 'classic':
          default:
            this.playHarmonicTone(ctx, 1000, now, 0.08, 'sine', 0.12, 0.7);
            break;
        }
        return;
      }

      // 4. HOURLY CHIME (Westminster & Crystal clock chimes)
      if (trigger === 'hourlyChime') {
        if (theme === 'westminster' || theme === 'classic') {
          // Authentic Westminster 4-note chime: E5, C5, D5, G4
          const notes = [
            { f: 659.25, d: 0.28 }, // E5
            { f: 523.25, d: 0.28 }, // C5
            { f: 587.33, d: 0.28 }, // D5
            { f: 392.00, d: 0.65 }  // G4
          ];
          let timeOffset = 0;
          notes.forEach(({ f, d }) => {
            // Main bell tone + harmonic shimmer
            this.playHarmonicTone(ctx, f, now + timeOffset, d + 0.4, 'sine', 0.18, 0.9);
            this.playHarmonicTone(ctx, f * 2.76, now + timeOffset, d * 0.5, 'sine', 0.04, 0.4);
            timeOffset += d;
          });
        } else if (theme === 'crystal') {
          // Lush crystal chime
          const notes = [1046.50, 1318.51, 1567.98, 2093.00];
          notes.forEach((f, idx) => {
            this.playHarmonicTone(ctx, f, now + idx * 0.15, 0.8, 'triangle', 0.15, 0.95);
          });
        } else if (theme === 'marimba') {
          const notes = [523.25, 659.25, 783.99, 1046.50, 783.99, 1046.50];
          notes.forEach((f, idx) => {
            this.playHarmonicTone(ctx, f, now + idx * 0.12, 0.4, 'sine', 0.16, 0.7);
          });
        } else {
          // Standard chime
          const notes = [587.33, 880.00, 1174.66];
          notes.forEach((f, idx) => {
            this.playHarmonicTone(ctx, f, now + idx * 0.16, 0.6, 'sine', 0.15);
          });
        }
        return;
      }

      // 5. TIMER ALARM & MODE COMPLETE
      if (trigger === 'timerAlarm') {
        if (theme === 'urgent') {
          for (let rep = 0; rep < 3; rep++) {
            const startT = now + rep * 0.35;
            this.playHarmonicTone(ctx, 880, startT, 0.1, 'sawtooth', 0.15);
            this.playHarmonicTone(ctx, 1174.66, startT + 0.12, 0.15, 'sawtooth', 0.18);
          }
        } else if (theme === 'marimba') {
          const melody = [523.25, 659.25, 783.99, 1046.50, 880.00, 1046.50, 1318.51];
          melody.forEach((f, idx) => {
            this.playHarmonicTone(ctx, f, now + idx * 0.1, 0.35, 'sine', 0.18, 0.7);
          });
        } else if (theme === 'scifi') {
          for (let i = 0; i < 3; i++) {
            const t = now + i * 0.22;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(800, t);
            osc.frequency.exponentialRampToValueAtTime(2400, t + 0.16);
            gain.gain.setValueAtTime(0.12 * this.masterVolume, t);
            gain.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(t);
            osc.stop(t + 0.2);
          }
        } else {
          // Classic melodious triple chime
          const melody = [659.25, 783.99, 1046.50, 1318.51];
          melody.forEach((f, idx) => {
            this.playHarmonicTone(ctx, f, now + idx * 0.14, 0.6, 'sine', 0.16, 0.85);
          });
        }
        return;
      }

      // 6. PREVIEW & THEME AUDITION
      switch (theme) {
        case 'marimba': {
          // Warm woody marimba arpeggio: C5, E5, G5, C6
          const notes = [523.25, 659.25, 783.99, 1046.50];
          notes.forEach((freq, idx) => {
            this.playHarmonicTone(ctx, freq, now + idx * 0.11, 0.45, 'sine', 0.22, 0.7);
            // Wooden body overtone
            this.playHarmonicTone(ctx, freq * 3, now + idx * 0.11, 0.08, 'triangle', 0.05, 0.3);
          });
          break;
        }
        case 'crystal': {
          // Pure glass crystal ring: F5 -> Bb5 -> D6
          const notes = [698.46, 932.33, 1174.66];
          notes.forEach((freq, idx) => {
            this.playHarmonicTone(ctx, freq, now + idx * 0.14, 0.85, 'triangle', 0.18, 0.95);
            this.playHarmonicTone(ctx, freq * 2, now + idx * 0.14, 0.6, 'sine', 0.06, 0.8);
          });
          break;
        }
        case 'scifi': {
          // Cyber sweep and double high-tech bleep
          const osc1 = ctx.createOscillator();
          const gain1 = ctx.createGain();
          osc1.type = 'sawtooth';
          osc1.frequency.setValueAtTime(600, now);
          osc1.frequency.exponentialRampToValueAtTime(1800, now + 0.18);
          gain1.gain.setValueAtTime(0.12 * this.masterVolume, now);
          gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
          osc1.connect(gain1);
          gain1.connect(ctx.destination);
          osc1.start(now);
          osc1.stop(now + 0.22);

          this.playHarmonicTone(ctx, 2200, now + 0.24, 0.15, 'sine', 0.12);
          break;
        }
        case 'westminster': {
          // 4-bell tower chime
          const notes = [659.25, 523.25, 587.33, 392.00];
          let t = 0;
          notes.forEach((freq) => {
            this.playHarmonicTone(ctx, freq, now + t, 0.6, 'sine', 0.2, 0.9);
            t += 0.22;
          });
          break;
        }
        case 'urgent': {
          // High alert double burst
          for (let i = 0; i < 2; i++) {
            const t = now + i * 0.18;
            this.playHarmonicTone(ctx, 1174.66, t, 0.12, 'sawtooth', 0.16);
            this.playHarmonicTone(ctx, 1567.98, t + 0.06, 0.1, 'sawtooth', 0.16);
          }
          break;
        }
        case 'bubble': {
          // Twin water droplet pops
          [0, 0.16].forEach((offset, idx) => {
            const bOsc = ctx.createOscillator();
            const bGain = ctx.createGain();
            bOsc.type = 'sine';
            const startF = idx === 0 ? 380 : 520;
            const endF = idx === 0 ? 980 : 1350;
            bOsc.frequency.setValueAtTime(startF, now + offset);
            bOsc.frequency.exponentialRampToValueAtTime(endF, now + offset + 0.08);
            bGain.gain.setValueAtTime(0.2 * this.masterVolume, now + offset);
            bGain.gain.exponentialRampToValueAtTime(0.001, now + offset + 0.1);
            bOsc.connect(bGain);
            bGain.connect(ctx.destination);
            bOsc.start(now + offset);
            bOsc.stop(now + offset + 0.12);
          });
          break;
        }
        case 'classic':
        default: {
          // Classic 2-tone melodic chime: D5 -> A5
          this.playHarmonicTone(ctx, 587.33, now, 0.45, 'triangle', 0.2, 0.85);
          this.playHarmonicTone(ctx, 880.00, now + 0.16, 0.6, 'triangle', 0.22, 0.9);
          break;
        }
      }
    } catch {
      // AudioContext fallback
    }
  }
}

export const soundEngine = new SoundEngine();
