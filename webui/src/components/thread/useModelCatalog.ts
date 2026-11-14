import { useEffect, useRef, useState } from "react";

import { fetchProviderModels } from "@/lib/api";
import type { SettingsPayload } from "@/lib/types";
import type { ModelCatalogOption } from "@/components/thread/ModelPresetBadge";

const CATALOG_TTL_MS = 5 * 60_000;
let catalogCache: { at: number; providers: string; models: ModelCatalogOption[] } | null = null;

/**
 * Load the model catalog of every configured provider for the composer picker.
 * Cached for a few minutes: each provider costs one upstream model-list request.
 */
export function useModelCatalog(
  settings: SettingsPayload | null,
  getToken: () => string,
  enabled: boolean,
): ModelCatalogOption[] {
  const [models, setModels] = useState<ModelCatalogOption[]>([]);
  const tokenRef = useRef(getToken);
  tokenRef.current = getToken;

  useEffect(() => {
    if (!enabled || !settings) return;
    const providers = settings.providers.filter(
      (provider) => provider.configured && provider.model_selectable !== false,
    );
    if (!providers.length) return;
    const providersKey = providers.map((provider) => provider.name).join(",");
    if (
      catalogCache
      && catalogCache.providers === providersKey
      && Date.now() - catalogCache.at < CATALOG_TTL_MS
    ) {
      setModels(catalogCache.models);
      return;
    }
    let cancelled = false;
    void Promise.all(providers.map(async (provider) => {
      try {
        const payload = await fetchProviderModels(tokenRef.current(), provider.name);
        return payload.models.map((model): ModelCatalogOption => ({
          provider: provider.name,
          providerLabel: provider.label,
          id: model.id,
          label: model.label ?? undefined,
          contextWindow: model.context_window ?? undefined,
        }));
      } catch {
        return [];
      }
    })).then((rows) => {
      if (cancelled) return;
      const loaded = rows.flat();
      catalogCache = { at: Date.now(), providers: providersKey, models: loaded };
      setModels(loaded);
    });
    return () => {
      cancelled = true;
    };
  }, [enabled, settings]);

  return models;
}
