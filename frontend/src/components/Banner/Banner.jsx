import { useEffect, useRef } from 'react';
import { CheckCircle, XCircle, AlertCircle, RotateCcw, Zap } from 'lucide-react';
import usePipelineStore from '../../store/pipelineStore';
import usePipeline from '../../hooks/usePipeline';


// ─────────────────────────────────────────
// TRANSFORMATION PLAN SECTION
// Shows the steps the Architect planned
// Only visible on success
// ─────────────────────────────────────────

function TransformationPlanSection({ plan }) {
    if (!plan || !plan.steps || plan.steps.length === 0) return null;

    return (
        <div className="mt-4 bg-white bg-opacity-60 rounded-xl p-4 border border-green-100">
            <p className="text-[10px] font-black text-green-600 uppercase tracking-widest mb-3">
                Transformation Steps Applied
            </p>
            <div className="flex flex-col gap-2">
                {plan.steps.map((step, index) => (
                    <div
                        key={index}
                        className="flex items-start gap-2"
                    >
                        <span className="text-[10px] font-black text-green-400 mt-0.5 shrink-0">
                            {String(index + 1).padStart(2, '0')}
                        </span>
                        <p className="text-xs text-green-700 leading-relaxed">
                            {step}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
}


// ─────────────────────────────────────────
// VALIDATION LOGS SECTION
// Shows Docker test output on failure
// Helps user understand what went wrong
// ─────────────────────────────────────────

function ValidationLogsSection({ logs }) {
    if (!logs) return null;

    return (
        <div className="mt-4 bg-white bg-opacity-60 rounded-xl border border-red-100 overflow-hidden">
            <div className="px-4 py-2 border-b border-red-100 flex items-center gap-2">
                <AlertCircle size={11} className="text-red-400" />
                <p className="text-[10px] font-black text-red-400 uppercase tracking-widest">
                    Validation Logs
                </p>
            </div>
            <pre className="p-4 text-xs font-mono text-red-400 overflow-auto max-h-48 leading-relaxed whitespace-pre-wrap">
                {logs}
            </pre>
        </div>
    );
}


// ─────────────────────────────────────────
// SUCCESS BANNER
// ─────────────────────────────────────────

function SuccessBanner({
    detectedLanguage,
    detectedFramework,
    transformationPlan
}) {
    return (
        <div className="bg-green-50 border border-green-200 rounded-3xl p-8 shadow-xl animate-in zoom-in-95 duration-500">

            {/* ── Top Row ──────────────────────── */}
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">

                    {/* Icon */}
                    <div className="p-3 bg-green-100 rounded-2xl">
                        <CheckCircle size={28} className="text-green-500" />
                    </div>

                    {/* Title + subtitle */}
                    <div>
                        <p className="text-slate-900 font-black text-2xl tracking-tight">
                            Modernization Complete
                        </p>
                        <p className="text-slate-500 text-sm font-medium mt-1">
                            Code verified by the agent team
                        </p>
                    </div>
                </div>

                {/* Detected meta badge */}
                {(detectedLanguage || detectedFramework) && (
                    <div className="flex items-center gap-2 bg-white border border-green-100 px-4 py-2 rounded-xl shadow-sm">
                        <Zap size={12} className="text-green-400" />
                        <p className="text-xs font-black text-slate-600 uppercase tracking-widest">
                            {[detectedLanguage, detectedFramework]
                                .filter(Boolean)
                                .join(' · ')
                            }
                        </p>
                    </div>
                )}
            </div>

            {/* ── Transformation Plan ──────────── */}
            <TransformationPlanSection plan={transformationPlan} />

        </div>
    );
}


// ─────────────────────────────────────────
// FAILED BANNER
// ─────────────────────────────────────────

function FailedBanner({
    error,
    validationLogs,
    onRetry
}) {
    return (
        <div className="bg-red-50 border border-red-200 rounded-3xl p-8 shadow-xl animate-in slide-in-from-bottom-4 duration-500">

            {/* ── Top Row ──────────────────────── */}
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">

                    {/* Icon */}
                    <div className="p-3 bg-red-100 rounded-2xl">
                        <XCircle size={28} className="text-[#FF4B4B]" />
                    </div>

                    {/* Title + subtitle */}
                    <div>
                        <p className="text-slate-900 font-black text-2xl tracking-tight">
                            Pipeline Failed
                        </p>
                        <p className="text-slate-500 text-sm font-medium mt-1">
                            {error || 'Something went wrong during modernization'}
                        </p>
                    </div>
                </div>

                {/* Retry button */}
                <button
                    onClick={onRetry}
                    className="flex items-center gap-2 bg-[#FF4B4B] hover:bg-[#e63939] text-white px-6 py-3 rounded-xl font-black text-xs uppercase tracking-widest shadow-md transition-all active:scale-95"
                >
                    <RotateCcw size={14} />
                    Retry
                </button>
            </div>

            {/* ── Validation Logs ──────────────── */}
            <ValidationLogsSection logs={validationLogs} />

        </div>
    );
}


// ─────────────────────────────────────────
// BANNER COMPONENT
// Appears at bottom of page when pipeline
// completes — success or failure
// Auto scrolls into view when it appears
// ─────────────────────────────────────────

export default function Banner() {

    const bannerRef = useRef(null);

    const {
        pipelineStatus,
        error,
        validationLogs,
        transformationPlan,
        detectedLanguage,
        detectedFramework,
    } = usePipelineStore();

    const { retryPipeline } = usePipeline();

    const isSuccess = pipelineStatus === 'success';
    const isFailed  = pipelineStatus === 'failed';
    const isVisible = isSuccess || isFailed;


    // ── Auto scroll into view ─────────────
    // Smooth scroll when banner appears
    useEffect(() => {
        if (isVisible && bannerRef.current) {
            bannerRef.current.scrollIntoView({
                behavior: 'smooth',
                block:    'center'
            });
        }
    }, [isVisible]);


    // Don't render if pipeline not complete
    if (!isVisible) return null;

    return (
        <div
            ref={bannerRef}
            className="scroll-mt-24"
        >
            {isSuccess ? (
                <SuccessBanner
                    detectedLanguage={detectedLanguage}
                    detectedFramework={detectedFramework}
                    transformationPlan={transformationPlan}
                />
            ) : (
                <FailedBanner
                    error={error}
                    validationLogs={validationLogs}
                    onRetry={retryPipeline}
                />
            )}
        </div>
    );
}