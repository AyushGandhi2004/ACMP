import { create } from 'zustand';

// ─────────────────────────────────────────
// PIPELINE STORE
// Global state for the entire pipeline UI
// Shared between Home page and all components
// Never recreate this — import and use directly
//
// Usage in any component:
//   import usePipelineStore from '../store/pipelineStore'
//   const { originalCode, setOriginalCode } = usePipelineStore()
// ─────────────────────────────────────────

const usePipelineStore = create((set, get) => ({

    // ─────────────────────────────────────────
    // INPUT STATE
    // What the user submits
    // ─────────────────────────────────────────
    originalCode:     "",
    selectedLanguage: "auto",
    selectedFile:     null,
    inputMode:        "paste",  // "paste" | "upload"


    // ─────────────────────────────────────────
    // PIPELINE STATE
    // Tracks the running pipeline
    // ─────────────────────────────────────────
    sessionId:        null,
    pipelineStatus:   "idle",
    // idle | running | success | failed
    isLoading:        false,
    error:            null,


    // ─────────────────────────────────────────
    // AGENT STATE
    // Live updates from WebSocket
    // ─────────────────────────────────────────
    agentEvents:      [],
    // List of AgentEvent objects:
    // { agent_name, status, message, data }

    activeAgent:      null,
    // Name of currently running agent


    // ─────────────────────────────────────────
    // RESULT STATE
    // Final pipeline output
    // ─────────────────────────────────────────
    modernCode:           "",
    transformationPlan:   {},
    validationLogs:       "",
    detectedLanguage:     null,
    detectedFramework:    null,


    // ─────────────────────────────────────────
    // INPUT ACTIONS
    // ─────────────────────────────────────────

    setOriginalCode: (code) => set({ originalCode: code }),

    setSelectedLanguage: (language) => set({ selectedLanguage: language }),

    setSelectedFile: (file) => set({ selectedFile: file }),

    setInputMode: (mode) => set({ inputMode: mode }),


    // ─────────────────────────────────────────
    // PIPELINE ACTIONS
    // ─────────────────────────────────────────

    setSessionId: (id) => set({ sessionId: id }),

    setPipelineStatus: (status) => set({ pipelineStatus: status }),

    setIsLoading: (loading) => set({ isLoading: loading }),

    setError: (error) => set({ error: error }),


    // ─────────────────────────────────────────
    // AGENT ACTIONS
    // ─────────────────────────────────────────

    addAgentEvent: (event) => set((state) => ({
        agentEvents: [...state.agentEvents, event],
        activeAgent: event.status === 'running'
            ? event.agent_name
            : state.activeAgent
        // Only update activeAgent when status is "running"
        // "completed" and "failed" don't change the active highlight
    })),

    setActiveAgent: (agentName) => set({ activeAgent: agentName }),


    // ─────────────────────────────────────────
    // RESULT ACTIONS
    // ─────────────────────────────────────────

    setModernCode: (code) => set({ modernCode: code }),

    setTransformationPlan: (plan) => set({ transformationPlan: plan }),

    setValidationLogs: (logs) => set({ validationLogs: logs }),

    setDetectedMeta: (language, framework) => set({
        detectedLanguage: language,
        detectedFramework: framework
    }),


    // ─────────────────────────────────────────
    // RESET ACTION
    // Called when starting a new pipeline run
    // Clears all previous results and events
    // Preserves input (code and language)
    // ─────────────────────────────────────────

    resetPipeline: () => set({
        sessionId:          null,
        pipelineStatus:     "idle",
        isLoading:          false,
        error:              null,
        agentEvents:        [],
        activeAgent:        null,
        modernCode:         "",
        transformationPlan: {},
        validationLogs:     "",
        detectedLanguage:   null,
        detectedFramework:  null,
    }),
    // Note: originalCode, selectedLanguage,
    // selectedFile and inputMode are NOT reset
    // so user doesn't have to re-upload their file


    // ─────────────────────────────────────────
    // FULL RESET ACTION
    // Resets everything including inputs
    // Called when user wants a fresh start
    // ─────────────────────────────────────────

    fullReset: () => set({
        originalCode:       "",
        selectedLanguage:   "auto",
        selectedFile:       null,
        inputMode:          "paste",
        sessionId:          null,
        pipelineStatus:     "idle",
        isLoading:          false,
        error:              null,
        agentEvents:        [],
        activeAgent:        null,
        modernCode:         "",
        transformationPlan: {},
        validationLogs:     "",
        detectedLanguage:   null,
        detectedFramework:  null,
    }),


    // ─────────────────────────────────────────
    // COMPUTED HELPERS
    // Derived values used across components
    // ─────────────────────────────────────────

    isRunning: () => get().pipelineStatus === "running",

    isComplete: () =>
        get().pipelineStatus === "success" ||
        get().pipelineStatus === "failed",

    hasResult: () => get().modernCode !== "",

}));

export default usePipelineStore;