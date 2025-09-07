import { useRef, useState, useEffect, useCallback } from "react";

export function useWebSocketRequest(url, onMessage, protocols) {
    const socketRef = useRef(null);
    const [isReady, setIsReady] = useState(false);
    const [error, setError] = useState(null);
    const queueRef = useRef([]);

    useEffect(() => {
        const socket = new WebSocket(url, protocols);
        socketRef.current = socket;

        socket.onopen = () => {
            setIsReady(true);
            queueRef.current.forEach(msg => socket.send(JSON.stringify(msg)));
            queueRef.current = [];
        };

        socket.onmessage = event => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (e) {
                console.error("WebSocket parse error", e);
            }
        };

        socket.onerror = e => {
            console.error("WebSocket error", e);
            setError(e);
        };

        socket.onclose = () => {
            setIsReady(false);
        };

        return () => {
            if (
                socket.readyState === WebSocket.OPEN ||
                socket.readyState === WebSocket.CONNECTING
            ) {
                socket.close(1000, "Component unmounted");
            }
        };
    }, [url, protocols, onMessage]);
    
    const sendRequest = useCallback(
        payload => {
            if (socketRef.current?.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify(payload));
            } else {
                queueRef.current.push(payload);
            }
        },
        []
    );

    return { sendRequest, isReady, error };
}