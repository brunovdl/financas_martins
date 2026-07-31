import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabaseClient'
import { hashPassword, createToken, SESSION_DURATION_SECONDS } from '@/lib/auth'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { name, email, password } = body

    // 1. Validations
    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return NextResponse.json({ error: 'O nome de usuário é obrigatório.' }, { status: 400 })
    }

    if (!email || typeof email !== 'string' || !email.includes('@')) {
      return NextResponse.json({ error: 'E-mail inválido.' }, { status: 400 })
    }

    if (!password || typeof password !== 'string' || password.length < 8) {
      return NextResponse.json({ error: 'A senha deve conter no mínimo 8 caracteres.' }, { status: 400 })
    }

    const cleanEmail = email.trim().toLowerCase()
    const cleanName = name.trim()

    // 2. Check if user exists
    /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
    const { data: existingUser } = await (supabase as any)
      .from('mai_finance_users')
      .select('id')
      .eq('email', cleanEmail)
      .maybeSingle()

    if (existingUser) {
      return NextResponse.json({ error: 'Este e-mail já está cadastrado.' }, { status: 409 })
    }

    // 3. Hash password and insert
    const passwordHash = hashPassword(password)
    /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
    const { data: newUser, error: insertError } = await (supabase as any)
      .from('mai_finance_users')
      .insert({
        name: cleanName,
        email: cleanEmail,
        password_hash: passwordHash,
      })
      .select('id, name, email')
      .single()

    if (insertError) {
      console.error('Error creating user:', insertError)
      return NextResponse.json({ error: 'Erro ao criar conta no banco de dados.' }, { status: 500 })
    }

    // 4. Generate 24h JWT token
    const { token, exp } = createToken({
      userId: newUser.id,
      name: newUser.name,
      email: newUser.email,
    })

    const response = NextResponse.json({
      user: newUser,
      expiresAt: exp,
      message: 'Conta criada com sucesso!',
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
    console.error('Register API error:', error)
    return NextResponse.json({ error: 'Erro interno no servidor.' }, { status: 500 })
  }
}
