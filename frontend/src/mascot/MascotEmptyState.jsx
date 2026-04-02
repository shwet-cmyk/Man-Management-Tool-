import React from 'react'
import { MascotStateRenderer } from './MascotStateRenderer'

export function MascotEmptyState({ message = 'No data yet. Try a quick question.' }) {
  return <div style={{ padding: 12, border: '1px dashed #cbd5e1', borderRadius: 10, background: '#fff' }}><MascotStateRenderer state="idle" subtitle={message} /></div>
}
