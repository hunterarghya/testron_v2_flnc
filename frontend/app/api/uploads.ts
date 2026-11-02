// Image uploads go from the browser straight to storage (ImageKit, or the local dev stand-in),
// with a signature from our API (editor_content_spec.md §5.1, ADR-060). Our server never
// sees the file.
import { api, unwrap } from '~/api/client'
import { ApiProblem, networkProblem } from '~/api/problems'
import type { FetchFn } from '~/api/retry'

export const IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/gif']
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024

export interface UploadedImage {
  fileId: string
  url: string
}

/** Checked before asking for a signature, so the teacher hears at once. */
export function imageProblem(file: File): ApiProblem | null {
  if (!IMAGE_TYPES.includes(file.type)) {
    return new ApiProblem({ status: 0, code: 'image_type', detail: file.type })
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return new ApiProblem({ status: 0, code: 'image_too_large', detail: String(file.size) })
  }
  return null
}

export async function uploadImage(file: File, send: FetchFn = request => fetch(request)): Promise<UploadedImage> {
  const problem = imageProblem(file)
  if (problem) {
    throw problem
  }
  const signed = await unwrap(api.POST('/api/v1/admin/media/upload-signature', {
    body: { file_name: file.name, mime: file.type, size_bytes: file.size },
  }))
  const form = new FormData()
  form.append('file', file)
  form.append('fileName', file.name)
  form.append('publicKey', signed.public_key)
  form.append('signature', signed.signature)
  form.append('expire', String(signed.expire))
  form.append('token', signed.token)
  form.append('folder', signed.folder)
  form.append('useUniqueFileName', 'true')
  return readUploaded(await sendForm(send, new Request(signed.upload_url, { method: 'POST', body: form })))
}

async function sendForm(send: FetchFn, request: Request): Promise<Response> {
  try {
    return await send(request)
  }
  catch {
    throw networkProblem()
  }
}

async function readUploaded(response: Response): Promise<UploadedImage> {
  const body: unknown = await response.json().catch(() => null)
  const uploaded = body as Partial<UploadedImage> | null
  if (!response.ok || typeof uploaded?.url !== 'string' || typeof uploaded.fileId !== 'string') {
    throw new ApiProblem({ status: response.status, code: 'upload_failed', detail: response.statusText })
  }
  return { fileId: uploaded.fileId, url: uploaded.url }
}
