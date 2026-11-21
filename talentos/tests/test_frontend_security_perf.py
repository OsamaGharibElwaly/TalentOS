from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
SRC = FRONTEND / "src"


def _read(relative: str) -> str:
    return (SRC / relative).read_text(encoding="utf-8")


def test_next_config_sets_full_security_header_suite() -> None:
    text = (FRONTEND / "next.config.ts").read_text(encoding="utf-8")
    text += _read("proxy.ts")
    for token in (
        "Content-Security-Policy",
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "connect-src 'self'",
        "img-src 'self'",
        "frame-ancestors 'none'",
        "X-Content-Type-Options",
        "nosniff",
        "X-Frame-Options",
        "DENY",
        "Referrer-Policy",
        "strict-origin-when-cross-origin",
        "Permissions-Policy",
        "Cache-Control",
        "no-store",
        "poweredByHeader: false",
    ):
        assert token in text, token

    proxy_text = _read("proxy.ts")
    for token in ("x-nonce", "randomUUID", "strict-dynamic", "NextResponse.next"):
        assert token in proxy_text, token
    assert "Content-Security-Policy" not in (FRONTEND / "next.config.ts").read_text(encoding="utf-8")


def test_external_urls_are_allowlisted_and_links_are_rel_hardened() -> None:
    text = _read("lib/security.ts")
    assert "export function sanitizeExternalUrl" in text
    for token in ("new URL(", "'https:'", "'http:'", "javascript:", "data:", "vbscript:"):
        assert token in text, token
    assert "export function externalLinkProps" in text
    assert "rel: 'noopener noreferrer'" in text


def test_untrusted_text_is_never_injected_as_html() -> None:
    for path in SRC.rglob("*"):
        if path.suffix in {".ts", ".tsx"}:
            assert "dangerouslySetInnerHTML" not in path.read_text(encoding="utf-8"), path
    assert "<mark key" in _read("components/ui/SafeText.tsx")
    assert "<SafeText" in _read("components/candidates/SplitEvidenceViewer.tsx")
    assert "<SafeText" in _read("components/search/TalentSearchWorkbench.tsx")


def test_request_dedup_cache_debounce_and_abort_are_wired() -> None:
    cache = _read("lib/query-cache.ts")
    for token in ("cachedGet", "inFlight", "Date.now() + ttlMs", "invalidateCache", "debounce", "setTimeout"):
        assert token in cache, token

    client = _read("lib/api-client.ts")
    for token in ("cachedGet(", "invalidateCache(", "csrfHeaders()", "signal,"):
        assert token in client, token
    session = _read("lib/auth-session.ts")
    assert "document.cookie" in session
    assert "X-CSRF-Token" in session
    assert "X-Requested-With" in session

    workbench = _read("components/search/TalentSearchWorkbench.tsx")
    for token in ("debounce(", "250", "AbortController", ".abort()", "next.signal"):
        assert token in workbench, token

    viewer = _read("components/candidates/SplitEvidenceViewer.tsx")
    for token in ("useMemo", "useCallback", "memo(SplitEvidenceViewer)"):
        assert token in viewer, token
    assert "PAGE_SIZE" in _read("app/candidates/page.tsx")


def test_command_palette_and_design_tokens_exist() -> None:
    palette = _read("components/ui/CommandPalette.tsx")
    for token in ("event.metaKey", "event.ctrlKey", "'k'", "Escape", 'role="dialog"'):
        assert token in palette, token
    assert "CommandPalette" in _read("components/shell/AppShell.tsx")

    css = _read("app/globals.css")
    for token in (
        ":focus-visible",
        "prefers-reduced-motion",
        "--space-3",
        "--elevation",
        ".skeleton",
        "@keyframes shimmer",
    ):
        assert token in css, token
    assert "CandidateListSkeleton" in _read("app/candidates/page.tsx")
