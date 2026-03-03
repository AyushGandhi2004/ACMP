import { Code } from 'lucide-react';
import usePipelineStore from '../../store/pipelineStore';


// ─────────────────────────────────────────
// SUPPORTED LANGUAGES
// Add new languages here as platform grows
// value must match SupportedLanguage enum
// in backend/app/domain/enums.py
// ─────────────────────────────────────────

const LANGUAGES = [
    {
        value: 'auto',
        label: 'Auto Detect',
        description: 'Let Profiler Agent detect'
    },
    {
        value: 'python',
        label: 'Python',
        description: 'Django, Flask, FastAPI'
    },
    {
        value: 'javascript',
        label: 'JavaScript',
        description: 'Express, React'
    },
    {
        value: 'typescript',
        label: 'TypeScript',
        description: 'Modern JS with types'
    },
    {
        value: 'java',
        label: 'Java',
        description: 'Spring framework'
    },
];


// ─────────────────────────────────────────
// LANGUAGE SELECTOR COMPONENT
// Dropdown for selecting target language
// Auto updates when file is uploaded
// ─────────────────────────────────────────

export default function LanguageSelector() {

    const {
        selectedLanguage,
        setSelectedLanguage,
        detectedLanguage,
        pipelineStatus,
    } = usePipelineStore();

    const isRunning = pipelineStatus === 'running';


    return (
        <div className="flex flex-col gap-2">

            {/* ── Label ────────────────────────── */}
            <div className="flex items-center gap-2">
                <Code size={12} className="text-slate-400" />
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Language
                </p>
            </div>

            {/* ── Dropdown ─────────────────────── */}
            <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                disabled={isRunning}
                className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs font-bold text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-[#FF4B4B] transition-all disabled:opacity-50 cursor-pointer min-w-[160px]"
            >
                {LANGUAGES.map((lang) => (
                    <option
                        key={lang.value}
                        value={lang.value}
                    >
                        {lang.label}
                    </option>
                ))}
            </select>

            {/* ── Auto detected badge ───────────── */}
            {/* Shows when Profiler has detected    */}
            {/* the language during pipeline run    */}
            {detectedLanguage && selectedLanguage === 'auto' && (
                <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                    <p className="text-[10px] font-black text-green-500 uppercase tracking-widest">
                        Detected: {detectedLanguage}
                    </p>
                </div>
            )}

            {/* ── Manual selection badge ────────── */}
            {/* Shows when user manually selected   */}
            {/* a language from the dropdown        */}
            {selectedLanguage !== 'auto' && (
                <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#FF4B4B]" />
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        Manual selection
                    </p>
                </div>
            )}

        </div>
    );
}