import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";
import MessageContent from "./MessageContent";

declare global {
  interface Window {
    __xss?: boolean;
  }
}

afterEach(cleanup);

describe("MessageContent", () => {
  beforeEach(() => {
    window.__xss = undefined;
  });

  it("never turns injected markup into a live, executable DOM node (XSS regression)", () => {
    const malicious = '<img src=x onerror="window.__xss=true">';
    const { container } = render(<MessageContent content={malicious} />);

    const img = container.querySelector("img");

    // jsdom does not perform real image loading, so a genuine <img onerror>
    // never auto-fires here. Dispatch the failure event manually so this
    // assertion is meaningful (it would have caught the old
    // dangerouslySetInnerHTML implementation) rather than vacuously true.
    img?.dispatchEvent(new Event("error"));

    expect(img).toBeNull();
    expect(window.__xss).not.toBe(true);
  });

  it("does not execute a javascript: URL smuggled in as a link", () => {
    const malicious = '[click me](javascript:window.__xss=true)';
    const { container } = render(<MessageContent content={malicious} />);

    const link = container.querySelector("a");
    if (link) {
      // react-markdown's default urlTransform already strips javascript:
      // URLs, but assert directly on the rendered href as well.
      expect(link.getAttribute("href")).not.toMatch(/^javascript:/i);
    }
    expect(window.__xss).not.toBe(true);
  });

  it("still renders bold, italic, and inline code via markdown syntax", () => {
    const { getByText } = render(
      <MessageContent content="**bold** and *italic* and `code`" />
    );

    expect(getByText("bold").tagName.toLowerCase()).toBe("strong");
    expect(getByText("italic").tagName.toLowerCase()).toBe("em");
    expect(getByText("code").tagName.toLowerCase()).toBe("code");
  });
});
