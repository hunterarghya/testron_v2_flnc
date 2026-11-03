// Every test runs fullscreen (domain_model.md §5.8). Entering needs a user gesture, so the
// gate's Start button calls it; where a browser can't (iPhone Safari), the test goes on
// without it (frontend_spec.md §5.4).

export async function enterFullscreen(): Promise<void> {
  if (document.fullscreenElement || !document.documentElement.requestFullscreen) return
  try {
    await document.documentElement.requestFullscreen()
    await holdEscape()
  }
  catch {
    // Refused or unsupported: the test continues in the window
  }
}

// Chromium's Keyboard Lock: Esc must then be held to leave fullscreen (PRD §8). Elsewhere
// there is no such API and nothing extra happens.
interface KeyboardLock {
  lock: (keys: string[]) => Promise<void>
}

async function holdEscape(): Promise<void> {
  const keyboard = (navigator as Navigator & { keyboard?: KeyboardLock }).keyboard
  await keyboard?.lock(['Escape'])
}

/** Fullscreen exists here (not on iPhone Safari, frontend_spec.md §5.4). */
export function canFullscreen(): boolean {
  return Boolean(document.fullscreenEnabled)
}

export async function exitFullscreen(): Promise<void> {
  if (!document.fullscreenElement) return
  try {
    await document.exitFullscreen()
  }
  catch {
    // Already left
  }
}
