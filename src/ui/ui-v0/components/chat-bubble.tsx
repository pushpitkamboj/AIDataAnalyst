export function ChatBubble({ role, content }: { role: "user" | "assistant"; content: string }) {
  const isUser = role === "user"
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-lg border px-3 py-2 text-sm ${
          isUser ? "bg-primary text-primary-foreground border-transparent" : "bg-card text-foreground border-border"
        }`}
        aria-live="polite"
      >
        {content}
      </div>
    </div>
  )
}
