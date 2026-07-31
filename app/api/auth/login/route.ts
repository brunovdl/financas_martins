import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabaseClient'
import { verifyPassword, createToken, SESSION_DURATION_SECONDS } from '@/lib/auth'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { email, password } = body

    if (!email || typeof email !== 'string' || !email.includes('@')) {
      return NextResponse.json({ error: 'E-mail inválido.' }, { status: 400 })
    }

    if (!password || typeof password !== 'string' || password.length < 8) {
      return NextResponse.json({ error: 'A senha deve conter no mínimo 8 caracteres.' }, { status: 400 })
    }

    const cleanEmail = email.trim().toLowerCase()

    // 1. Fetch user by email
    /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
    const { data: user, error } = await (supabase as any)
      .from('mai_finance_users')
      .select('id, name, email, password_hash')
      .eq('email', cleanEmail)
      .maybeSingle()

    if (error || !user) {
      return NextResponse.json({ error: 'E-mail ou senha incorretos.' }, { status: 401 })
    }

    // 2. Verify password
    const isValidPassword = verifyPassword(password, user.password_hash)
    if (!isValidPassword) {
      return NextResponse.json({ error: 'E-mail ou senha incorretos.' }, { status: 401 })
    }

    // 3. Create 24h token
    const { token, exp } = createToken({
      userId: user.id,
      name: user.name,
      email: user.email,
    })

    const userPayload = {
      id: user.id,
      name: user.name,
      email: user.email,
    }

    const response = NextResponse.json({
      user: userPayload,
      expiresAt: exp,
      message: 'Login realizado com sucesso!',
    })

    // Set 24h HttpOnly cookie
    response.cookies.set('auth_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: SESSION_DURATION_SECONDS,
      path: '/',
    })

    return response
  } catch (error) {
    console.error('Login API error:', error)
    return NextResponse.json({ error: 'Erro interno no servidor.' }, { status: 500 })
  }
}
