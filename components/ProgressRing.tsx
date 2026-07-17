'use client'

import React from 'react'
import type { ThemeTokens } from '@/lib/theme'

interface ProgressRingProps {
  pct: number
  size?: number
  T: ThemeTokens
}

export function ProgressRing({ pct, size = 64, T }: ProgressRingProps) {
  const stroke = 6
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = c - (pct / 100) * c

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} stroke={T.ringTrack} strokeWidth={stroke} fill="none" />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke="url(#ringGradient)"
        strokeWidth={stroke}
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1)' }}
      />
      <defs>
        <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={T.ring1} />
          <stop offset="100%" stopColor={T.ring2} />
        </linearGradient>
      </defs>
    </svg>
  )
}
