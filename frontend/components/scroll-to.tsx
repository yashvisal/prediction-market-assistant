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
      el.scrollIntoView({ behavior: "smooth" })
    }
  }

  return (
    <button onClick={handleClick} className={className}>
      {children}
    </button>
  )
}
