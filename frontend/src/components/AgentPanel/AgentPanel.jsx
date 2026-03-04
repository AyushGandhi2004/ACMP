import { CheckCircle, XCircle, Loader, Clock, Wrench } from 'lucide-react';
import usePipelineStore from '../../store/pipelineStore';


// ─────────────────────────────────────────
// AGENT DEFINITIONS
// Order matters — matches pipeline flow
// Add new agents here as platform grows
// ─────────────────────────────────────────

const AGENTS = [
    {
        id:          'profiler',
        label:       'Profiler',
        description: 'Detects language & framework',
    },
    {
        id:          'logic_anchor',
        label:       'Logic Anchor',
        description: 'Generates unit tests',
    },
    {
        id:          'architect',
        label:       'Architect',
        description: 'Builds transformation plan',
    },
    {
        id:          'engineer',
        label:       'Engineer',
        description: 'Modernizes the code',
    },
    {
        id:          'tester',
        label:       'Tester',
        description: 'Runs tests in Docker',
    },
    {
        id:          'fixer',
        label:       'Fixer',
        description: 'Fixes syntax errors',
    },
];


// ─────────────────────────────────────────
// STATUS CONFIG
// Maps agent status to visual properties
// ─────────────────────────────────────────

const STATUS_CONFIG = {
    waiting: {
        icon:       Clock,
        iconColor:  'text-slate-300',
        cardBorder: 'border-slate-100',
        cardBg:     'bg-white',
        labelColor: 'text-slate-300',
        dotColor:   'bg-slate-200',
    },
    running: {
        icon:       Loader,
        iconColor:  'text-[#FF4B4B]',
        cardBorder: 'border-[#FF4B4B]',
        cardBg:     'bg-red-50',
        labelColor: 'text-[#FF4B4B]',
        dotColor:   'bg-[#FF4B4B] animate-pulse',
    },
    completed: {
        icon:       CheckCircle,
        iconColor:  'text-green-500',
        cardBorder: 'border-green-100',
        cardBg:     'bg-green-50',
        labelColor: 'text-green-600',
        dotColor:   'bg-green-400',
    },
    failed: {
        icon:       XCircle,
        iconColor:  'text-red-500',
        cardBorder: 'border-red-200',
        cardBg:     'bg-red-50',
        labelColor: 'text-red-500',
        dotColor:   'bg-red-400',
    },
};


// ─────────────────────────────────────────
// HELPER — GET AGENT STATUS
// Derives current status of each agent
// from the list of agentEvents in store
// ─────────────────────────────────────────

const getAgentStatus = (agentId, agentEvents) => {
    // Find all events for this agent
    const events = agentEvents.filter(
        (e) => e.agent_name === agentId
    );

    if (events.length === 0) return 'waiting';

    // Get the most recent event for this agent
    const latest = events[events.length - 1];
    return latest.status;
};


// ─────────────────────────────────────────
// HELPER — GET AGENT MESSAGE
// Returns the latest message for an agent
// ─────────────────────────────────────────

const getAgentMessage = (agentId, agentEvents) => {
    const events = agentEvents.filter(
        (e) => e.agent_name === agentId
    );
    if (events.length === 0) return null;
    const latest = events[events.length - 1];
    return latest.message || null;
};


// ─────────────────────────────────────────
// SINGLE AGENT CARD COMPONENT
// ─────────────────────────────────────────

function AgentCard({ agent, status, message }) {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.waiting;
    const Icon   = config.icon;
    const isRunning = status === 'running';

    return (
        <div className={`
            flex flex-col gap-3 p-4 rounded-2xl border
            transition-all duration-500
            ${config.cardBg} ${config.cardBorder}
            ${isRunning ? 'shadow-lg shadow-red-100 scale-[1.02]' : 'shadow-sm'}
        `}>

            {/* ── Top Row: Icon + Status dot ─── */}
            <div className="flex items-center justify-between">
                <div className={`
                    p-2 rounded-xl
                    ${isRunning ? 'bg-red-100' : 'bg-white'}
                    transition-colors
                `}>
                    <Icon
                        size={18}
                        className={`
                            ${config.iconColor}
                            ${isRunning ? 'animate-spin' : ''}
                        `}
                    />
                </div>

                {/* Status dot */}
                <div className={`
                    w-2 h-2 rounded-full
                    ${config.dotColor}
                `} />
            </div>

            {/* ── Agent Name ───────────────────── */}
            <div>
                <p className={`
                    text-xs font-black uppercase tracking-widest
                    ${config.labelColor}
                    transition-colors duration-300
                `}>
                    {agent.label}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5 font-medium">
                    {agent.description}
                </p>
            </div>

            {/* ── Live Message ─────────────────── */}
            {/* Only shown when agent has a message */}
            {message && (
                <div className={`
                    text-[10px] font-medium leading-relaxed
                    px-3 py-2 rounded-lg
                    ${isRunning
                        ? 'bg-white text-[#FF4B4B] border border-red-100'
                        : 'bg-white text-slate-500 border border-slate-100'
                    }
                `}>
                    {message}
                </div>
            )}

        </div>
    );
}


// ─────────────────────────────────────────
// AGENT PANEL COMPONENT
// Shows all 6 agents as cards in a row
// Updates live via WebSocket events
// ─────────────────────────────────────────

export default function AgentPanel() {

    const {
        agentEvents,
        pipelineStatus,
    } = usePipelineStore();

    // Don't render panel if pipeline hasn't started
    if (pipelineStatus === 'idle') return null;

    return (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">

            {/* ── Header ───────────────────────── */}
            <div className="flex items-center gap-2 mb-6">
                <Wrench size={14} className="text-slate-400" />
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Agent Activity
                </p>

                {/* Live indicator when running */}
                {pipelineStatus === 'running' && (
                    <div className="flex items-center gap-1.5 ml-auto">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#FF4B4B] animate-ping" />
                        <p className="text-[10px] font-black text-[#FF4B4B] uppercase tracking-widest">
                            Live
                        </p>
                    </div>
                )}
            </div>

            {/* ── Agent Cards Grid ─────────────── */}
            <div className="grid grid-cols-6 gap-3">
                {AGENTS.map((agent) => {
                    const status  = getAgentStatus(agent.id, agentEvents);
                    const message = getAgentMessage(agent.id, agentEvents);

                    return (
                        <AgentCard
                            key={agent.id}
                            agent={agent}
                            status={status}
                            message={message}
                        />
                    );
                })}
            </div>

        </div>
    );
}





