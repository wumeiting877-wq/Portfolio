import { computed, onScopeDispose, reactive, watch, type WatchSource } from "vue";
import { useRoute, type RouteLocationRaw } from "vue-router";
import { breadcrumbTitle, type BreadcrumbMetaItem } from "../config/roleUi";
import { useAuthStore } from "../stores/auth";

export type BreadcrumbItem = {
  title: string;
  to?: RouteLocationRaw;
};

const dynamicTitles = reactive<Record<string, string>>({});

export function useDynamicBreadcrumbTitle(source: WatchSource<string | null | undefined>) {
  const route = useRoute();
  const routeName = typeof route.name === "string" ? route.name : "";

  watch(
    source,
    (title) => {
      if (!routeName) return;
      const next = title?.trim();
      if (next) {
        dynamicTitles[routeName] = next;
        return;
      }
      delete dynamicTitles[routeName];
    },
    { immediate: true },
  );

  onScopeDispose(() => {
    if (routeName) delete dynamicTitles[routeName];
  });
}

export function useBreadcrumb() {
  const route = useRoute();
  const auth = useAuthStore();

  return computed<BreadcrumbItem[]>(() => {
    const record = [...route.matched]
      .reverse()
      .find((item) => Array.isArray(item.meta.breadcrumb));
    const defined = (record?.meta.breadcrumb as BreadcrumbMetaItem[] | undefined) ?? [];
    const items: BreadcrumbItem[] = defined.map((item) => ({
      title: breadcrumbTitle(auth.role, item),
      to: item.to,
    }));
    if (items.length === 0) {
      const title = typeof route.meta.title === "string" ? route.meta.title : "";
      return title ? [{ title }] : [];
    }

    const routeName =
      typeof record?.name === "string"
        ? record.name
        : typeof route.name === "string"
          ? route.name
          : "";
    const dynamicTitle = routeName ? dynamicTitles[routeName] : "";
    if (dynamicTitle) {
      items[items.length - 1] = { title: dynamicTitle };
    }
    return items;
  });
}
