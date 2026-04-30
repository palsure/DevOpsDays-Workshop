import { useState } from 'react';
import { HomePage } from './pages/HomePage';
import { DetailPage } from './pages/DetailPage';
import { Navbar } from './components/Navbar';
import { CATALOG, type Video } from './data/catalog';
import { parseDemoScenario } from './demo/scenarios';
import './App.css';

// ── E2E bypass ─────────────────────────────────────────────────────
// When ?e2e_autoplay=1 is present, skip the streaming UI and go
// straight to the player so Playwright tests continue to work.
function getE2EVideo(): { video: Video; autoPlay: boolean } | null {
  const params = new URLSearchParams(window.location.search);
  const autoPlay = params.get('e2e_autoplay') === '1' || params.get('e2e_autoplay') === 'true';
  if (!autoPlay) return null;

  const scenarioParam = params.get('scenario');
  const scenario      = parseDemoScenario(scenarioParam);

  // Find the catalog video matching the requested scenario, or fall back to first
  const match =
    CATALOG.flatMap(r => r.videos).find(v => v.scenario === scenario) ??
    CATALOG[0].videos[0];

  return { video: match, autoPlay: true };
}

// ── Router state ───────────────────────────────────────────────────
type Route =
  | { page: 'home' }
  | { page: 'detail'; video: Video; autoPlay?: boolean };

export default function App() {
  const e2e = getE2EVideo();

  const [route, setRoute] = useState<Route>(
    e2e ? { page: 'detail', video: e2e.video, autoPlay: e2e.autoPlay } : { page: 'home' },
  );

  const goHome   = () => setRoute({ page: 'home' });
  const goDetail = (v: Video) => setRoute({ page: 'detail', video: v });

  // Play with immediate fullscreen — called from the hero banner Play button.
  // requestFullscreen() must be called synchronously inside the user-gesture handler.
  const goPlay = (v: Video) => {
    document.documentElement.requestFullscreen?.().catch(() => {});
    setRoute({ page: 'detail', video: v, autoPlay: true });
  };

  return (
    <div className="app-shell">
      <Navbar onHome={goHome} />

      {route.page === 'home' && (
        <HomePage onSelect={goDetail} onPlay={goPlay} />
      )}

      {route.page === 'detail' && (
        <DetailPage
          video={route.video}
          onBack={goHome}
          autoPlay={route.autoPlay ?? (e2e?.autoPlay ?? false)}
        />
      )}
    </div>
  );
}
