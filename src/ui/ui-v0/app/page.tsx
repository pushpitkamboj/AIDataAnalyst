import Link from "next/link"

export default function HomePage() {
  return (
    <main className="min-h-dvh bg-background text-foreground">
      <section className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="text-balance text-3xl font-semibold">Chatbot Data Uploader</h1>
        <p className="mt-3 text-muted-foreground">
          Choose a data source (CSV file or a database connection string), then start chatting.
        </p>
        <div className="mt-8">
          <Link
            href="/upload"
            className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-primary-foreground hover:opacity-90"
          >
            Go to Upload
          </Link>
        </div>
      </section>
    </main>
  )
}
