import crypto from 'crypto'

const JWT_SECRET = process.env.JWT_SECRET || 'mai_finance_super_secret_session_key_2026_24h'
export const SESSION_DURATION_SECONDS = 86400 // 24 hours in seconds

// ---------------------------------------------------------------------------
// Password Hashing (PBKDF2 with Salt)
// ---------------------------------------------------------------------------
export function hashPassword(password: string): string {
  const salt = crypto.randomBytes(16).toString('hex')
  const hash = crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha512').toString('hex')
  return `${salt}:${hash}`
}

export function verifyPassword(password: string, storedHash: string): boolean {
  const [salt, originalHash] = storedHash.split(':')
  if (!salt || !originalHash) return false
  const hash = crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha512').toString('hex')
  return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), Buffer.from(originalHash, 'hex'))
}

// ---------------------------------------------------------------------------
// Lightweight Signed JWT (HS256)
// ---------------------------------------------------------------------------
function base64UrlEncode(str: string): string {
  return Buffer.from(str)
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
}

function base64UrlDecode(str: string): string {
  let base64 = str.replace(/-/g, '+').replace(/_/g, '/')
  while (base64.length % 4) {
    base64 += '='
  }
  return Buffer.from(base64, 'base64').toString('utf-8')
}

export interface JWTPayload {
  userId: string
  name: string
  email: string
  iat: number
  exp: number
}

export function createToken(payload: Omit<JWTPayload, 'iat' | 'exp'>): { token: string; exp: number } {
  const iat = Math.floor(Date.now() / 1000)
  const exp = iat + SESSION_DURATION_SECONDS

  const header = { alg: 'HS256', typ: 'JWT' }
  const fullPayload: JWTPayload = { ...payload, iat, exp }

  const encodedHeader = base64UrlEncode(JSON.stringify(header))
  const encodedPayload = base64UrlEncode(JSON.stringify(fullPayload))

  const signature = crypto
    .createHmac('sha256', JWT_SECRET)
    .update(`${encodedHeader}.${encodedPayload}`)
    .digest('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')

  const token = `${encodedHeader}.${encodedPayload}.${signature}`
  return { token, exp: exp * 1000 }
}

export function verifyToken(token: string): JWTPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null

    const [encodedHeader, encodedPayload, signature] = parts
    const expectedSignature = crypto
      .createHmac('sha256', JWT_SECRET)
      .update(`${encodedHeader}.${encodedPayload}`)
      .digest('base64')
      .replace(/=/g, '')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature))) {
      return null
    }

    const payload: JWTPayload = JSON.parse(base64UrlDecode(encodedPayload))
    const now = Math.floor(Date.now() / 1000)

    if (payload.exp && payload.exp < now) {
      return null // Expired session (24h exceeded)
    }

    return payload
  } catch (err) {
    return null
  }
}
