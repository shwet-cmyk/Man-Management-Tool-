import React from 'react'
import { MascotAvatar } from './MascotAvatar'

const captions = {
  idle: 'Ready when you are.',
  happy: 'Great progress.',
  thinking: 'Working on your request…',
  waiting: 'Waiting for your input.',
  loading: 'Preparing details…',
  alert: 'This may need your attention.',
  sad: 'Oh no. Something didn’t go as planned.',
  celebrate: 'Done successfully.',
  sleeping: 'Assistant resting quietly.',
  listening: 'Listening…',
}

export function MascotStateRenderer({ state = 'idle', subtitle }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <MascotAvatar state={state} size={54} />
      <div>
        <div style={{ fontWeight: 600, color: '#0f172a' }}>Labrador Assistant</div>
        <div style={{ fontSize: 12, color: '#64748b' }}>{subtitle || captions[state] || captions.idle}</div>
      </div>
    </div>
  )
}
