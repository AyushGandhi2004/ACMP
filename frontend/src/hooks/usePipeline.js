import { runPipeline } from '../services/api';
import usePipelineStore from '../store/pipelineStore';


// ─────────────────────────────────────────
// usePipeline HOOK
// Orchestrates the full pipeline run
// from the frontend perspective
//
// Responsibilities:
// - Validate input before submission
// - Call POST /api/v1/pipeline/run
// - Store session_id in Zustand
// - Update pipeline status
// - Handle submission errors
//
// WebSocket connection is handled separately
// by useWebSocket hook which watches sessionId
//
// Usage:
//   const { startPipeline, isLoading } = usePipeline()
// ─────────────────────────────────────────

const usePipeline = () => {

    const {
        originalCode,
        selectedLanguage,
        setSessionId,
        setPipelineStatus,
        setIsLoading,
        setError,
        resetPipeline,
        isLoading,
        pipelineStatus,
    } = usePipelineStore();


    // ─────────────────────────────────────────
    // INPUT VALIDATION
    // Check all conditions before submitting
    // Returns error message or null if valid
    // ─────────────────────────────────────────

    const validateInput = (code) => {
        if (!code || code.trim() === '') {
            return 'Please provide code to modernize';
        }

        if (code.trim().length < 10) {
            return 'Code is too short to modernize';
        }

        if (code.trim().length > 50000) {
            return 'Code is too large. Maximum 50,000 characters allowed';
        }

        return null; // null means valid
    };


    // ─────────────────────────────────────────
    // START PIPELINE
    // Main function called by Run Pipeline button
    // ─────────────────────────────────────────

    const startPipeline = async () => {
        const code = originalCode;
        const language = selectedLanguage === 'auto'
            ? null
            : selectedLanguage;

        // ── Step 1: Validate input ────────────
        const validationError = validateInput(code);
        if (validationError) {
            setError(validationError);
            return;
        }

        // ── Step 2: Reset previous results ────
        // Clear all previous agent events,
        // modern code and status before new run
        resetPipeline();

        // ── Step 3: Set loading state ─────────
        setIsLoading(true);
        setPipelineStatus('running');

        try {
            // ── Step 4: Call backend API ──────
            // Returns session_id immediately
            // Pipeline runs in background
            const response = await runPipeline(code, language);

            const sessionId = response.session_id;

            if (!sessionId) {
                throw new Error('No session ID returned from backend');
            }

            // ── Step 5: Store session ID ──────
            // useWebSocket hook watches this value
            // When it changes — WebSocket connects
            // automatically to the new session
            setSessionId(sessionId);

        } catch (err) {
            // ── Handle submission error ───────
            const errorMessage =
                err.response?.data?.detail ||
                err.message ||
                'Failed to start pipeline. Is the backend running?';

            setError(errorMessage);
            setPipelineStatus('failed');
            setIsLoading(false);
        }
    };


    // ─────────────────────────────────────────
    // RETRY PIPELINE
    // Called from the error Banner
    // Resets everything and starts fresh
    // with the same code and language
    // ─────────────────────────────────────────

    const retryPipeline = async () => {
        await startPipeline();
    };


    // ─────────────────────────────────────────
    // CAN SUBMIT CHECK
    // Derived boolean for disabling the
    // Run Pipeline button in the UI
    // ─────────────────────────────────────────

    const canSubmit =
        originalCode.trim().length >= 10 &&
        !isLoading &&
        pipelineStatus !== 'running';


    return {
        startPipeline,
        retryPipeline,
        canSubmit,
        isLoading,
        pipelineStatus,
    };
};

export default usePipeline;
