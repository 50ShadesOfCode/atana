import { useCallback, useEffect, useRef, useState } from "react";

import { fetchProviderModels } from "@/lib/api";
import type { SettingsPayload } from "@/lib/types";
import type { ModelCatalogOption } from "@/components/thread/ModelPresetBadge";

const CATALOG_TTL_MS = 5 * 60_000;
let catalogCache: { at: number; providers: string; models: ModelCatalogOption[] } | null = null;

interface ModelCatalog {
  models: ModelCatalogOption[];
  loading: boolean;
  /** Retry an empty catalog, e.g. when the picker opens before the prefetch finished. */
  reload: () => void;
}

/**
 * Load the model catalog of every configured provider for the composer picker.
 * Cached for a few minutes: each provider costs one upstream model-list request.
 */
export function useModelCatalog(
  settings: SettingsPayload | null,
  getToken: () => string,
): ModelCatalog {
  const [models, setModels] = useState<ModelCatalogOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  const tokenRef = useRef(getToken);
  tokenRef.current = getToken;

  useEffect(() => {
    if (!settings) return;
    const providers = settings.providers.filter(
      (provider) => provider.configured && provider.model_selectable !== false,
    );
    if (!providers.length) {
      setLoading(false);
      return;
    }
    const providersKey = providers.map((provider) => provider.name).join(",");
    if (
      catalogCache
      && catalogCache.providers === providersKey
      && Date.now() - catalogCache.at < CATALOG_TTL_MS
    ) {
      setModels(catalogCache.models);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
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
      // A failed request must not pin an empty list for the whole TTL.
      if (loaded.length) catalogCache = { at: Date.now(), providers: providersKey, models: loaded };
      setModels(loaded);
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [settings, retry]);

  const reload = useCallback(() => {
    if (!loading) setRetry((value) => value + 1);
  }, [loading]);

  return { models, loading, reload };
}
