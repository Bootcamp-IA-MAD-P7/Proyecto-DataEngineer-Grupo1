import { useEffect, useState } from "react";
import { getHealth, ApiUnavailableError } from "../services/api";

type HealthState = "checking" | "online" | "offline";

export function useHealth(): { state: HealthState } {
  const [state, setState] = useState<HealthState>("checking");

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setInterval> | undefined;

    async function check() {
      try {
        const res = await getHealth();
        if (active) setState(res.status === "ok" ? "online" : "offline");
      } catch {
        if (active) setState("offline");
      }
    }

    check();
    timer = setInterval(check, 30_000);

    return () => {
      active = false;
      if (timer) clearInterval(timer);
    };
  }, []);

  return { state };
}
