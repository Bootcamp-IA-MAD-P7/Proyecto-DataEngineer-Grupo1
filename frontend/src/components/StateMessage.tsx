interface StateMessageProps {
  kind: "loading" | "empty" | "unavailable" | "error";
  detail?: string;
  criteria?: string;
}

export function StateMessage({ kind, detail, criteria }: StateMessageProps) {
  if (kind === "loading") {
    return (
      <div role="status" aria-busy="true">
        Loading…
      </div>
    );
  }

  if (kind === "empty") {
    return (
      <div role="alert">
        No results found{criteria ? ` matching: ${criteria}` : ""}.
      </div>
    );
  }

  if (kind === "unavailable") {
    return (
      <div role="alert">
        Cannot reach the API. It may be down or starting up.
      </div>
    );
  }

  return (
    <div role="alert">Request failed: {detail ?? "unknown error"}</div>
  );
}
