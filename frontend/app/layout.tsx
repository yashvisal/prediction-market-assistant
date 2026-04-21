import type { Metadata } from "next"
import { Instrument_Serif, Geist_Mono, Inter } from "next/font/google"

import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { cn } from "@/lib/utils"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
  variable: "--font-serif",
})

const fontMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export const metadata: Metadata = {
  title: "World Signal Feed",
  description:
    "A topic-centric intelligence product that turns fragmented prediction market signals into clear views of what is changing.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn(
        "antialiased",
        inter.variable,
        fontMono.variable,
        instrumentSerif.variable,
        "font-sans"
      )}
    >
      <body>
        <a
          href="#main-content"
          className="sr-only fixed left-4 top-4 z-50 rounded-md bg-background px-3 py-2 text-sm font-medium text-foreground shadow-sm focus:not-sr-only focus:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          Skip to main content
        </a>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  )
}
