import { defineStore } from "pinia";
import { useAuthStore } from "./auth";

export const useUserStore = defineStore("user", {
  getters: {
    currentUser: () => useAuthStore().profile,
    displayName(): string {
      const profile = useAuthStore().profile;
      return profile?.employee_name || profile?.username || "";
    },
  },
});
