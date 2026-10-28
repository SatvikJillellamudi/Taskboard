import { useEffect, useRef, useState } from "react";
import { WS_URL, getToken } from "./api.js";

// Keeps a WebSocket open to /ws/boards/{id} and reconnects with backoff if it drops.
// status: "connecting" | "live" | "offline"
export function useBoardSocket(boardId, handlers) {
  const [status, setStatus] = useState("connecting");
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers; // always call the latest handlers without reconnecting

  useEffect(() => {
    let ws;
    let retry = 0;
    let retryTimer;
    let pingTimer;
    let stopped = false;

    function connect() {
      setStatus("connecting");
      ws = new WebSocket(`${WS_URL}/ws/boards/${boardId}?token=${encodeURIComponent(getToken())}`);
      ws.onopen = () => {
        retry = 0;
        setStatus("live");
        pingTimer = setInterval(() => ws.readyState === 1 && ws.send("ping"), 25000);
      };
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        const h = handlersRef.current;
        if (msg.type === "board") h.onBoard?.(msg.board);
        else if (msg.type === "presence") h.onPresence?.(msg.users);
        else if (msg.type === "board_deleted") h.onDeleted?.();
      };
      ws.onclose = (e) => {
        clearInterval(pingTimer);
        if (stopped) return;
        if (e.code === 4401) return handlersRef.current.onUnauthorized?.();
        if (e.code === 4404) return handlersRef.current.onDeleted?.();
        setStatus("offline");
        const delay = Math.min(1000 * 2 ** retry++, 10000); // 1s, 2s, 4s ... capped at 10s
        retryTimer = setTimeout(connect, delay);
      };
    }

    connect();
    return () => {
      stopped = true;
      clearTimeout(retryTimer);
      clearInterval(pingTimer);
      ws?.close();
    };
  }, [boardId]);

  return status;
}
