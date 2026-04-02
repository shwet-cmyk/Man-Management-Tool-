import { MascotStateRenderer } from './MascotStateRenderer'

export function MascotErrorState({ message = 'Oh no. I couldn’t complete that request.' }) {
  return <div style={{ padding: 12, border: '1px solid #fecaca', borderRadius: 10, background: '#fff1f2' }}><MascotStateRenderer state="sad" subtitle={message} /></div>
}
