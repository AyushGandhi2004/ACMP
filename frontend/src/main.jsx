import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';


// ─────────────────────────────────────────
// ENTRY POINT
// Mounts the React app into the DOM
// StrictMode helps catch common bugs
// during development
// ─────────────────────────────────────────

createRoot(document.getElementById('root')).render(
    <StrictMode>
        <App />
    </StrictMode>
);