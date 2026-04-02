import React, { useEffect, useState } from 'react'
import { MascotStateRenderer } from './MascotStateRenderer'

export function MascotSuccessToast({ open, message = 'All set.', onClose }) {
  const [visible, setVisible] = useState(open)

  useEffect(() => {
    setVisible(open)
    if (!open) return
    const t = setTimeout(() => {
      setVisible(false)
      onClose?.()
    }, 1600)
    return () => clearTimeout(t)
  }, [open, onClose])

  if (!visible) return null
  return (
    <div style={{ position: 'fixed', right: 24, bottom: 26, zIndex: 60, width: 260, background: '#ecfdf5', border: '1px solid #86efac', borderRadius: 10, padding: 10 }}>
      <MascotStateRenderer state="celebrate" subtitle={message} />
    </div>
  )
}
