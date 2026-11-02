// Every API error arrives as problem+json and is thrown as one ApiProblem
// (api_contract.md §1, frontend_spec.md §3).

export interface FieldError {
  field: string
  code: string
  message: string
}

export interface ProblemInit {
  status: number
  code: string
  detail: string
  errors?: FieldError[]
  context?: Record<string, unknown>
  traceId?: string | null
}

export class ApiProblem extends Error {
  readonly status: number
  readonly code: string
  readonly detail: string
  readonly errors: FieldError[]
  readonly context: Record<string, unknown>
  // Shown to the user as a "reference code" they can quote
  readonly traceId: string | null

  constructor(init: ProblemInit) {
    super(`${init.status} ${init.code}: ${init.detail}`)
    this.name = 'ApiProblem'
    this.status = init.status
    this.code = init.code
    this.detail = init.detail
    this.errors = init.errors ?? []
    this.context = init.context ?? {}
    this.traceId = init.traceId ?? null
  }
}

// The request never reached the server (offline, DNS, connection reset)
export const NETWORK_ERROR = 'network_error'

export function networkProblem(): ApiProblem {
  return new ApiProblem({ status: 0, code: NETWORK_ERROR, detail: 'No connection to the server' })
}

export async function problemFromResponse(response: Response): Promise<ApiProblem> {
  const body = await readJsonObject(response)
  return new ApiProblem({
    status: response.status,
    code: typeof body.code === 'string' ? body.code : 'internal_error',
    detail: typeof body.detail === 'string' ? body.detail : response.statusText,
    errors: Array.isArray(body.errors) ? (body.errors as FieldError[]) : [],
    context: isObject(body.context) ? body.context : {},
    traceId: typeof body.trace_id === 'string' ? body.trace_id : response.headers.get('X-Request-ID'),
  })
}

/** For `catch` blocks: an ApiProblem is returned, anything else is a bug and is re-thrown. */
export function toProblem(error: unknown): ApiProblem {
  if (error instanceof ApiProblem) {
    return error
  }
  throw error
}

async function readJsonObject(response: Response): Promise<Record<string, unknown>> {
  try {
    const body: unknown = await response.json()
    return isObject(body) ? body : {}
  }
  catch {
    // Not JSON (a proxy's HTML error page, an empty body): the status alone describes it
    return {}
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
