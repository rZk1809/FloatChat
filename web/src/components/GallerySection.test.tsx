import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import GallerySection from "./GallerySection";

afterEach(cleanup);

const PLOTS = [
  { file: "ts_diagram.png", title: "T-S Diagram with Clusters", category: "Clustering" },
  { file: "feature_importance.png", title: "XGBoost Feature Importance", category: "ML" },
  { file: "pdp_latitude.png", title: "Partial Dependence: Latitude", category: "XAI" },
];

// next/image returns a plain img in tests
vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

describe("GallerySection", () => {
  it("renders all plots by default", () => {
    render(<GallerySection plots={PLOTS} />);
    expect(screen.getByLabelText("View T-S Diagram with Clusters")).toBeInTheDocument();
    expect(screen.getByLabelText("View XGBoost Feature Importance")).toBeInTheDocument();
    expect(screen.getByLabelText("View Partial Dependence: Latitude")).toBeInTheDocument();
  });

  it("filters by category when a category pill is clicked", () => {
    render(<GallerySection plots={PLOTS} />);
    fireEvent.click(screen.getByRole("button", { name: /^ML/ }));
    expect(screen.getByLabelText("View XGBoost Feature Importance")).toBeInTheDocument();
    expect(screen.queryByLabelText("View T-S Diagram with Clusters")).not.toBeInTheDocument();
  });

  it("shows all plots when All is re-selected", () => {
    render(<GallerySection plots={PLOTS} />);
    fireEvent.click(screen.getByRole("button", { name: /^ML/ }));
    fireEvent.click(screen.getByRole("button", { name: /^All/ }));
    expect(screen.getAllByRole("button", { name: /^View / })).toHaveLength(PLOTS.length);
  });

  it("filters plots by search query", async () => {
    render(<GallerySection plots={PLOTS} />);
    const input = screen.getByPlaceholderText("Search plots…");
    fireEvent.change(input, { target: { value: "Feature" } });
    // debounce is 200ms — advance timers isn't needed here because we just
    // check that the input is wired (filtering updates on next render)
    await screen.findByLabelText("View XGBoost Feature Importance");
    expect(screen.queryByLabelText("View T-S Diagram with Clusters")).not.toBeInTheDocument();
  });

  it("clears search with the × button", async () => {
    render(<GallerySection plots={PLOTS} />);
    const input = screen.getByPlaceholderText("Search plots…");
    fireEvent.change(input, { target: { value: "Feature" } });
    const clearBtn = screen.getByLabelText("Clear search");
    fireEvent.click(clearBtn);
    expect((input as HTMLInputElement).value).toBe("");
  });

  it("shows empty state when no plots match search", async () => {
    render(<GallerySection plots={PLOTS} />);
    const input = screen.getByPlaceholderText("Search plots…");
    fireEvent.change(input, { target: { value: "zzznomatch" } });
    await screen.findByText(/No visualizations match/);
  });
});
