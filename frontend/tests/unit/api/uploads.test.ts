import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import { ApiProblem } from '~/api/problems'
import { imageProblem, MAX_IMAGE_BYTES, uploadImage } from '~/api/uploads'
import { type FakeApi, ok } from '../../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const SIGNED = {
  token: 't-1', expire: 1_800_000_000, signature: 'sig', public_key: 'pk',
  url_endpoint: '/dev-media', folder: '/tests/2026/11',
  // The browser resolves the relative /dev-media/upload itself; tests have no page address
  upload_url: 'http://localhost/dev-media/upload',
}

function png(size = 10): File {
  return new File([new Uint8Array(size)], 'cell.png', { type: 'image/png' })
}

function answer(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status })
}

describe('image uploads', () => {
  beforeEach(() => {
    fake.POST.mockReset().mockImplementation(() => ok(SIGNED))
  })

  it.each([
    [new File(['<svg/>'], 'a.svg', { type: 'image/svg+xml' }), 'image_type'],
    [png(MAX_IMAGE_BYTES + 1), 'image_too_large'],
  ])('refuses %s before asking for a signature', async (file, code) => {
    expect(imageProblem(file)?.code).toBe(code)
    await expect(uploadImage(file, vi.fn())).rejects.toMatchObject({ code })
    expect(fake.POST).not.toHaveBeenCalled()
  })

  it('sends the file with the signature to the upload address', async () => {
    const send = vi.fn((_request: Request) => Promise.resolve(answer(200, { fileId: 'f1', url: '/dev-media/tests/2026/11/f1.png' })))

    const uploaded = await uploadImage(png(), send)

    expect(uploaded).toEqual({ fileId: 'f1', url: '/dev-media/tests/2026/11/f1.png' })
    const request = send.mock.calls[0]![0]
    expect(request.url).toContain('/dev-media/upload')
    const form = await request.formData()
    expect([form.get('token'), form.get('expire'), form.get('folder'), form.get('publicKey')])
      .toEqual(['t-1', '1800000000', '/tests/2026/11', 'pk'])
  })

  it('a refused upload is an upload_failed problem', async () => {
    const send = vi.fn(() => Promise.resolve(answer(400, { message: 'refused' })))

    await expect(uploadImage(png(), send)).rejects.toBeInstanceOf(ApiProblem)
    await expect(uploadImage(png(), send)).rejects.toMatchObject({ code: 'upload_failed' })
  })

  it('no connection is a network problem', async () => {
    const send = vi.fn(() => Promise.reject(new TypeError('offline')))

    await expect(uploadImage(png(), send)).rejects.toMatchObject({ code: 'network_error' })
  })
})
