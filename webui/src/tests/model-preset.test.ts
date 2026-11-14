import { describe, expect, it } from "vitest";

import { toModelBadgeInfo } from "@/components/thread/model-preset";
import type { SettingsPayload } from "@/lib/types";

const baseSettings = {
  agent: {
    model: "openai-codex/gpt-5.5",
    provider: "auto",
    resolved_provider: "openai_codex",
    model_preset: "default",
  },
  model_presets: [
    {
      name: "default",
      label: "Default",
      is_default: true,
      active: true,
      model: "openai-codex/gpt-5.5",
      provider: "auto",
      resolved_provider: "openai_codex",
    },
    {
      name: "deep",
      is_default: false,
      active: false,
      model: "openai/gpt-5",
      provider: "openai",
      resolved_provider: "openai",
    },
  ],
  providers: [
    { name: "openai_codex", label: "OpenAI", configured: true },
    { name: "openai", label: "OpenAI", configured: true },
    { name: "opencode_go", label: "OpenCode Go", configured: true },
    { name: "anthropic", label: "Anthropic", configured: true },
  ],
} as SettingsPayload;

describe("toModelBadgeInfo", () => {
  it("labels a scoped preset with its own name and provider", () => {
    const badge = toModelBadgeInfo("openai-codex/gpt-5.5", baseSettings, "deep");

    expect(badge.label).toBe("deep");
    expect(badge.provider).toBe("openai");
    expect(badge.needsSetup).toBe(false);
  });

  it("trusts the provider stored with an explicit session model", () => {
    const badge = toModelBadgeInfo(
      "openai-codex/gpt-5.5",
      baseSettings,
      "",
      "opencode_go/deepseek-v4-pro",
      "opencode_go",
    );

    expect(badge.label).toBe("deepseek-v4-pro");
    expect(badge.provider).toBe("opencode_go");
    expect(badge.providerLabel).toBe("OpenCode Go");
    expect(badge.needsSetup).toBe(false);
  });

  it("infers an auto provider from the model, not from the default preset", () => {
    const badge = toModelBadgeInfo(
      "openai-codex/gpt-5.5",
      baseSettings,
      "",
      "claude-sonnet-4",
      "auto",
    );

    expect(badge.provider).toBe("anthropic");
    expect(badge.needsSetup).toBe(false);
  });

  it("keeps an explicit model usable when its provider row is missing", () => {
    const badge = toModelBadgeInfo(
      "openai-codex/gpt-5.5",
      baseSettings,
      "",
      "some-local-model",
      "my_provider",
    );

    expect(badge.provider).toBe("my_provider");
    expect(badge.needsSetup).toBe(false);
  });
});
