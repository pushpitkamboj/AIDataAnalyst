"use client"

import type React from "react"

import { useEffect, useMemo, useRef, useState } from "react"
import axios from "axios"
import Link from "next/link"
import { useToast } from "@/hooks/use-toast"
import { getDataSource, clearDataSource, type DataSource } from "@/lib/data-source"
import { ChatBubble } from "@/components/chat-bubble"

const API_BASE = "http://localhost:8000"

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
}

export default function ChatPage() {
  const [dataSource, setDataSourceState] = useState<DataSource | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamBuffer, setStreamBuffer] = useState("") // accumulates assistant streaming text
  const { toast } = useToast()
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const ds = getDataSource()
    setDataSourceState(ds)
  }, [])

  // Auto-scroll to bottom when messages or stream updates
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages, streamBuffer])

  const headerLabel = useMemo(() => {
    if (!dataSource) return "No data source"
    return dataSource.type === "csv" ? "CSV source connected" : "Database source connected"
  }, [dataSource])

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if (!dataSource) {
      toast({ title: "No data source", description: "Go back and upload a CSV or DB URL first." })
      return
    }
    const q = input.trim()
    if (!q) return

    // push user message
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: q }
    setMessages((prev) => [...prev, userMsg])
    setInput("")

    // Start streaming placeholder
    setIsStreaming(true)
    setStreamBuffer("")

    try {
      const payload: Record<string, any> = { query: q }
      if (dataSource.type === "csv") payload.csv_url = dataSource.url
      if (dataSource.type === "db") payload.db_url = dataSource.url

      // Attempt streaming with fetch if server supports it
      const streamingSupported = true // we can optimistically try streaming; will fallback on failure
      if (streamingSupported) {
        const resp = await fetch(`${API_BASE}/query`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            // ask server for a streaming response if available
            Accept: "text/event-stream, application/x-ndjson, application/json",
          },
          body: JSON.stringify(payload),
        })

        const ctype = resp.headers.get("Content-Type") || ""
        const isSSE = ctype.includes("text/event-stream")
        const isNDJSON = ctype.includes("application/x-ndjson") || ctype.includes("ndjson")
        const isJSON = ctype.includes("application/json")

        console.log("[v0] /query content-type:", ctype)

        if ((isSSE || isNDJSON) && resp.body) {
          // Stream parse
          const reader = resp.body.getReader()
          const decoder = new TextDecoder()
          let assistantText = ""
          let buffered = ""

          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            const chunk = decoder.decode(value, { stream: true })
            buffered += chunk

            // SSE: lines start with "data: ..."
            if (isSSE) {
              const lines = buffered.split("\n")
              // retain last partial line
              buffered = lines.pop() || ""
              for (const line of lines) {
                const trimmed = line.trim()
                if (!trimmed.startsWith("data:")) continue
                const dataStr = trimmed.replace(/^data:\s*/, "")
                try {
                  const obj = JSON.parse(dataStr)
                  if (typeof obj?.final_answer === "string") {
                    assistantText += obj.final_answer
                    setStreamBuffer(assistantText)
                  }
                } catch {
                  // not JSON; treat as raw text
                  assistantText += dataStr
                  setStreamBuffer(assistantText)
                }
              }
            } else if (isNDJSON) {
              const lines = buffered.split("\n")
              buffered = lines.pop() || ""
              for (const line of lines) {
                const trimmed = line.trim()
                if (!trimmed) continue
                try {
                  const obj = JSON.parse(trimmed)
                  if (typeof obj?.final_answer === "string") {
                    assistantText += obj.final_answer
                    setStreamBuffer(assistantText)
                  }
                } catch {
                  assistantText += trimmed
                  setStreamBuffer(assistantText)
                }
              }
            }
          }

          // If after streaming nothing came, try to parse buffered JSON
          if (!isSSE && !isNDJSON && isJSON) {
            const data = await resp.json()
            const finalAnswer: string = data?.final_answer || ""
            setStreamBuffer(finalAnswer)
          }
        } else if (isJSON) {
          const data = await resp.json()
          const finalAnswer: string = data?.final_answer || ""
          setStreamBuffer(finalAnswer)
        } else if (!resp.ok) {
          // Fallback to axios if non-ok or unknown type
          throw new Error(`Streaming not supported (status ${resp.status})`)
        }
      } else {
        // Non-stream fallback (axios)
        const res = await axios.post(`${API_BASE}/query`, payload, {
          headers: { "Content-Type": "application/json" },
        })
        const finalAnswer: string = res?.data?.final_answer || ""
        setStreamBuffer(finalAnswer)
      }
    } catch (err: any) {
      console.error("[v0] Query error:", err)
      // Final fallback using axios JSON
      try {
        const res = await axios.post(
          `${API_BASE}/query`,
          { query: q, ...(dataSource.type === "csv" ? { csv_url: dataSource.url } : { db_url: dataSource.url }) },
          {
            headers: { "Content-Type": "application/json" },
          },
        )
        const finalAnswer: string = res?.data?.final_answer || ""
        setStreamBuffer(finalAnswer)
      } catch (err2: any) {
        console.error("[v0] Fallback axios error:", err2)
        toast({
          title: "Query failed",
          description: err2?.response?.data?.error || err2?.message || "Please try again.",
        })
      }
    } finally {
      // Move stream buffer to messages and reset
      if (streamBuffer) {
        const assistantMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: streamBuffer,
        }
        setMessages((prev) => [...prev, assistantMsg])
        setStreamBuffer("")
      } else {
        // There might have been streaming updates; ensure we push the last text
        if (streamBuffer.length > 0) {
          const assistantMsg: Message = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: streamBuffer,
          }
          setMessages((prev) => [...prev, assistantMsg])
          setStreamBuffer("")
        }
      }
      setIsStreaming(false)
    }
  }

  if (!dataSource) {
    return (
      <main className="min-h-dvh bg-background text-foreground">
        <section className="mx-auto max-w-xl px-6 py-12">
          <h1 className="text-2xl font-semibold text-balance">No data source configured</h1>
          <p className="mt-2 text-muted-foreground">
            Please upload a CSV or provide a database connection string to start chatting.
          </p>
          <div className="mt-6">
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

  return (
    <main className="grid min-h-dvh grid-rows-[auto,1fr,auto] bg-background text-foreground">
      <header className="border-b border-border px-6 py-4">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between">
          <div className="flex flex-col">
            <h1 className="text-lg font-medium">Chat</h1>
            <span className="text-xs text-muted-foreground">{headerLabel}</span>
          </div>
          <button
            className="inline-flex items-center rounded-md border border-border bg-transparent px-3 py-1.5 text-xs hover:bg-accent"
            onClick={() => {
              clearDataSource()
              setDataSourceState(null)
            }}
          >
            Clear data source
          </button>
        </div>
      </header>

      <section ref={containerRef} className="mx-auto w-full max-w-3xl overflow-y-auto px-6 py-6">
        <div className="grid gap-4">
          {messages.map((m) => (
            <ChatBubble key={m.id} role={m.role} content={m.content} />
          ))}
          {isStreaming && <ChatBubble role="assistant" content={streamBuffer || "…"} />}
        </div>
      </section>

      <footer className="border-t border-border px-6 py-4">
        <form
          onSubmit={handleSend}
          className="mx-auto flex w-full max-w-3xl items-end gap-3"
          aria-label="Send a message"
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your data..."
            className="min-h-10 max-h-40 w-full resize-y rounded-md border border-border bg-card px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
            disabled={isStreaming}
          />
          <button
            type="submit"
            className="inline-flex h-10 shrink-0 items-center rounded-md bg-primary px-4 text-sm text-primary-foreground hover:opacity-90 disabled:opacity-50"
            disabled={isStreaming || !input.trim()}
          >
            Send
          </button>
        </form>
        <p className="mx-auto mt-2 max-w-3xl text-xs text-muted-foreground">
          Your query is sent to {'"'}
          {`${API_BASE}/query`}
          {'"'} as JSON along with your {dataSource.type === "csv" ? "csv_url" : "db_url"}. The response is streamed
          when supported, otherwise returned as a single JSON {"{'final_answer': '...'}"}.
        </p>
      </footer>
    </main>
  )
}
