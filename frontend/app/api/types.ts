// Friendly names for the generated API types (never edit schema.d.ts itself).
import type { components } from '~/api/schema'

type Schemas = components['schemas']

export type SessionUser = Schemas['SessionUserOut']
export type Session = Schemas['SessionOut']
export type StudentRow = Schemas['StudentRowOut']
export type StudentPage = Schemas['Page_StudentRowOut_']
export type BulkResult = Schemas['BulkResultOut']
export type ListedStatus = StudentRow['status']
