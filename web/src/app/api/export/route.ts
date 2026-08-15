import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const messageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().max(8000),
  timestamp: z.number().optional(),
});

const exportSchema = z.object({
  messages: z.array(messageSchema).min(1).max(100),
  format: z.enum(["json", "markdown", "txt"]).default("markdown"),
});

function toMarkdown(messages: z.infer<typeof messageSchema>[]): string {
  const lines = [
    "# FloatChat Conversation Export",
    "",
    `**Exported:** ${new Date().toUTCString()}`,
    `**Messages:** ${messages.length}`,
    "",
    "---",
    "",
  ];
  for (const m of messages) {
    const ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : "";
    lines.push(`### ${m.role === "user" ? "You" : "FloatChat AI"}${ts ? ` — ${ts}` : ""}`);
    lines.push("", m.content, "");
  }
  return lines.join("\n");
}

function toPlainText(messages: z.infer<typeof messageSchema>[]): string {
  return messages
    .map((m) => `[${m.role.toUpperCase()}]: ${m.content}`)
    .join("\n\n");
}

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const parsed = exportSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid export payload" }, { status: 400 });
  }

  const { messages, format } = parsed.data;

  if (format === "json") {
    return new NextResponse(JSON.stringify(messages, null, 2), {
      headers: {
        "Content-Type": "application/json",
        "Content-Disposition": `attachment; filename="floatchat-export.json"`,
      },
    });
  }

  if (format === "txt") {
    return new NextResponse(toPlainText(messages), {
      headers: {
        "Content-Type": "text/plain",
        "Content-Disposition": `attachment; filename="floatchat-export.txt"`,
      },
    });
  }

  return new NextResponse(toMarkdown(messages), {
    headers: {
      "Content-Type": "text/markdown",
      "Content-Disposition": `attachment; filename="floatchat-export.md"`,
    },
  });
}
