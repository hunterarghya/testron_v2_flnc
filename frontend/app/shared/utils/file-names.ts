// Export file names (domain_model.md §6.6): characters Windows or macOS refuse are removed,
// the name is kept to 150 characters, and the date is in India time.

export const MAX_NAME_LENGTH = 150
const NOT_IN_NAMES = /[<>:"/\\|?*\p{Cc}]/gu

/** "2026-11-12", the India date of an instant (now by default). */
export function indiaDate(at: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata' }).format(at)
}

/** Joins the parts with " - ", cleans them, and keeps the extension whole. */
export function fileName(parts: string[], extension: string): string {
  const clean = parts.map(p => p.replace(NOT_IN_NAMES, '').replace(/\s+/g, ' ').trim()).filter(Boolean)
  const suffix = `.${extension}`
  return clean.join(' - ').slice(0, MAX_NAME_LENGTH - suffix.length) + suffix
}

/** "{Student} - {Title} - {YYYY-MM-DD}[ - Take N].html": the take only from the second on. */
export function answerSheetName(student: string, title: string, take: number, at?: Date): string {
  return fileName([student, title, indiaDate(at), ...(take > 1 ? [`Take ${take}`] : [])], 'html')
}

export function answerKeyName(title: string, at?: Date): string {
  return fileName([title, 'Answer Key', indiaDate(at)], 'html')
}

export function answerSheetsZipName(title: string, at?: Date): string {
  return fileName([title, indiaDate(at), 'Answer Sheets'], 'zip')
}

/** Hands a file to the browser's downloads. */
export function saveFile(name: string, contents: Blob): void {
  const url = URL.createObjectURL(contents)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
