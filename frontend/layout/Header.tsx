export function Header() {
  return (
    <header className="header">
      <div className="header-container">
        {/* LEFT */}
        <div className="header-left">
          <div className="header-logo">MAZH</div>

          <div className="header-live-badge">
            <span className="inline-flex h-2 w-2 rounded-full bg-[#22c55e] animate-status-dot" />
            LIVE
          </div>
        </div>

        {/* RIGHT */}
        <div className="header-right">
          <a
            href="https://x.com/mazh_io"
            target="_blank"
            rel="noreferrer"
            className="header-link"
            title="@mazh_io"
          >
            𝕏
          </a>

          <button className="btn-upgrade">
            Early Pro Access €25/mo
          </button>
        </div>
      </div>
    </header>
  );
}
