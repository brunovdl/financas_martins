import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { verifyToken } from '@/lib/auth'

export async function GET() {
  try {
    const cookieStore = await cookies()
    const tokenCookie = cookieStore.get('auth_token')

    if (!tokenCookie || !tokenCookie.value) {
      return NextResponse.json({ authenticated: false }, { status: 401 })
    }

    const payload = verifyToken(tokenCookie.value)
    if (!payload) {
      // Expired or tampered token (24h limit reached)
      const response = NextResponse.json({ authenticated: false, error: 'Sessão expirada.' }, { status: 401 })
      response.cookies.set('auth_token', '', { maxAge: 0, path: '/' })
      return response
    }

    return NextResponse.json({
      authenticated: true,
      user: {
        id: payload.userId,
        name: payload.name,
        email: payload.email,
      },
      expiresAt: payload.exp * 1000,
    })
  } catch (error) {
    console.error('Check auth API error:', error)
    return NextResponse.json({ authenticated: false }, { status: 500 })
  }
}
