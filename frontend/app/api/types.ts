// Friendly names for the generated API types (never edit schema.d.ts itself).
import type { components } from '~/api/schema'

type Schemas = components['schemas']

export type SessionUser = Schemas['SessionUserOut']
export type Session = Schemas['SessionOut']
export type StudentRow = Schemas['StudentRowOut']
export type StudentPage = Schemas['Page_StudentRowOut_']
export type BulkResult = Schemas['BulkResultOut']
export type ListedStatus = StudentRow['status']
export type StudentDetail = Schemas['StudentDetailOut']
export type GroupRef = Schemas['GroupRefOut']
export type Group = Schemas['GroupOut']
export type GroupDetail = Schemas['GroupDetailOut']
export type GroupMember = Schemas['GroupMemberOut']
export type Tag = Schemas['TagOut']
export type TagUsage = Schemas['TagUsageOut']
export type TagKind = Tag['kind']
export type AppInfo = Schemas['AppInfoOut']
export type AppSettings = Schemas['AppSettingsOut']
export type AppSettingsChanges = Schemas['AppSettingsPatchIn']
export type UploadSignature = Schemas['UploadSignatureOut']
export type Badges = Schemas['BadgesOut']
