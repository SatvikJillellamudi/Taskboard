import { useEffect, useState } from "react";
import { API_URL } from "../api.js";

// The free hosting tier puts the API to sleep after 15 idle minutes; the first request
// then takes up to a minute. Instead of looking broken, say what's happening.
export default function ServerWakeNotice() {
  const [state, setState] = useState("checking"); // checking | waking | ready

  useEffect(() => {
    let cancelled = false;
    const slow = setTimeout(() => !cancelled && setState((s) => (s === "checking" ? "waking" : s)), 2500);
    async function ping(attempt = 0) {
      try {
        const res = await fetch(`${API_URL}/health`);
        if (res.ok && !cancelled) return setState("ready");
      } catch {
        /* server still asleep or starting */
      }
      if (!cancelled && attempt < 40) setTimeout(() => ping(attempt + 1), 3000);
    }
    ping();
    return () => {
      cancelled = true;
      clearTimeout(slow);
    };
  }, []);

  if (state !== "waking") return null;
  return (
    <div className="wake-notice" role="status">
      <span className="spinner" aria-hidden="true" />
      Waking up the server. The free hosting tier sleeps when idle, so the first load can take
      up to a minute.
    </div>
  );
}
