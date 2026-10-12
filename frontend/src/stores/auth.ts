import { defineStore } from "pinia";
import { changePassword, fetchMe, login, logout, type MeResponse } from "../api/auth";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("access_token") || "",
    profile: null as MeResponse | null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    role: (state) => state.profile?.role || "",
    canViewEmployees: (state) => ["ADMIN", "BOSS"].includes(state.profile?.role || ""),
    canWriteEmployees: (state) => state.profile?.role === "ADMIN",
    canManageUsers: (state) => state.profile?.role === "ADMIN",
    canWriteProjects: (state) => state.profile?.role === "ADMIN",
    canWriteResources: (state) => state.profile?.role === "ADMIN",
    canWriteExpenses: (state) => state.profile?.role === "ADMIN",
    canViewRecurringExpenses: (state) => ["ADMIN", "BOSS"].includes(state.profile?.role || ""),
    canImport: (state) => state.profile?.role === "ADMIN",
    canExport: (state) => Boolean(state.profile?.role),
    canViewAuditLogs: (state) => ["ADMIN", "BOSS"].includes(state.profile?.role || ""),
    canViewSettings: (state) => ["ADMIN", "BOSS"].includes(state.profile?.role || ""),
    canWriteSettings: (state) => state.profile?.role === "ADMIN",
  },
  actions: {
    async login(username: string, password: string) {
      const result = await login(username, password);
      this.token = result.access_token;
      localStorage.setItem("access_token", result.access_token);
      await this.fetchProfile();
    },
    async fetchProfile() {
      this.profile = await fetchMe();
    },
    async changePassword(oldPassword: string, newPassword: string) {
      await changePassword(oldPassword, newPassword);
      if (this.profile) {
        this.profile.must_change_password = false;
      }
    },
    async logout() {
      try {
        await logout();
      } catch {
        // Client-side logout still proceeds.
      }
      this.token = "";
      this.profile = null;
      localStorage.removeItem("access_token");
    },
  },
});
