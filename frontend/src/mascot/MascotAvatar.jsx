import React, { useMemo } from 'react'
import { useMotionPreferences } from './MotionPreferenceProvider'

const statePalette = {
  idle: { ear: '#8d6e63', nose: '#6d4c41', accent: '#d7a97c' },
  happy: { ear: '#8d6e63', nose: '#6d4c41', accent: '#e0b785' },
  thinking: { ear: '#7f6458', nose: '#5d4037', accent: '#d4a276' },
  waiting: { ear: '#8d6e63', nose: '#6d4c41', accent: '#cfa279' },
  loading: { ear: '#8d6e63', nose: '#6d4c41', accent: '#d8ab80' },
  alert: { ear: '#7f6458', nose: '#5d4037', accent: '#d9976e' },
  sad: { ear: '#735a50', nose: '#4e342e', accent: '#c79070' },
  celebrate: { ear: '#8d6e63', nose: '#6d4c41', accent: '#e4bd91' },
  sleeping: { ear: '#6d4c41', nose: '#4e342e', accent: '#c89d74' },
  listening: { ear: '#8d6e63', nose: '#6d4c41', accent: '#deb287' },
}

export function MascotAvatar({ state = 'idle', size = 88 }) {
  const { preferences } = useMotionPreferences()
  const palette = statePalette[state] || statePalette.idle
  const animatedClass = preferences.reduceAnimations ? '' : `mascot-${state}`

  const styleTag = useMemo(() => (
    <style>{`
      .mascot-base { transition: transform 240ms ease, opacity 240ms ease; }
      .mascot-idle { animation: mascotBlink 4.8s infinite; }
      .mascot-happy { animation: mascotWag 1.6s ease-in-out infinite; }
      .mascot-thinking { animation: mascotTilt 2.2s ease-in-out infinite; }
      .mascot-waiting { animation: mascotPulse 2.5s ease-in-out infinite; }
      .mascot-loading { animation: mascotBounce 1.8s ease-in-out infinite; }
      .mascot-alert { animation: mascotTilt 1.4s ease-in-out infinite; }
      .mascot-sad { animation: mascotSlow 2.4s ease-in-out infinite; }
      .mascot-celebrate { animation: mascotBounce 1.2s ease-in-out infinite; }
      .mascot-sleeping { animation: mascotBreath 3s ease-in-out infinite; opacity: 0.9; }
      .mascot-listening { animation: mascotWag 1.4s ease-in-out infinite; }
      @keyframes mascotBlink { 0%, 45%, 48%, 100% { transform: translateY(0); } 46% { transform: translateY(1px); } }
      @keyframes mascotWag { 0%,100% { transform: rotate(0deg); } 50% { transform: rotate(1.2deg); } }
      @keyframes mascotTilt { 0%,100% { transform: rotate(0deg); } 50% { transform: rotate(-3deg); } }
      @keyframes mascotPulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.02); } }
      @keyframes mascotBounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-2px); } }
      @keyframes mascotSlow { 0%,100% { transform: translateY(0); } 50% { transform: translateY(2px); } }
      @keyframes mascotBreath { 0%,100% { transform: scale(1); } 50% { transform: scale(0.985); } }
    `}</style>
  ), [])

  return (
    <div style={{ width: size, height: size }} aria-label={`Mascot ${state}`}>
      {styleTag}
      <svg className={`mascot-base ${animatedClass}`} viewBox="0 0 120 120" width={size} height={size} role="img">
        <circle cx="60" cy="64" r="34" fill={palette.accent} />
        <ellipse cx="35" cy="52" rx="12" ry="18" fill={palette.ear} />
        <ellipse cx="85" cy="52" rx="12" ry="18" fill={palette.ear} />
        <circle cx="48" cy="62" r="4" fill="#2f2f2f" />
        <circle cx="72" cy="62" r="4" fill="#2f2f2f" />
        <ellipse cx="60" cy="74" rx="12" ry="9" fill="#f5e1cf" />
        <ellipse cx="60" cy="72" rx="6" ry="4" fill={palette.nose} />
        <path d="M52 80 Q60 86 68 80" stroke="#6d4c41" strokeWidth="2.5" fill="none" strokeLinecap="round" />
        {state === 'sleeping' && <text x="88" y="28" fontSize="11" fill="#64748b">z</text>}
        {state === 'thinking' && <circle cx="92" cy="30" r="5" fill="#cbd5e1" />}
        {state === 'alert' && <circle cx="94" cy="24" r="4" fill="#f59e0b" />}
        {state === 'celebrate' && <circle cx="93" cy="28" r="4" fill="#22c55e" />}
      </svg>
    </div>
  )
}
