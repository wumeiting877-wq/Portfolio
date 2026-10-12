import { computed } from "vue";
import { routeLabel, type BusinessRouteName } from "../config/roleUi";
import { useAuthStore } from "../stores/auth";

export function useRouteTitle(routeName: BusinessRouteName) {
  const auth = useAuthStore();
  return computed(() => routeLabel(auth.role, routeName));
}
