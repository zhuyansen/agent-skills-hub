export function SkeletonCards({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 animate-skeleton"
          style={{ animationDelay: `${i * 100}ms` }}
        >
          <div className="flex items-start gap-4">
            {/* Score circle */}
            <div className="w-14 h-14 rounded-full bg-gray-200 dark:bg-gray-700 shrink-0" />
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-gray-200 dark:bg-gray-700" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-20" />
              </div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-full" />
              <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-2/3" />
            </div>
          </div>
          <div className="mt-3 flex gap-1.5">
            <div className="h-5 bg-gray-100 dark:bg-gray-700/60 rounded-full w-16" />
            <div className="h-5 bg-gray-100 dark:bg-gray-700/60 rounded-full w-14" />
            <div className="h-5 bg-gray-100 dark:bg-gray-700/60 rounded-full w-12" />
          </div>
          <div className="mt-3 flex items-center gap-4">
            <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-10" />
            <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-10" />
            <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-16 ml-auto" />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Skeleton for TrendingSection (5-col grid) */
export function SkeletonTrending({ count = 5 }: { count?: number }) {
  return (
    <div className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-5 h-5 bg-gray-200 dark:bg-gray-700 rounded animate-skeleton" />
        <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-skeleton" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 animate-skeleton"
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16" />
            </div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
            <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-full mb-1" />
            <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-2/3" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Skeleton for list-style sections (TopRated, RecentlyUpdated) */
export function SkeletonList({ count = 5 }: { count?: number }) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl divide-y divide-gray-50 dark:divide-gray-700/50">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-4 py-3 animate-skeleton" style={{ animationDelay: `${i * 60}ms` }}>
          <div className="w-6 h-4 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3.5 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
            <div className="h-2.5 bg-gray-100 dark:bg-gray-700/60 rounded w-1/4" />
          </div>
          <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-12" />
        </div>
      ))}
    </div>
  );
}

/** Skeleton for HallOfFame podium */
export function SkeletonHallOfFame() {
  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="border-2 border-gray-200 dark:border-gray-700 rounded-xl p-5 animate-skeleton" style={{ animationDelay: `${i * 80}ms` }}>
            <div className="flex justify-between mb-3">
              <div className="w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700" />
              <div className="w-10 h-5 bg-gray-200 dark:bg-gray-700 rounded-full" />
            </div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-2" />
            <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function SkeletonDashboard() {
  return (
    <div className="space-y-6 animate-skeleton">
      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
            <div className="h-7 bg-gray-200 dark:bg-gray-700 rounded w-16 mb-2" />
            <div className="h-3 bg-gray-100 dark:bg-gray-700/60 rounded w-20" />
          </div>
        ))}
      </div>
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 h-48" />
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 h-48" />
      </div>
    </div>
  );
}
