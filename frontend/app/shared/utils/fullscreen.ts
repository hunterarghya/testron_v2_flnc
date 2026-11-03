// Every test runs fullscreen (domain_model.md §5.8). Entering needs a user gesture, so the
// gate's Start button calls it; where a browser can't (iPhone Safari), the test goes on
// without it (frontend_spec.md §5.4).

export async function enterFullscreen(): Promise<void> {
  if (document.fullscreenElement || !document.documentElement.requestFullscreen) return
  try {
    await document.documentElement.requestFullscreen()
  }
  catch {
    // Refused or unsupported: the test continues in the window
  }
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
