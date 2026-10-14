import { useEffect, useRef } from 'react'

/**
 * Lightweight scroll-reveal hook using IntersectionObserver.
 * Adds a `.revealed` class when the element enters the viewport.
 * Respects prefers-reduced-motion.
 *
 * @param {Object} options
 * @param {number} options.threshold - 0-1 visibility ratio (default 0.15)
 * @param {string} options.rootMargin - observer root margin (default '0px 0px -60px 0px')
 */
export default function useScrollReveal({ threshold = 0.15, rootMargin = '0px 0px -60px 0px' } = {}) {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    // Respect reduced motion preference
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReduced) {
      el.classList.add('revealed')
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add('revealed')
          observer.unobserve(el)
        }
      },
      { threshold, rootMargin }
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [threshold, rootMargin])

  return ref
}
