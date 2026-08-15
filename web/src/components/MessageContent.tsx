import ReactMarkdown, { type Components } from "react-markdown";
import remarkBreaks from "remark-breaks";

// Safe chat-message renderer.
//
// This intentionally does NOT use `rehype-raw` (or any other plugin that
// turns raw HTML in the source string into real DOM nodes) and does NOT use
// `dangerouslySetInnerHTML`. react-markdown's default pipeline never
// executes/renders embedded HTML — it is stripped or shown as inert text —
// so message content (from the user, or from the LLM) can never inject a
// live <script>, <img onerror>, event-handler attribute, etc. into the page.
//
// remark-breaks is the one addition beyond plain react-markdown: it makes a
// single "\n" behave like a line break (matching the old behavior, which
// turned every "\n" into a <br/>), instead of CommonMark's default of
// collapsing single newlines into a space. It carries no HTML/security
// implications — it only changes how soft line breaks are parsed.
const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => (
    <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-cyan-300 underline hover:text-cyan-200"
    >
      {children}
    </a>
  ),
  code: ({ className, children, ...props }) => {
    const isBlock = Boolean(className);
    if (isBlock) {
      return (
        <code
          className={`my-1 block overflow-x-auto rounded bg-ocean-800/80 p-2 font-mono text-xs text-cyan-300 ${className ?? ""}`}
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <code
        className="rounded bg-ocean-700 px-1 font-mono text-sm text-cyan-400"
        {...props}
      >
        {children}
      </code>
    );
  },
};

export default function MessageContent({ content }: { content: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkBreaks]} components={markdownComponents}>
      {content}
    </ReactMarkdown>
  );
}
