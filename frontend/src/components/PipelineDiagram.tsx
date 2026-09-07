export function PipelineDiagram() {
  const steps = ["Kafka", "MongoDB", "ETL", "PostgreSQL", "API", "Frontend"];

  return (
    <figure>
      <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: "0.4rem" }}>
        {steps.map((step, i) => (
          <span key={step} style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <span
              style={{
                padding: "0.4rem 0.8rem",
                borderRadius: 6,
                border: ["API", "Frontend"].includes(step)
                  ? "2px solid #c05621"
                  : "1px solid #999",
                background: ["API", "Frontend"].includes(step)
                  ? "#fff3e6"
                  : "#f9f9f9",
                fontWeight: ["API", "Frontend"].includes(step) ? 700 : 400,
                fontSize: "0.9rem",
              }}
            >
              {step}
            </span>
            {i < steps.length - 1 && (
              <span aria-hidden="true" style={{ color: "#999" }}>
                →
              </span>
            )}
          </span>
        ))}
      </div>
      <figcaption style={{ marginTop: "0.6rem", fontSize: "0.85rem", color: "#555" }}>
        Events are ingested, stored, processed, consolidated and served — this app
        reads only the final consolidated layer.
      </figcaption>
    </figure>
  );
}
