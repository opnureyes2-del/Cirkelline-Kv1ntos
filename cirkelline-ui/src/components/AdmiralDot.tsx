'use client'

import { useState, useEffect } from 'react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

export default function AdmiralDot() {
  const [ok, setOk] = useState<boolean | null>(null)

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch('/api/admiral/status', { signal: AbortSignal.timeout(3000) })
        const d = await r.json()
        setOk(d.admiral_reachable === true)
      } catch {
        setOk(false)
      }
    }
    check()
    const t = setInterval(check, 60000)
    return () => clearInterval(t)
  }, [])

  if (ok === null) return null

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center justify-center w-6 h-6 cursor-default">
            <div
              className={`w-2 h-2 rounded-full transition-colors ${
                ok ? 'bg-green-400 shadow-[0_0_4px_#4ade80]' : 'bg-red-400/60'
              }`}
            />
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="text-xs">
          {ok ? 'Admiral: online' : 'Admiral: offline'}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
