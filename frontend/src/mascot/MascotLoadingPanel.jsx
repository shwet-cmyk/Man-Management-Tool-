import React from 'react'
import { MascotStateRenderer } from './MascotStateRenderer'

export function MascotLoadingPanel({ message = 'Loading…' }) {
  return <div style={{ padding: 12, border: '1px solid #e2e8f0', borderRadius: 10, background: '#f8fafc' }}><MascotStateRenderer state="loading" subtitle={message} /></div>
}
