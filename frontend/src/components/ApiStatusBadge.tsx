import { useHealth } from "../hooks/useHealth";

export function ApiStatusBadge() {
  const { state } = useHealth();

  const dot: Record<string, { color: string; label: string }> = {
    checking: { color: "#888", label: "Checking…" },
    online: { color: "#22c55e", label: "API online" },
    offline: { color: "#ef4444", label: "API offline" },
  };

  const { color, label } = dot[state];

  return (
    <span aria-live="polite" style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
      <span
        aria-hidden="true"
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          backgroundColor: color,
          display: "inline-block",
        }}
      />
      {label}
    </span>
  );
}
