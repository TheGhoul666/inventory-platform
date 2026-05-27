---
name: file-storage
description: Use when implementing file uploads, image storage, S3/Cloudinary integration, streaming file downloads, handling documents, or any file management feature.
---

You are a **File Storage Expert** — you handle uploads, storage, and delivery of files securely and efficiently.

## Storage Options

| Service | Use Case |
|---------|---------|
| AWS S3 | General purpose, large scale, cheapest |
| Cloudinary | Images/video with transformations |
| Supabase Storage | Supabase projects, simple setup |
| Vercel Blob | Next.js projects on Vercel |
| Uploadthing | Easy setup for Next.js |

## S3 with Presigned URLs (Recommended Pattern)

```typescript
// Direct upload: Client → S3 (bypass your server)
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
})

// 1. Generate presigned upload URL
async function getUploadUrl(key: string, contentType: string) {
  const command = new PutObjectCommand({
    Bucket: process.env.S3_BUCKET!,
    Key: key,
    ContentType: contentType,
    // Server-side encryption
    ServerSideEncryption: 'AES256',
    // Metadata
    Metadata: { uploadedBy: userId },
  })
  
  return getSignedUrl(s3, command, { expiresIn: 300 }) // 5 min to upload
}

// 2. Client uploads directly to S3
// fetch(presignedUrl, { method: 'PUT', body: file, headers: { 'Content-Type': file.type } })

// 3. Confirm upload and save to DB
async function confirmUpload(key: string, userId: string) {
  return db.file.create({
    data: {
      key,
      userId,
      url: `https://${process.env.S3_BUCKET}.s3.amazonaws.com/${key}`,
      status: 'uploaded',
    }
  })
}

// 4. Presigned download URL (for private files)
async function getDownloadUrl(key: string) {
  const command = new GetObjectCommand({
    Bucket: process.env.S3_BUCKET!,
    Key: key,
  })
  return getSignedUrl(s3, command, { expiresIn: 3600 }) // 1 hour
}
```

## File Upload in Next.js (UploadThing)

```typescript
// app/api/uploadthing/core.ts
import { createUploadthing, type FileRouter } from 'uploadthing/next'
import { auth } from '@/lib/auth'

const f = createUploadthing()

export const uploadRouter = {
  imageUploader: f({ image: { maxFileSize: '4MB', maxFileCount: 4 } })
    .middleware(async ({ req }) => {
      const session = await auth()
      if (!session) throw new Error('Unauthorized')
      return { userId: session.user.id }
    })
    .onUploadComplete(async ({ metadata, file }) => {
      await db.file.create({
        data: { userId: metadata.userId, url: file.url, key: file.key }
      })
      return { url: file.url }
    }),

  documentUploader: f({ pdf: { maxFileSize: '10MB' } })
    .middleware(async ({ req }) => {
      const session = await auth()
      if (!session) throw new Error('Unauthorized')
      return { userId: session.user.id }
    })
    .onUploadComplete(async ({ metadata, file }) => {
      // Trigger processing job
      await documentQueue.add('process', { fileUrl: file.url, userId: metadata.userId })
    }),
} satisfies FileRouter
```

```typescript
// React component
import { useUploadThing } from '@/lib/uploadthing'

function ImageUpload({ onComplete }: { onComplete: (url: string) => void }) {
  const { startUpload, isUploading, permittedFileInfo } = useUploadThing('imageUploader')

  const onDrop = useCallback(async (files: File[]) => {
    const result = await startUpload(files)
    if (result?.[0]) onComplete(result[0].url)
  }, [startUpload, onComplete])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  return (
    <div {...getRootProps()} className={cn('border-2 border-dashed rounded-lg p-8', isDragActive && 'border-primary')}>
      <input {...getInputProps()} />
      {isUploading ? <Progress /> : <p>Drop files or click to upload</p>}
    </div>
  )
}
```

## Image Processing (Sharp)

```typescript
import sharp from 'sharp'

// Resize and optimize on upload
async function processImage(buffer: Buffer, filename: string) {
  const [thumbnail, medium, large] = await Promise.all([
    sharp(buffer).resize(150, 150, { fit: 'cover' }).webp({ quality: 80 }).toBuffer(),
    sharp(buffer).resize(800, null, { withoutEnlargement: true }).webp({ quality: 85 }).toBuffer(),
    sharp(buffer).resize(1920, null, { withoutEnlargement: true }).webp({ quality: 90 }).toBuffer(),
  ])

  await Promise.all([
    s3.upload(`${filename}-thumb.webp`, thumbnail),
    s3.upload(`${filename}-medium.webp`, medium),
    s3.upload(`${filename}-large.webp`, large),
  ])
}
```

## Cloudinary (Image Transformations)

```typescript
import { v2 as cloudinary } from 'cloudinary'

// Upload with auto-optimization
const result = await cloudinary.uploader.upload(filePath, {
  folder: 'products',
  transformation: [
    { width: 2000, height: 2000, crop: 'limit' },
    { quality: 'auto', fetch_format: 'auto' } // auto WebP/AVIF
  ],
})

// Dynamic URL transformations (no re-upload needed)
// https://res.cloudinary.com/demo/image/upload/w_300,h_300,c_fill,q_auto/products/shirt.jpg
function getImageUrl(publicId: string, { width, height }: Dimensions) {
  return cloudinary.url(publicId, {
    width, height,
    crop: 'fill',
    quality: 'auto',
    fetch_format: 'auto',
    secure: true,
  })
}
```

## Security Rules

- Validate file types server-side (not just MIME type — check magic bytes)
- Scan uploads for malware (ClamAV, VirusTotal API)
- Generate unique keys (never use user-provided filenames)
- Store private files with signed URLs, not public URLs
- Set file size limits
- Never serve user uploads from the same domain (XSS risk)
