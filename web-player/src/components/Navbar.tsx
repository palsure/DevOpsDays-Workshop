interface NavbarProps {
  onHome: () => void;
  onPipeline?: () => void;
}

export function Navbar({ onHome, onPipeline }: NavbarProps) {
  return (
    <nav className="navbar">
      <button className="navbar-logo" onClick={onHome} type="button" aria-label="Go home">
        <span className="navbar-logo-icon">▶</span>
        <span className="navbar-logo-text">StreamApp</span>
      </button>
      <ul className="navbar-links">
        <li><button type="button" onClick={onHome}>Home</button></li>
        {onPipeline && (
          <li>
            <button type="button" onClick={onPipeline}>Pipeline</button>
          </li>
        )}
        <li><button type="button" onClick={onHome}>Movies</button></li>
        <li><button type="button" onClick={onHome}>Shows</button></li>
        <li><button type="button" onClick={onHome}>Live</button></li>
      </ul>
      <div className="navbar-actions">
        <button className="navbar-search" type="button" aria-label="Search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </button>
        <div className="navbar-avatar" aria-label="Profile">
          <span>QE</span>
        </div>
      </div>
    </nav>
  );
}
