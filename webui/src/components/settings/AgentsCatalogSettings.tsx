import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  SettingsGroup,
  SettingsRow,
  SettingsSectionTitle,
} from "@/components/settings/shared/SettingsControls";
import { fetchAgents } from "@/lib/api";
import type { AgentsPayload } from "@/lib/types";
import { useClient } from "@/providers/ClientProvider";

type AgentsState =
  | { status: "loading" | "error"; payload: null }
  | { status: "ready"; payload: AgentsPayload };

export function AgentsCatalogSettings() {
  const { t } = useTranslation();
  const { getToken } = useClient();
  const [state, setState] = useState<AgentsState>({ status: "loading", payload: null });

  useEffect(() => {
    let cancelled = false;
    fetchAgents(getToken())
      .then((payload) => {
        if (!cancelled) setState({ status: "ready", payload });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "error", payload: null });
      });
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  const payload = state.payload;
  return (
    <div className="settings-stack">
      <SettingsSectionTitle>{t("settings.subagents.title")}</SettingsSectionTitle>
      <p className="text-sm text-muted-foreground">{t("settings.subagents.description")}</p>
      {state.status === "loading" ? (
        <p className="text-sm text-muted-foreground">{t("settings.subagents.loading")}</p>
      ) : null}
      {state.status === "error" ? (
        <p role="alert" className="text-sm text-destructive">{t("settings.subagents.loadFailed")}</p>
      ) : null}
      {payload && payload.agents.length === 0 && payload.issues.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("settings.subagents.empty")}</p>
      ) : null}
      {payload && payload.agents.length > 0 ? (
        <SettingsGroup>
          {payload.agents.map((agent) => (
            <SettingsRow key={agent.name} title={<span className="font-medium">{agent.name}</span>}>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">{agent.description}</p>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                  <span>
                    {agent.tools === null
                      ? t("settings.subagents.allTools")
                      : agent.tools.length === 0
                        ? t("settings.subagents.noTools")
                        : agent.tools.join(", ")}
                  </span>
                  <span className="font-mono">{agent.path}</span>
                </div>
              </div>
            </SettingsRow>
          ))}
        </SettingsGroup>
      ) : null}
      {payload && payload.issues.length > 0 ? (
        <>
          <SettingsSectionTitle>{t("settings.subagents.skipped")}</SettingsSectionTitle>
          <SettingsGroup>
            {payload.issues.map((issue) => (
              <SettingsRow key={issue.name} title={<span className="font-medium">{issue.name}</span>}>
                <p className="text-sm text-muted-foreground">{issue.reason}</p>
              </SettingsRow>
            ))}
          </SettingsGroup>
        </>
      ) : null}
    </div>
  );
}
