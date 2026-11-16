import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { AgentsCatalogSettings } from "@/components/settings/AgentsCatalogSettings";
import { ClientProvider } from "@/providers/ClientProvider";

function renderAgents(payload: unknown) {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  })));
  render(
    <ClientProvider client={{ requestMutation: vi.fn(), status: "open", onStatus: () => () => {} } as never} token="tok">
      <AgentsCatalogSettings />
    </ClientProvider>,
  );
}

beforeEach(() => {
  vi.stubGlobal("matchMedia", vi.fn(() => ({
    matches: false, media: "", onchange: null,
    addEventListener: vi.fn(), removeEventListener: vi.fn(),
    addListener: vi.fn(), removeListener: vi.fn(), dispatchEvent: vi.fn(),
  })));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

it("lists roles with their tools and skipped files", async () => {
  renderAgents({
    agents: [
      { name: "reviewer", description: "Reviews diffs.", tools: ["read_file", "rg"], path: "agents/reviewer.md" },
      { name: "researcher", description: "Researches.", tools: null, path: "agents/researcher.md" },
    ],
    issues: [{ name: "broken", reason: "invalid metadata" }],
  });

  expect(await screen.findByText("reviewer")).toBeVisible();
  expect(screen.getByText("Reviews diffs.")).toBeVisible();
  expect(screen.getByText("read_file, rg")).toBeVisible();
  expect(screen.getByText("All subagent tools")).toBeVisible();
  expect(screen.getByText("agents/researcher.md")).toBeVisible();
  expect(screen.getByText("Skipped files")).toBeVisible();
  expect(screen.getByText("broken")).toBeVisible();
  expect(screen.getByText("invalid metadata")).toBeVisible();
});

it("explains where roles come from when there are none", async () => {
  renderAgents({ agents: [], issues: [] });

  expect(await screen.findByText(/No custom agents yet/)).toBeVisible();
});
