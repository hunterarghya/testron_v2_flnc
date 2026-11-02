// The one theme file: components take colours from these names, never from raw values
// (frontend_spec.md §2).
export default defineAppConfig({
  ui: {
    colors: {
      primary: 'blue',
      neutral: 'slate',
      success: 'green',
      warning: 'amber',
      error: 'red',
    },
  },
  icon: {
    // An icon missing from the bundle shows as blank in development instead of being
    // fetched from the Iconify API, which the CSP blocks anyway
    fallbackToApi: false,
  },
})
