import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { AgentsCatalogSettings } from "@/components/settings/AgentsCatalogSettings";
import { ClientProvider } from "@/providers/ClientProvider";

const REVIEWER = {
  name: "reviewer",
  description: "Reviews diffs.",
  tools: ["read_file", "grep"],
  tools_missing: ["grep"],
  path: "agents/reviewer.md",
};

function renderAgents(payload: unknown, onRunCommand?: (content: string) => unknown) {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  })));
  render(
    <ClientProvider client={{ requestMutation: vi.fn(), status: "open", onStatus: () => () => {} } as never} token="tok">
      <AgentsCatalogSettings onRunCommand={onRunCommand} />
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
      REVIEWER,
      { name: "researcher", description: "Researches.", tools: null, tools_missing: [], path: "agents/researcher.md" },
    ],
    issues: [{ name: "broken", reason: "frontmatter is not valid YAML" }],
  });

  expect(await screen.findByText("reviewer")).toBeVisible();
  expect(screen.getByText("Reviews diffs.")).toBeVisible();
  expect(screen.getByText("read_file", { exact: false })).toBeInTheDocument();
  expect(screen.getByText("All subagent tools")).toBeVisible();
  expect(screen.getByText("agents/researcher.md")).toBeVisible();
  expect(screen.getByText("Skipped files")).toBeVisible();
  expect(screen.getByText("agents/broken.md")).toBeVisible();
  expect(screen.getByText("frontmatter is not valid YAML")).toBeVisible();
});

it("marks tools a subagent cannot use", async () => {
  renderAgents({ agents: [REVIEWER], issues: [] });

  expect(await screen.findByText("grep")).toHaveProperty("tagName", "S");
});

it("filters roles by name or description", async () => {
  renderAgents({
    agents: [
      REVIEWER,
      { name: "researcher", description: "Reads papers.", tools: null, tools_missing: [], path: "agents/researcher.md" },
    ],
    issues: [],
  });

  await screen.findByText("reviewer");
  fireEvent.change(screen.getByLabelText("Search agents"), { target: { value: "papers" } });

  expect(screen.queryByText("reviewer")).not.toBeInTheDocument();
  expect(screen.getByText("researcher")).toBeVisible();
});

it("starts a role from its card", async () => {
  const onRun = vi.fn();
  renderAgents({ agents: [REVIEWER], issues: [] }, onRun);

  fireEvent.click(await screen.findByRole("button", { name: "Run…" }));
  fireEvent.change(screen.getByLabelText("Task"), { target: { value: "review the diff" } });
  fireEvent.click(screen.getByRole("button", { name: "Start task" }));

  expect(onRun).toHaveBeenCalledWith("/agents run reviewer review the diff");
});

it("explains where roles come from when there are none", async () => {
  renderAgents({ agents: [], issues: [] });

  expect(await screen.findByText(/No custom agents yet/)).toBeVisible();
});
