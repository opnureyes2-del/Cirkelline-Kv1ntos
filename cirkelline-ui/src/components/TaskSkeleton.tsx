'use client'

export default function TaskSkeleton() {
  return (
    <div className="p-3 rounded-lg bg-light-bg dark:bg-dark-bg border border-transparent animate-pulse">
      <div className="flex items-start gap-2.5">
        {/* Checkbox skeleton */}
        <div className="mt-0.5 w-[18px] h-[18px] bg-light-text-secondary/20 dark:bg-dark-text-secondary/20 rounded" />

        {/* Content skeleton */}
        <div className="flex-1 space-y-2">
          {/* Title skeleton */}
          <div className="h-4 bg-light-text-secondary/20 dark:bg-dark-text-secondary/20 rounded w-3/4" />

          {/* Date skeleton (random width) */}
          <div className="h-3 bg-light-text-secondary/10 dark:bg-dark-text-secondary/10 rounded w-1/3" />
        </div>
      </div>
    </div>
  )
}
