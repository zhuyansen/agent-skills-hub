import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
  type RefObject,
} from "react";

/** Height in px a block holds until it has rendered, on phones, sm (640px+),
 *  md (768px+) and lg (1024px+). Measure with `ops/perf/home_cls.py --heights`. */
export type Reserve = readonly [base: number, sm: number, md: number, lg: number];

interface Props {
  children: ReactNode;
  /** How far before the viewport to start rendering */
  rootMargin?: string;
  /** Space held until the content has rendered (see READY_SHARE) */
  reserve?: Reserve;
  className?: string;
}

// Blocks used to sit at 200px and spring open to their real 600–8,000px on screen
// when the visitor scrolled faster than they loaded: CLS 0.5–1.4 in
// ops/perf/home_cls.py, 0.13–0.17 for real users (CrUX, 11-02). Now a block
// renders about a screen and a half ahead, and holds its measured height until its
// content fills most of it, so one still waiting for data (several render null or
// a one-line "loading" meanwhile) no longer collapses and then springs open.
const DEFAULT_RESERVE: Reserve = [200, 200, 200, 200];
const READY_SHARE = 0.75;
/** A block whose content never comes (an empty or failed fetch) gives its space back
 *  after this long, and only while it is still below the screen. Collapsing one the
 *  visitor can see or has scrolled past is the very jump this prevents: an 8 s limit
 *  did that on slow phones, where New This Week took longer (CLS 0.9, 11-02). */
const READY_TIMEOUT_MS = 60_000;
const RESERVE_CLASS =
  "min-h-[var(--lz-base)] sm:min-h-[var(--lz-sm)] md:min-h-[var(--lz-md)] lg:min-h-[var(--lz-lg)]";

function reserveStyle([base, sm, md, lg]: Reserve): CSSProperties {
  return {
    "--lz-base": `${base}px`,
    "--lz-sm": `${sm}px`,
    "--lz-md": `${md}px`,
    "--lz-lg": `${lg}px`,
  } as CSSProperties;
}

function useNearViewport(
  ref: RefObject<HTMLDivElement | null>,
  rootMargin: string,
): boolean {
  const [near, setNear] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setNear(true);
          observer.disconnect();
        }
      },
      { rootMargin },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref, rootMargin]);

  return near;
}

/** True once the rendered content fills READY_SHARE of the held space, or once
 *  READY_TIMEOUT_MS has passed with the block still below the screen. */
function useContentReady(
  outer: RefObject<HTMLDivElement | null>,
  inner: RefObject<HTMLDivElement | null>,
  started: boolean,
): boolean {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const box = outer.current;
    const content = inner.current;
    if (!started || ready || !box || !content) return;
    const held = parseFloat(getComputedStyle(box).minHeight) || 0;
    const check = () => {
      if (content.offsetHeight >= held * READY_SHARE) setReady(true);
    };
    const resize = new ResizeObserver(check);
    resize.observe(content);
    const timer = window.setTimeout(() => {
      if (box.getBoundingClientRect().top >= window.innerHeight) setReady(true);
    }, READY_TIMEOUT_MS);
    check();
    return () => {
      resize.disconnect();
      window.clearTimeout(timer);
    };
  }, [outer, inner, started, ready]);

  return ready;
}

export function LazySection({
  children,
  rootMargin = "1200px 0px",
  reserve = DEFAULT_RESERVE,
  className,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const inner = useRef<HTMLDivElement>(null);
  const near = useNearViewport(ref, rootMargin);
  const ready = useContentReady(ref, inner, near);

  return (
    <div
      ref={ref}
      className={ready ? className : [className, RESERVE_CLASS].filter(Boolean).join(" ")}
      style={ready ? undefined : reserveStyle(reserve)}
    >
      {near ? <div ref={inner}>{children}</div> : null}
    </div>
  );
}
