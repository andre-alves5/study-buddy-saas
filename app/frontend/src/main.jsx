import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { Amplify } from 'aws-amplify';

// Configure Amplify with values injected from environment variables
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: window.env?.COGNITO_POOL_ID || import.meta.env.VITE_COGNITO_POOL_ID,
      userPoolClientId: window.env?.COGNITO_CLIENT_ID || import.meta.env.VITE_COGNITO_CLIENT_ID,
    }
  }
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
