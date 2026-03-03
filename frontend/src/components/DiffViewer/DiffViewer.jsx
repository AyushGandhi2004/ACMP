import { useState } from 'react';
import { Terminal, FileCode, Copy, Check } from 'lucide-react';
import usePipelineStore from '../../store/pipelineStore';


// ─────────────────────────────────────────
// COPY BUTTON COMPONENT
// Reused on both left and right panels
// Shows checkmark for 2 seconds after copy
// ─────────────────────────────────────────

function CopyButton({ text }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            // Clipboard API failed — silent fail
        }
    };

    return (
        <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 bg-white hover:bg-slate-50 text-slate-500 px-3 py-1 rounded-lg text-[10px] font-black border border-slate-200 shadow-sm transition-all active:scale-95 uppercase tracking-widest"
        >
            {copied
                ? <Check size={11} className="text-green-500" />
                : <Copy size={11} />
            }
            {copied ? 'Copied' : 'Copy'}
        </button>
    );
}


// ─────────────────────────────────────────
// CODE PANEL COMPONENT
// Single panel — reused for both
// original and modernized code
// ─────────────────────────────────────────

function CodePanel({
    title,
    icon: Icon,
    iconColor,
    code,
    placeholder,
    borderColor,
    showCopy = false
}) {
    return (
        <div className="flex flex-col h-full">

            {/* ── Panel Header ─────────────────── */}
            <div className="flex items-center justify-between mb-4">
                <div className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-widest ${iconColor}`}>
                    <Icon size={14} />
                    {title}
                </div>

                {/* Copy button — only on right panel */}
                {showCopy && code && (
                    <CopyButton text={code} />
                )}
            </div>

            {/* ── Code Area ────────────────────── */}
            <div className={`
                flex-1 rounded-2xl border overflow-auto
                shadow-inner bg-slate-50
                ${borderColor}
            `}
                style={{ height: '600px' }}
            >
                {code ? (
                    <pre className="p-6 text-sm font-mono text-slate-700 whitespace-pre-wrap leading-relaxed">
                        {code}
                    </pre>
                ) : (
                    <div className="flex items-center justify-center h-full">
                        <p className="text-slate-200 italic text-sm font-medium">
                            {placeholder}
                        </p>
                    </div>
                )}
            </div>

        </div>
    );
}


// ─────────────────────────────────────────
// LINE COUNT BADGE
// Shows number of lines in the code
// ─────────────────────────────────────────

function LineCountBadge({ code, label }) {
    if (!code) return null;
    const lines = code.split('\n').length;

    return (
        <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">
            {label}: {lines.toLocaleString()} lines
        </span>
    );
}


// ─────────────────────────────────────────
// DIFF STATS BAR
// Shows a quick comparison between
// original and modernized code
// Only visible when both codes exist
// ─────────────────────────────────────────

function DiffStatsBar({ originalCode, modernCode }) {
    if (!originalCode || !modernCode) return null;

    const originalLines = originalCode.split('\n').length;
    const modernLines   = modernCode.split('\n').length;
    const lineDiff      = modernLines - originalLines;
    const isSmaller     = lineDiff < 0;
    const isSame        = lineDiff === 0;

    return (
        <div className="flex items-center gap-6 px-6 py-3 bg-slate-50 border border-slate-100 rounded-xl mb-6">

            {/* Original stats */}
            <LineCountBadge
                code={originalCode}
                label="Original"
            />

            <div className="h-4 w-[1px] bg-slate-200" />

            {/* Modern stats */}
            <LineCountBadge
                code={modernCode}
                label="Modernized"
            />

            <div className="h-4 w-[1px] bg-slate-200" />

            {/* Difference */}
            <span className={`
                text-[10px] font-black uppercase tracking-widest
                ${isSmaller
                    ? 'text-green-500'
                    : isSame
                        ? 'text-slate-400'
                        : 'text-[#FF4B4B]'
                }
            `}>
                {isSame
                    ? 'Same length'
                    : isSmaller
                        ? `${Math.abs(lineDiff)} lines removed`
                        : `${lineDiff} lines added`
                }
            </span>

        </div>
    );
}


// ─────────────────────────────────────────
// DIFF VIEWER COMPONENT
// Side by side panels showing original
// and modernized code
// Only renders when pipeline has result
// ─────────────────────────────────────────

export default function DiffViewer() {

    const {
        originalCode,
        modernCode,
        pipelineStatus,
    } = usePipelineStore();

    // Don't render until we have a result
    if (!modernCode) return null;

    return (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">

            {/* ── Header ───────────────────────── */}
            <div className="flex items-center gap-2 mb-4">
                <FileCode size={14} className="text-slate-400" />
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Code Comparison
                </p>

                {/* Success badge */}
                {pipelineStatus === 'success' && (
                    <div className="ml-auto flex items-center gap-1.5 bg-green-50 border border-green-100 px-3 py-1 rounded-full">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                        <p className="text-[10px] font-black text-green-500 uppercase tracking-widest">
                            Verified
                        </p>
                    </div>
                )}
            </div>

            {/* ── Diff Stats Bar ───────────────── */}
            <DiffStatsBar
                originalCode={originalCode}
                modernCode={modernCode}
            />

            {/* ── Side by Side Panels ──────────── */}
            <div className="grid grid-cols-2 gap-6">

                {/* Left — Original Code */}
                <CodePanel
                    title="Source"
                    icon={Terminal}
                    iconColor="text-slate-400"
                    code={originalCode}
                    placeholder="Original code will appear here..."
                    borderColor="border-slate-100"
                    showCopy={false}
                />

                {/* Right — Modernized Code */}
                <CodePanel
                    title="Modernized"
                    icon={FileCode}
                    iconColor="text-[#FF4B4B]"
                    code={modernCode}
                    placeholder="Awaiting pipeline execution..."
                    borderColor="border-red-100"
                    showCopy={true}
                />

            </div>

        </div>
    );
}





