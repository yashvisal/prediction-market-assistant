"use client"

import * as React from "react"

export function ScrollTo({
  target,
  className,
  children,
}: {
  target: string
  className?: string
  children: React.ReactNode
}) {
  function handleClick() {
    const el = document.getElementById(target)
    if (el) {
      const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches

      el.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth" })
    }
  }

  return (
    <button type="button" onClick={handleClick} className={className}>
      {children}
    </button>
  )
}
