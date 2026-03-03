import { useEffect, useRef } from 'react';
import { getWebSocketUrl } from '../services/api';
import usePipelineStore from '../store/pipelineStore';


// ─────────────────────────────────────────
// useWebSocket HOOK
// Manages the entire WebSocket lifecycle
// for a single pipeline run
//
// Connects when sessionId is available
// Disconnects when component unmounts
// Automatically handles all message types
//
// Usage:
//   useWebSocket(sessionId)
// ─────────────────────────────────────────

const useWebSocket = (sessionId) => {

    // Keep a ref to the WebSocket instance
    // so we can close it on cleanup
    // useRef persists across renders without
    // causing re-renders when it changes
    const wsRef = useRef(null);

    const {
        addAgentEvent,
        setModernCode,
        setTransformationPlan,
        setValidationLogs,
        setDetectedMeta,
        setPipelineStatus,
        setIsLoading,
        setError,
    } = usePipelineStore();


    useEffect(() => {

        // ── Don't connect without a session ──────
        if (!sessionId) return;

        // ── Build WebSocket URL ───────────────────
        const url = getWebSocketUrl(sessionId);

        // ── Create WebSocket connection ───────────
        const ws = new WebSocket(url);
        wsRef.current = ws;


        // ─────────────────────────────────────────
        // ON OPEN
        // Connection established successfully
        // ─────────────────────────────────────────
        ws.onopen = () => {
            console.log(`WebSocket connected for session: ${sessionId}`);

            // Start ping interval to keep connection alive
            // Send ping every 30 seconds
            const pingInterval = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                }
            }, 30000);

            // Store interval on ws object for cleanup
            ws.pingInterval = pingInterval;
        };


        // ─────────────────────────────────────────
        // ON MESSAGE
        // Handle all incoming events from backend
        // Two types of messages:
        // 1. AgentEvent — live agent updates
        // 2. pipeline_complete — final result
        // 3. pipeline_error — pipeline failed
        // 4. pong — response to our ping
        // ─────────────────────────────────────────
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // ── Pong response — ignore ────────
                if (data.type === 'pong') return;


                // ── Pipeline complete ─────────────
                // Final result received
                if (data.type === 'pipeline_complete') {
                    const result = data.result || {};

                    // Update all result state
                    setModernCode(result.modern_code || '');
                    setTransformationPlan(result.transformation_plan || {});
                    setValidationLogs(result.validation_logs || '');
                    setDetectedMeta(
                        result.language || null,
                        result.framework || null
                    );

                    // Set final status
                    const finalStatus = result.status === 'validation_passed' ||
                                       result.status === 'success'
                        ? 'success'
                        : 'failed';

                    setPipelineStatus(finalStatus);
                    setIsLoading(false);
                    return;
                }


                // ── Pipeline error ────────────────
                // Something went wrong in the pipeline
                if (data.type === 'pipeline_error') {
                    setError(data.message || 'Pipeline failed unexpectedly');
                    setPipelineStatus('failed');
                    setIsLoading(false);
                    return;
                }


                // ── Agent event ───────────────────
                // Regular agent status update
                // Has: agent_name, status, message, data
                if (data.agent_name) {
                    addAgentEvent(data);

                    // Extract detected metadata from
                    // profiler agent's completed event
                    if (
                        data.agent_name === 'profiler' &&
                        data.status === 'completed' &&
                        data.data
                    ) {
                        setDetectedMeta(
                            data.data.language || null,
                            data.data.framework || null
                        );
                    }
                }

            } catch (err) {
                // Non JSON message — ignore silently
                console.warn('WebSocket non-JSON message:', event.data);
            }
        };


        // ─────────────────────────────────────────
        // ON ERROR
        // WebSocket connection error
        // ─────────────────────────────────────────
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setError('WebSocket connection error. Please try again.');
            setPipelineStatus('failed');
            setIsLoading(false);
        };


        // ─────────────────────────────────────────
        // ON CLOSE
        // Connection closed — could be normal or unexpected
        // ─────────────────────────────────────────
        ws.onclose = (event) => {
            console.log(`WebSocket closed. Code: ${event.code}`);

            // Clear ping interval
            if (ws.pingInterval) {
                clearInterval(ws.pingInterval);
            }

            // Code 1000 = normal closure
            // Any other code = unexpected closure
            if (event.code !== 1000) {
                const { pipelineStatus } = usePipelineStore.getState();

                // Only mark as failed if pipeline was still running
                // Don't override a completed success/failed status
                if (pipelineStatus === 'running') {
                    setError('Connection lost. Check results tab for final status.');
                    setPipelineStatus('failed');
                    setIsLoading(false);
                }
            }
        };


        // ─────────────────────────────────────────
        // CLEANUP FUNCTION
        // Runs when component unmounts OR
        // when sessionId changes
        // Always close WebSocket on cleanup
        // ─────────────────────────────────────────
        return () => {
            if (ws.pingInterval) {
                clearInterval(ws.pingInterval);
            }
            if (ws.readyState === WebSocket.OPEN ||
                ws.readyState === WebSocket.CONNECTING) {
                ws.close(1000, 'Component unmounted');
            }
        };

    }, [sessionId]);
    // Only re-run when sessionId changes
    // New session = new WebSocket connection


    // ─────────────────────────────────────────
    // MANUAL CLOSE FUNCTION
    // Exposed so components can close
    // the connection explicitly if needed
    // ─────────────────────────────────────────
    const closeConnection = () => {
        if (wsRef.current &&
            wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.close(1000, 'Manual close');
        }
    };

    return { closeConnection };
};

export default useWebSocket;