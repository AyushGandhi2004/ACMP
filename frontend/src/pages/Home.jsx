import { useEffect } from 'react';
import { Zap, RotateCcw } from 'lucide-react';
import CodeInput from '../components/CodeInput/CodeInput';
import LanguageSelector from '../components/LanguageSelector/LanguageSelector';
import AgentPanel from '../components/AgentPanel/AgentPanel';
import DiffViewer from '../components/DiffViewer/DiffViewer';
import Banner from '../components/Banner/Banner';
import usePipelineStore from '../store/pipelineStore';
import usePipeline from '../hooks/usePipeline';
import useWebSocket from '../hooks/useWebSocket';


// ─────────────────────────────────────────
// HOME PAGE
// Main pipeline UI
// Assembles all components in correct order
// ─────────────────────────────────────────

export default function Home() {

    const {
        sessionId,
        pipelineStatus,
        fullReset,
    } = usePipelineStore();

    const {
        startPipeline,
        canSubmit,
        isLoading,
    } = usePipeline();

    // WebSocket connects automatically
    // when sessionId is set by usePipeline
    useWebSocket(sessionId);

    const isRunning = pipelineStatus === 'running';
    const isComplete = pipelineStatus === 'success' ||
                       pipelineStatus === 'failed';


    return (
        <div className="max-w-[1280px] mx-auto p-8 font-sans text-slate-800 bg-white min-h-screen">


            {/* ── Header ───────────────────────── */}
            <div className="mb-12 text-center">
                <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2 italic">
                    ACMP
                </h1>
                <p className="text-slate-400 text-sm font-black uppercase tracking-[0.15em]">
                    Autonomous Code Modernization Platform
                </p>
            </div>


            {/* ── Control Bar ──────────────────── */}
            {/* File upload / paste + language     */}
            {/* selector + run button in one row   */}
            <div className="bg-white border border-slate-200 rounded-2xl p-3 flex items-center gap-4 shadow-sm mb-6">

                {/* Language selector */}
                <div className="px-3">
                    <LanguageSelector />
                </div>

                <div className="h-8 w-[1px] bg-slate-100" />

                {/* Status indicator while running */}
                {isRunning && (
                    <div className="flex items-center gap-2 px-3">
                        <div className="w-2 h-2 rounded-full bg-[#FF4B4B] animate-ping" />
                        <p className="text-[10px] font-black text-[#FF4B4B] uppercase tracking-widest">
                            Pipeline Running...
                        </p>
                    </div>
                )}

                {/* Spacer */}
                <div className="flex-1" />

                {/* New session button — shown after completion */}
                {isComplete && (
                    <button
                        onClick={fullReset}
                        className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-600 px-5 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all active:scale-95"
                    >
                        <RotateCcw size={14} />
                        New Session
                    </button>
                )}

                {/* Run Pipeline button */}
                <button
                    onClick={startPipeline}
                    disabled={!canSubmit}
                    className="flex items-center gap-2 bg-[#FF4B4B] hover:bg-[#e63939] text-white px-8 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest shadow-md transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    <Zap size={16} />
                    {isLoading ? 'Starting...' : 'Run Pipeline'}
                </button>

            </div>


            {/* ── Code Input Section ───────────── */}
            <div className="mb-6">
                <CodeInput />
            </div>


            {/* ── Agent Panel ──────────────────── */}
            {/* Only visible after pipeline starts */}
            <div className="mb-6">
                <AgentPanel />
            </div>


            {/* ── Diff Viewer ──────────────────── */}
            {/* Only visible when result exists    */}
            <div className="mb-6">
                <DiffViewer />
            </div>


            {/* ── Result Banner ────────────────── */}
            {/* Auto scrolls into view on complete */}
            <div className="mb-16">
                <Banner />
            </div>


        </div>
    );
}



