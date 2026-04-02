import { createContext, useContext, useMemo, useState } from 'react'

const MotionPreferenceContext = createContext(null)

const STORAGE_KEY = 'tez_mascot_preferences_v1'

const defaultPrefs = {
  reduceAnimations: false,
  assistantSounds: true,
  notificationSounds: true,
  showMascotAssistant: true,
}

function loadInitialPreferences() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultPrefs
    return { ...defaultPrefs, ...JSON.parse(raw) }
  } catch {
    return defaultPrefs
  }
}

export function MotionPreferenceProvider({ children }) {
  const [preferences, setPreferences] = useState(loadInitialPreferences)

  const updatePreference = (key, value) => {
    setPreferences((curr) => {
      const next = { ...curr, [key]: value }
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } catch {
        // no-op
      }
      return next
    })
  }

  const value = useMemo(() => ({ preferences, updatePreference }), [preferences])
  return <MotionPreferenceContext.Provider value={value}>{children}</MotionPreferenceContext.Provider>
}

export function useMotionPreferences() {
  const ctx = useContext(MotionPreferenceContext)
  if (!ctx) {
    throw new Error('useMotionPreferences must be used within MotionPreferenceProvider')
  }
  return ctx
}
