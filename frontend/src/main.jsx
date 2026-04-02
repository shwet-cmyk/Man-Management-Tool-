import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { MotionPreferenceProvider } from './mascot/MotionPreferenceProvider'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MotionPreferenceProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </MotionPreferenceProvider>
  </React.StrictMode>,
)
