import { useEffect, useRef, useState } from "react";

import { fetchProviderModels } from "@/lib/api";
import type { SettingsPayload } from "@/lib/types";
import type { ModelCatalogOption } from "@/components/thread/ModelPresetBadge";

interface ModelCatalog {
  models: ModelCatalogOption[];
  loading: boolean;
}

/**
 * Load the model catalog of every configured provider for the composer picker.
 * Fetched lazily: only while the picker is open.
 */
export function useModelCatalog(
  settings: SettingsPayload | null,
  getToken: () => string,
  enabled: boolean,
): ModelCatalog {
  const [models, setModels] = useState<ModelCatalogOption[]>([]);
  const [loading, setLoading] = useState(false);
  const tokenRef = useRef(getToken);
  tokenRef.current = getToken;

  useEffect(() => {
    if (!enabled || !settings) return;
    const providers = settings.providers.filter(
      (provider) => provider.configured && provider.model_selectable !== false,
    );
    if (!providers.length) return;
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
      setModels(rows.flat());
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [enabled, settings]);

  return { models, loading };
}
