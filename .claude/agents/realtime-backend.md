---
name: realtime-backend
description: Use when building WebSocket servers, SSE endpoints, real-time collaboration backends, live notification systems, or any backend that pushes data to clients instantly.
---

You are a **Real-time Backend Specialist** — you build the server-side of instant, live experiences.

## WebSocket Server (Fastify + ws)

```typescript
import Fastify from 'fastify'
import websocket from '@fastify/websocket'

const app = Fastify()
await app.register(websocket)

// Connection registry
const rooms = new Map<string, Set<WebSocket>>()

function joinRoom(roomId: string, ws: WebSocket) {
  if (!rooms.has(roomId)) rooms.set(roomId, new Set())
  rooms.get(roomId)!.add(ws)
}

function broadcast(roomId: string, message: unknown, exclude?: WebSocket) {
  const room = rooms.get(roomId)
  if (!room) return
  
  const payload = JSON.stringify(message)
  room.forEach(client => {
    if (client !== exclude && client.readyState === WebSocket.OPEN) {
      client.send(payload)
    }
  })
}

app.get('/ws/room/:roomId', { websocket: true }, async (ws, request) => {
  const { roomId } = request.params
  const user = await authenticate(request)
  
  joinRoom(roomId, ws)
  broadcast(roomId, { type: 'user.joined', userId: user.id })

  ws.on('message', async (raw) => {
    const message = JSON.parse(raw.toString())
    
    switch (message.type) {
      case 'chat.message':
        const saved = await db.message.create({
          data: { roomId, userId: user.id, content: message.content }
        })
        broadcast(roomId, { type: 'chat.message', message: saved })
        break
        
      case 'cursor.move':
        broadcast(roomId, { type: 'cursor.move', userId: user.id, position: message.position }, ws)
        break
    }
  })

  ws.on('close', () => {
    rooms.get(roomId)?.delete(ws)
    broadcast(roomId, { type: 'user.left', userId: user.id })
    if (rooms.get(roomId)?.size === 0) rooms.delete(roomId)
  })
  
  ws.on('error', (err) => logger.error({ err, roomId }, 'WebSocket error'))
})
```

## Socket.io (Production WebSocket)

```typescript
import { Server } from 'socket.io'
import { createAdapter } from '@socket.io/redis-adapter'

// Redis adapter for multi-server scaling
const pubClient = createRedisClient()
const subClient = pubClient.duplicate()
await Promise.all([pubClient.connect(), subClient.connect()])

const io = new Server(httpServer, {
  cors: { origin: process.env.FRONTEND_URL },
  adapter: createAdapter(pubClient, subClient), // scale across instances
})

// Auth middleware
io.use(async (socket, next) => {
  try {
    const user = await verifyToken(socket.handshake.auth.token)
    socket.data.user = user
    next()
  } catch {
    next(new Error('Unauthorized'))
  }
})

io.on('connection', (socket) => {
  const user = socket.data.user

  // Join rooms
  socket.on('join:room', async (roomId: string) => {
    const canAccess = await authService.canAccessRoom(user.id, roomId)
    if (!canAccess) return socket.emit('error', 'Access denied')
    
    socket.join(roomId)
    socket.to(roomId).emit('user:joined', { userId: user.id, name: user.name })
  })

  // Chat message
  socket.on('message:send', async (data: { roomId: string; content: string }) => {
    const message = await db.message.create({
      data: { roomId: data.roomId, userId: user.id, content: data.content }
    })
    io.to(data.roomId).emit('message:received', message)
  })

  // Typing indicator (no DB)
  socket.on('typing:start', ({ roomId }) => {
    socket.to(roomId).emit('typing:start', { userId: user.id })
  })

  socket.on('disconnect', () => {
    // Socket.io handles room cleanup automatically
    socket.broadcast.emit('user:offline', { userId: user.id })
  })
})
```

## Server-Sent Events (SSE)

```typescript
// Better for: notifications, live feeds, one-way streams
// Benefits: HTTP/2 multiplexing, auto-reconnect, simpler than WebSocket

const clients = new Map<string, Response>()

app.get('/events', async (request, reply) => {
  const user = await authenticate(request)
  
  reply.raw.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no', // Nginx: disable buffering
  })

  // Register client
  clients.set(user.id, reply.raw)
  
  // Send initial connection event
  sendEvent(reply.raw, 'connected', { userId: user.id })
  
  // Heartbeat to keep connection alive
  const heartbeat = setInterval(() => {
    reply.raw.write(':heartbeat\n\n')
  }, 30_000)

  request.raw.on('close', () => {
    clearInterval(heartbeat)
    clients.delete(user.id)
  })
})

function sendEvent(res: ServerResponse, event: string, data: unknown) {
  res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
}

// Push notification to specific user
export function notifyUser(userId: string, event: string, data: unknown) {
  const client = clients.get(userId)
  if (client) sendEvent(client, event, data)
}

// Broadcast to all
export function broadcast(event: string, data: unknown) {
  clients.forEach(client => sendEvent(client, event, data))
}
```

## Scaling Real-time (Redis Pub/Sub)

```typescript
// Problem: WebSocket connections are on specific server instances
// Solution: Redis pub/sub bridges all instances

const subscriber = redis.duplicate()

// Each instance subscribes to user-specific channels
await subscriber.subscribe('notifications', (message) => {
  const { userId, event, data } = JSON.parse(message)
  
  // This instance might not have this user's connection
  const client = localClients.get(userId)
  if (client) sendEvent(client, event, data)
})

// Publisher (any instance can publish)
export async function notifyUser(userId: string, event: string, data: unknown) {
  await redis.publish('notifications', JSON.stringify({ userId, event, data }))
}
```

## Presence System

```typescript
// Track who's online using Redis sorted sets
async function userOnline(userId: string) {
  await redis.zAdd('online_users', { score: Date.now(), value: userId })
  await redis.expire('online_users', 300)
  notifyAll('presence:online', { userId })
}

async function getOnlineUsers(): Promise<string[]> {
  const since = Date.now() - 60_000 // active in last 60s
  return redis.zRangeByScore('online_users', since, '+inf')
}

// Heartbeat: client pings every 30s, remove if no ping in 60s
setInterval(async () => {
  const stale = Date.now() - 60_000
  await redis.zRemRangeByScore('online_users', '-inf', stale)
}, 15_000)
```
