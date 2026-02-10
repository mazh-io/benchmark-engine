export function PlaygroundSection() {
  return (
    <div className="api-section-sm">
      <div>
        <h2 className="api-section-title">API Playground</h2>
        <p className="api-section-desc">
          Test API calls interactively with our Swagger documentation.
        </p>
      </div>

      <a href="https://mazh.io/api/docs" target="_blank" rel="noreferrer" className="block">
        <div className="api-playground-cta">
          <span className="api-playground-icon">⚡</span>
          <span className="api-playground-label">Open Interactive API Docs →</span>
        </div>
      </a>

      <p className="api-playground-helper">
        Swagger/OpenAPI interface with try-it-out functionality.
        <br />
        No API key required to explore endpoints.
      </p>
    </div>
  );
}
