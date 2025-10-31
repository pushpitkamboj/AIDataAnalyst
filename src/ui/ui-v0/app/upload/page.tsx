"use client"

import type React from "react"

import { useState, useRef } from "react"
import axios from "axios"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { setDataSource } from "@/lib/data-source"

const API_BASE = "http://localhost:8000"

type SourceType = "csv" | "db"

export default function UploadPage() {
  const [sourceType, setSourceType] = useState<SourceType>("csv")
  const [dbUrl, setDbUrl] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileRef = useRef<HTMLInputElement | null>(null)
  const router = useRouter()
  const { toast } = useToast()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const form = new FormData()

      if (sourceType === "csv") {
        const file = fileRef.current?.files?.[0]
        if (!file) {
          toast({ title: "Missing file", description: "Please select a CSV file first." })
          setIsSubmitting(false)
          return
        }
        form.append("file", file)
        console.log("[v0] Uploading CSV file:", file.name)
      } else {
        if (!dbUrl.trim()) {
          toast({ title: "Missing DB URL", description: "Please enter a database connection string." })
          setIsSubmitting(false)
          return
        }
        form.append("db_url", dbUrl.trim())
        console.log("[v0] Uploading DB URL")
      }

      const res = await axios.post(`${API_BASE}/upload`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })

      // Response type: json, includes "message" which is csv public url or db url
      const message: string | undefined = res?.data?.message
      if (!message) {
        throw new Error("Server response missing 'message'.")
      }

      if (sourceType === "csv") {
        setDataSource({ type: "csv", url: message })
      } else {
        setDataSource({ type: "db", url: message })
      }

      toast({ title: "Upload successful", description: "Taking you to the chat interface..." })
      router.push("/chat")
    } catch (err: any) {
      console.error("[v0] Upload error:", err)
      toast({
        title: "Upload failed",
        description: err?.response?.data?.error || err?.message || "Please try again.",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-dvh bg-background text-foreground">
      <section className="mx-auto max-w-xl px-6 py-12">
        <h1 className="text-2xl font-semibold text-balance">Upload Data Source</h1>
        <p className="mt-2 text-muted-foreground">Choose only one: a CSV file or a database connection string.</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          {/* Selector */}
          <fieldset className="rounded-lg border border-border p-4">
            <legend className="px-2 text-sm text-muted-foreground">Select data source</legend>
            <div className="flex items-center gap-6">
              <label className="inline-flex items-center gap-2">
                <input
                  type="radio"
                  name="source"
                  value="csv"
                  checked={sourceType === "csv"}
                  onChange={() => setSourceType("csv")}
                  className="h-4 w-4"
                  aria-label="CSV file"
                />
                <span>CSV file</span>
              </label>

              <label className="inline-flex items-center gap-2">
                <input
                  type="radio"
                  name="source"
                  value="db"
                  checked={sourceType === "db"}
                  onChange={() => setSourceType("db")}
                  className="h-4 w-4"
                  aria-label="DB connection string"
                />
                <span>DB connection string</span>
              </label>
            </div>
          </fieldset>

          {/* CSV input */}
          <div className="grid gap-2">
            <label htmlFor="csv" className="text-sm font-medium">
              CSV file
            </label>
            <input
              id="csv"
              ref={fileRef}
              type="file"
              accept=".csv,text/csv"
              disabled={sourceType !== "csv" || isSubmitting}
              className="block w-full rounded-md border border-border bg-card p-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-2 file:text-sm file:text-primary-foreground hover:file:opacity-90"
              aria-disabled={sourceType !== "csv" || isSubmitting}
            />
            <p className="text-xs text-muted-foreground">
              Only used if "CSV file" is selected. Sent as form-data with key {'"file"'}.
            </p>
          </div>

          {/* DB URL input */}
          <div className="grid gap-2">
            <label htmlFor="dburl" className="text-sm font-medium">
              Database connection string
            </label>
            <input
              id="dburl"
              type="text"
              placeholder="postgresql://user:pass@host:5432/dbname"
              value={dbUrl}
              onChange={(e) => setDbUrl(e.target.value)}
              disabled={sourceType !== "db" || isSubmitting}
              className="w-full rounded-md border border-border bg-card px-3 py-2 text-sm"
              aria-disabled={sourceType !== "db" || isSubmitting}
            />
            <p className="text-xs text-muted-foreground">
              Only used if "DB connection string" is selected. Sent as form-data with key {'"db_url"'}.
            </p>
          </div>

          <div className="flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => {
                if (fileRef.current) fileRef.current.value = ""
                setDbUrl("")
                setSourceType("csv")
              }}
              className="inline-flex items-center rounded-md border border-border bg-transparent px-4 py-2 text-sm hover:bg-accent"
              disabled={isSubmitting}
            >
              Reset
            </button>
            <button
              type="submit"
              className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:opacity-90 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Uploading..." : "Continue"}
            </button>
          </div>
        </form>
      </section>
    </main>
  )
}
