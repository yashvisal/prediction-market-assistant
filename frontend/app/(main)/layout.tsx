import { SiteHeader } from "@/components/site-header"

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      <SiteHeader />
      <main id="main-content" className="mx-auto max-w-6xl px-4 py-6">
        {children}
      </main>
    </>
  )
}
