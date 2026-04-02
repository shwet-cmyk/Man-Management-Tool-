import { useCallback } from 'react'
import { useMotionPreferences } from './MotionPreferenceProvider'

const SOUND_PRESETS = {
  success: [660, 880],
  error: [220, 160],
  warning: [420, 350],
  notification: [550],
  message_received: [620],
  approval_success: [700, 900],
  task_complete: [760, 980],
  reminder: [500, 620],
}

export function useActionSoundEngine() {
  const { preferences } = useMotionPreferences()

  const play = useCallback((category) => {
    if (!preferences.assistantSounds && category !== 'notification') return
    if (!preferences.notificationSounds && category === 'notification') return

    const tones = SOUND_PRESETS[category]
    if (!tones) return

    try {
      const context = new (window.AudioContext || window.webkitAudioContext)()
      let start = context.currentTime
      tones.forEach((freq) => {
        const osc = context.createOscillator()
        const gain = context.createGain()
        osc.type = 'sine'
        osc.frequency.value = freq
        gain.gain.value = 0.02
        osc.connect(gain)
        gain.connect(context.destination)
        osc.start(start)
        osc.stop(start + 0.09)
        start += 0.1
      })
    } catch {
      // Browser might block autoplay/sound.
    }
  }, [preferences.assistantSounds, preferences.notificationSounds])

  return { play }
}
