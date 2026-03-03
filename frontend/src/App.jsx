import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Admin from './pages/Admin';


// ─────────────────────────────────────────
// NAVIGATION BAR
// Minimal top nav with links to
// Home and Admin pages
// Highlights active route
// ─────────────────────────────────────────

function NavBar() {
    const location = useLocation();

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="top-0 left-0 right-0 z-50 bg-white border-b border-slate-100 shadow-sm">
            <div className="max-w-[1280px] mx-auto px-8 py-3 flex items-center justify-between">

                {/* ── Brand ────────────────────── */}
                <Link
                    to="/"
                    className="text-sm font-black text-slate-900 italic tracking-tight hover:text-[#FF4B4B] transition-colors"
                >
                    ACMP
                </Link>

                {/* ── Nav Links ────────────────── */}
                <div className="flex items-center gap-1">

                    <Link
                        to="/"
                        className={`
                            px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all
                            ${isActive('/')
                                ? 'bg-red-50 text-[#FF4B4B]'
                                : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
                            }
                        `}
                    >
                        Pipeline
                    </Link>

                    <Link
                        to="/admin"
                        className={`
                            px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all
                            ${isActive('/admin')
                                ? 'bg-red-50 text-[#FF4B4B]'
                                : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
                            }
                        `}
                    >
                        Admin
                    </Link>

                </div>
            </div>
        </nav>
    );
}



// ─────────────────────────────────────────
// APP COMPONENT
// Root component with routing setup
// NavBar is always visible
// Content changes based on route
// ─────────────────────────────────────────

export default function App() {
    return (
        <BrowserRouter>
            {/* ── Navigation ───────────────────── */}
            <NavBar />

            {/* ── Page Content ─────────────────── */}
            {/* pt-16 accounts for fixed navbar height */}
            <div className="pt-16">
                <Routes>
                    <Route path="/"      element={<Home />}  />
                    <Route path="/admin" element={<Admin />} />
                </Routes>
            </div>
        </BrowserRouter>
    );
}



