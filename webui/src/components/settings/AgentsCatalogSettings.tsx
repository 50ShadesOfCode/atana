import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { useTranslation } from "react-i18next";

import {
  SettingsGroup,
  SettingsRow,
  SettingsSectionTitle,
} from "@/components/settings/shared/SettingsControls";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { SearchInput } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { fetchAgents } from "@/lib/api";
import type { AgentSummary, AgentsPayload } from "@/lib/types";
import { useClient } from "@/providers/ClientProvider";

type AgentsState = {
  payload: AgentsPayload | null;
  loading: boolean;
  error: boolean;
};

const COLLAPSED_DESCRIPTION_CHARS = 160;

export function AgentsCatalogSettings({ onRunCommand }: {
  onRunCommand?: (content: string) => unknown;
}) {
  const { t } = useTranslation();
  const { getToken } = useClient();
  const [state, setState] = useState<AgentsState>({ payload: null, loading: true, error: false });
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [running, setRunning] = useState<AgentSummary | null>(null);
  const [task, setTask] = useState("");

  const load = useCallback(() => {
    setState((current) => ({ ...current, loading: true, error: false }));
    fetchAgents(getToken())
      .then((payload) => setState({ payload, loading: false, error: false }))
      .catch(() => setState((current) => ({ ...current, loading: false, error: true })));
  }, [getToken]);

  useEffect(load, [load]);

  const agents = state.payload?.agents ?? [];
  const issues = state.payload?.issues ?? [];
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return agents;
    return agents.filter(
      (agent) =>
        agent.name.toLowerCase().includes(needle)
        || agent.description.toLowerCase().includes(needle),
    );
  }, [agents, query]);

  const closeRun = () => {
    setRunning(null);
    setTask("");
  };
  const startRun = () => {
    if (running === null || !task.trim()) return;
    void onRunCommand?.(`/agents run ${running.name} ${task.trim()}`);
    closeRun();
  };

  return (
    <div className="settings-stack">
      <SettingsSectionTitle>{t("settings.subagents.title")}</SettingsSectionTitle>
      <p className="text-sm text-muted-foreground">{t("settings.subagents.description")}</p>
      <div className="flex items-center gap-2">
        <SearchInput
          className="flex-1"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("settings.subagents.search")}
          aria-label={t("settings.subagents.search")}
        />
        <Button variant="outline" onClick={load} disabled={state.loading}>
          <RefreshCw className="size-4" />
          {t("settings.subagents.refresh")}
        </Button>
      </div>
      {state.loading && state.payload === null ? (
        <p className="text-sm text-muted-foreground">{t("settings.subagents.loading")}</p>
      ) : null}
      {state.error ? (
        <div className="flex flex-wrap items-center gap-3">
          <p role="alert" className="text-sm text-destructive">
            {t("settings.subagents.loadFailed")}
          </p>
          <Button variant="outline" onClick={load}>{t("settings.subagents.retry")}</Button>
        </div>
      ) : null}
      {state.payload && agents.length === 0 && issues.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("settings.subagents.empty")}</p>
      ) : null}
      {state.payload && agents.length > 0 && visible.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("settings.subagents.noMatches")}</p>
      ) : null}
      {visible.length > 0 ? (
        <SettingsGroup>
          {visible.map((agent) => {
            const open = expanded[agent.name] ?? false;
            const long = agent.description.length > COLLAPSED_DESCRIPTION_CHARS;
            return (
              <SettingsRow key={agent.name} title={<span className="font-medium">{agent.name}</span>}>
                <div className="space-y-1.5">
                  <p className={open ? "text-sm text-muted-foreground" : "line-clamp-2 text-sm text-muted-foreground"}>
                    {agent.description}
                  </p>
                  {long ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setExpanded((current) => ({ ...current, [agent.name]: !open }))}
                    >
                      {open ? t("settings.subagents.showLess") : t("settings.subagents.showMore")}
                    </Button>
                  ) : null}
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                    <span>
                      {agent.tools === null ? (
                        t("settings.subagents.allTools")
                      ) : agent.tools.length === 0 ? (
                        t("settings.subagents.noTools")
                      ) : (
                        agent.tools.map((tool, index) => (
                          <span key={tool}>
                            {index > 0 ? ", " : ""}
                            {agent.tools_missing.includes(tool) ? (
                              <s className="text-destructive/80" title={t("settings.subagents.unavailableTool")}>
                                {tool}
                              </s>
                            ) : (
                              tool
                            )}
                          </span>
                        ))
                      )}
                    </span>
                    <span className="font-mono">{agent.path}</span>
                  </div>
                  {onRunCommand ? (
                    <Button variant="outline" size="sm" onClick={() => setRunning(agent)}>
                      {t("settings.subagents.run")}
                    </Button>
                  ) : null}
                </div>
              </SettingsRow>
            );
          })}
        </SettingsGroup>
      ) : null}
      {issues.length > 0 ? (
        <>
          <SettingsSectionTitle>{t("settings.subagents.skipped")}</SettingsSectionTitle>
          <SettingsGroup>
            {issues.map((issue) => (
              <SettingsRow
                key={issue.name}
                title={<span className="font-mono text-xs">agents/{issue.name}.md</span>}
              >
                <p className="text-sm text-muted-foreground">{issue.reason}</p>
              </SettingsRow>
            ))}
          </SettingsGroup>
        </>
      ) : null}
      <Dialog
        open={running !== null}
        onOpenChange={(open) => {
          if (!open) closeRun();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("settings.subagents.runTitle", { name: running?.name ?? "" })}</DialogTitle>
            <DialogDescription>{running?.description}</DialogDescription>
          </DialogHeader>
          <Textarea
            value={task}
            onChange={(event) => setTask(event.target.value)}
            placeholder={t("settings.subagents.runTaskPlaceholder")}
            aria-label={t("settings.subagents.runTaskLabel")}
            rows={4}
          />
          <DialogFooter>
            <Button variant="outline" onClick={closeRun}>{t("common.cancel")}</Button>
            <Button onClick={startRun} disabled={!task.trim()}>
              {t("settings.subagents.runStart")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
