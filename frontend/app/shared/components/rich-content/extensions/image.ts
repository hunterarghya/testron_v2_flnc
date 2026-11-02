// Images (editor_content_spec.md §2.3, §5): a block with the uploaded file's id, address and
// original size, a display size and an optional caption. While a file uploads, a placeholder
// stands in its place; placeholders are never saved.
import { Node } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import ImageView from '~/shared/components/rich-content/ImageView.vue'
import UploadView from '~/shared/components/rich-content/UploadView.vue'
import { IMAGE_UPLOAD } from '~/shared/components/rich-content/convert'

const attribute = <T>(value: T) => ({ default: value, rendered: false })

export const ImageKitImage = Node.create({
  name: 'image',
  group: 'block',
  atom: true,
  draggable: true,
  addAttributes: () => ({
    provider: attribute('imagekit'),
    fileId: attribute(''),
    src: attribute(''),
    width: attribute(1),
    height: attribute(1),
    size: attribute('M'),
    alt: attribute(''),
    caption: attribute(''),
  }),
  // Pasted <img> never becomes an image node: the paste step uploads or reports them instead
  parseHTML: () => [],
  renderHTML: ({ node }) => ['figure', ['img', { src: node.attrs.src, alt: node.attrs.alt }]],
  addNodeView: () => VueNodeViewRenderer(ImageView),
})

export const ImageUpload = Node.create({
  name: IMAGE_UPLOAD,
  group: 'block',
  atom: true,
  addAttributes: () => ({
    uploadId: attribute(''),
    previewUrl: attribute(''),
    failed: attribute(false),
  }),
  parseHTML: () => [],
  renderHTML: () => ['div', { 'data-type': IMAGE_UPLOAD }],
  addNodeView: () => VueNodeViewRenderer(UploadView),
})
