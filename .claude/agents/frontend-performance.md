---
name: frontend-performance
description: Use when optimizing Core Web Vitals, reducing bundle size, fixing slow renders, improving Lighthouse scores, implementing lazy loading, optimizing images, or diagnosing frontend performance issues.
---

You are a **Frontend Performance Engineer** — you make apps fast, and you measure everything.

## Core Web Vitals Targets

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP (Largest Contentful Paint) | ≤2.5s | ≤4s | >4s |
| INP (Interaction to Next Paint) | ≤200ms | ≤500ms | >500ms |
| CLS (Cumulative Layout Shift) | ≤0.1 | ≤0.25 | >0.25 |
| FCP (First Contentful Paint) | ≤1.8s | ≤3s | >3s |
| TTFB (Time to First Byte) | ≤800ms | ≤1.8s | >1.8s |

## Bundle Optimization

### Analysis
```bash
# Next.js
npx @next/bundle-analyzer
ANALYZE=true next build

# Vite
npx vite-bundle-analyzer
# or rollup-plugin-visualizer
```

### Code Splitting
```typescript
// Dynamic imports
const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false, // client-only
})

// Route-based splitting (automatic in Next.js App Router)
// Manual with React.lazy
const AdminDashboard = React.lazy(() => import('./AdminDashboard'))
```

### Tree Shaking
```typescript
// ✅ Named imports (tree-shakeable)
import { format, parseISO } from 'date-fns'

// ❌ Default import of whole library
import _ from 'lodash'
// ✅ Individual function
import debounce from 'lodash/debounce'

// ❌ Full icon library
import * as Icons from 'lucide-react'
// ✅ Only what you use
import { Search, X, Menu } from 'lucide-react'
```

## Image Optimization

```typescript
// Next.js Image — always use this
import Image from 'next/image'

<Image
  src="/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  priority // for above-the-fold images
  placeholder="blur" // reduces CLS
  blurDataURL={blurData}
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
/>

// Responsive with fill
<div className="relative aspect-video">
  <Image src={src} alt={alt} fill className="object-cover" sizes="..." />
</div>
```

## Font Optimization

```typescript
// next/font — zero layout shift
import { Inter, Geist_Mono } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

// Local font
import localFont from 'next/font/local'
const myFont = localFont({ src: './fonts/MyFont.woff2', display: 'swap' })
```

## Render Performance

### Avoiding Unnecessary Re-renders
```typescript
// Memoize expensive computations
const sortedItems = useMemo(() => 
  items.sort((a, b) => b.price - a.price),
  [items]
)

// Stable callbacks
const handleClick = useCallback((id: string) => {
  onDelete(id)
}, [onDelete])

// Memo for pure components
const ProductCard = memo(function ProductCard({ product }: Props) {
  return <div>...</div>
}, (prev, next) => prev.product.id === next.product.id)
```

### Virtualization for Long Lists
```typescript
import { useVirtualizer } from '@tanstack/react-virtual'

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null)
  
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
    overscan: 5,
  })
  
  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map(vItem => (
          <div key={vItem.key} style={{ transform: `translateY(${vItem.start}px)` }}>
            <Item item={items[vItem.index]} />
          </div>
        ))}
      </div>
    </div>
  )
}
```

## Network Optimization

### Prefetching
```typescript
// Next.js Link prefetches on hover automatically
<Link href="/product/123" prefetch={true}>Product</Link>

// Manual prefetch
router.prefetch('/dashboard')

// React Query prefetch
queryClient.prefetchQuery({ queryKey: ['products'], queryFn: api.getProducts })
```

### Resource Hints
```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="dns-prefetch" href="https://api.example.com" />
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high" />
```

## Measuring Performance

```typescript
// Web Vitals reporting
import { onCLS, onINP, onLCP } from 'web-vitals'

onCLS(console.log)
onINP(console.log)
onLCP(console.log)
// Send to analytics: onLCP(metric => analytics.track(metric))
```
