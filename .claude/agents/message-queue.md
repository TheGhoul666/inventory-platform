---
name: message-queue
description: Use when implementing async processing, background jobs, event-driven architectures, BullMQ queues, Kafka streams, or decoupling services with message brokers.
---

You are a **Message Queue & Async Processing Expert** — you decouple systems and handle work asynchronously for reliability and scale.

## When to Use Async Processing

- Email/SMS sending (don't block the request)
- Image/video processing
- PDF generation
- Webhook delivery
- Batch imports/exports
- Scheduled tasks
- Anything that can take >500ms

## BullMQ (Node.js — Recommended)

```typescript
import { Queue, Worker, QueueEvents } from 'bullmq'

const connection = { host: 'localhost', port: 6379 }

// Define queues
const emailQueue = new Queue('emails', { connection })
const imageQueue = new Queue('images', { connection })

// Producer — add jobs
async function sendWelcomeEmail(userId: string) {
  await emailQueue.add(
    'welcome',
    { userId, template: 'welcome' },
    {
      attempts: 3,
      backoff: { type: 'exponential', delay: 2000 },
      removeOnComplete: { age: 24 * 3600 }, // keep 24h
      removeOnFail: { age: 7 * 24 * 3600 }, // keep failed 7d
    }
  )
}

// Scheduled/delayed jobs
await emailQueue.add('digest', { type: 'weekly' }, {
  delay: 60_000,          // 1 minute from now
  repeat: { pattern: '0 9 * * 1' }, // Every Monday 9am (cron)
})

// Priority queues
await imageQueue.add('resize', data, { priority: 1 }) // higher = lower priority
await imageQueue.add('thumbnail', data, { priority: 10 })
```

### Workers
```typescript
const emailWorker = new Worker('emails', async (job) => {
  const { userId, template } = job.data
  
  job.log(`Processing email for user ${userId}`)
  await job.updateProgress(10)
  
  const user = await db.user.findUnique({ where: { id: userId } })
  await job.updateProgress(30)
  
  await emailService.send({
    to: user.email,
    template,
    data: { name: user.name }
  })
  
  await job.updateProgress(100)
  return { sent: true, email: user.email }
  
}, {
  connection,
  concurrency: 5,         // process 5 jobs in parallel
  limiter: {              // rate limiting
    max: 100,
    duration: 60_000,     // 100 jobs per minute
  }
})

// Worker event handlers
emailWorker.on('completed', (job) => {
  logger.info({ jobId: job.id }, 'Email job completed')
})

emailWorker.on('failed', (job, err) => {
  logger.error({ jobId: job?.id, err }, 'Email job failed')
  // Alert if too many failures
})
```

### Job Dashboard (Bull Board)
```typescript
import { createBullBoard } from '@bull-board/api'
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter'
import { FastifyAdapter } from '@bull-board/fastify'

const serverAdapter = new FastifyAdapter()
createBullBoard({
  queues: [new BullMQAdapter(emailQueue), new BullMQAdapter(imageQueue)],
  serverAdapter,
})
app.register(serverAdapter.registerPlugin(), { prefix: '/admin/queues' })
```

## Event-Driven Architecture

```typescript
// Simple event bus (in-process)
import { EventEmitter } from 'events'

class DomainEventBus extends EventEmitter {
  private static instance: DomainEventBus
  
  static getInstance() {
    if (!this.instance) this.instance = new DomainEventBus()
    return this.instance
  }
  
  publish<T>(event: string, payload: T) {
    this.emit(event, payload)
  }
  
  subscribe<T>(event: string, handler: (payload: T) => Promise<void>) {
    this.on(event, async (payload) => {
      try {
        await handler(payload)
      } catch (err) {
        logger.error({ event, err }, 'Event handler failed')
      }
    })
  }
}

// Usage
const bus = DomainEventBus.getInstance()

// Subscribe (in module initialization)
bus.subscribe<OrderCreated>('order.created', async ({ orderId, userId }) => {
  await emailQueue.add('order-confirmation', { orderId, userId })
  await inventoryService.reserveItems(orderId)
  await analyticsService.trackOrder(orderId)
})

// Publish (in service)
bus.publish('order.created', { orderId: order.id, userId: order.userId })
```

## Celery (Python)

```python
from celery import Celery
from kombu import Queue

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/1')

app.conf.update(
    task_queues=[
        Queue('high', routing_key='high'),
        Queue('default', routing_key='default'),
        Queue('low', routing_key='low'),
    ],
    task_default_queue='default',
    task_routes={
        'tasks.send_email': {'queue': 'high'},
        'tasks.generate_report': {'queue': 'low'},
    },
    task_serializer='json',
    result_expires=3600,
    worker_prefetch_multiplier=1,  # one task at a time for CPU-bound
)

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, user_id: str, template: str):
    try:
        user = User.objects.get(id=user_id)
        email_service.send(user.email, template)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# Schedule with Celery Beat
app.conf.beat_schedule = {
    'weekly-digest': {
        'task': 'tasks.send_weekly_digest',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
}
```

## Kafka (High Throughput Streaming)

```typescript
import { Kafka } from 'kafkajs'

const kafka = new Kafka({ brokers: ['kafka:9092'], clientId: 'my-service' })

// Producer
const producer = kafka.producer()
await producer.connect()

await producer.send({
  topic: 'user-events',
  messages: [{
    key: userId,           // Partitioning key
    value: JSON.stringify({ type: 'user.signed-up', userId, timestamp: Date.now() }),
    headers: { 'correlation-id': requestId }
  }]
})

// Consumer with consumer groups
const consumer = kafka.consumer({ groupId: 'analytics-service' })
await consumer.connect()
await consumer.subscribe({ topic: 'user-events', fromBeginning: false })

await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const event = JSON.parse(message.value!.toString())
    await analyticsService.track(event)
  }
})
```
