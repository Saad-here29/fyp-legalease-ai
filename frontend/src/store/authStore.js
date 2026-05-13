import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { STORAGE_KEYS } from "@/constants";

/**
 * Auth store — only the user profile is kept here. Access + refresh tokens
 * are stored as HttpOnly cookies set by the backend, so JavaScript cannot
 * read them. That's deliberate: it removes the XSS-exfiltration risk that
 * plain localStorage tokens have.
 *
 * `isAuthenticated` is therefore derived from "do we have a user we trust";
 * if the cookies expire, the next API call will 401 and the axios
 * interceptor will trigger a refresh or, on failure, clear this store.
 */
export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,

      setSession: ({ user }) => {
        set({ user, isAuthenticated: true });
      },

      updateUser: (partial) => set((s) => ({ user: { ...s.user, ...partial } })),

      clear: () => {
        set({ user: null, isAuthenticated: false });
      },

      hasRole: (role) => get().user?.role === role,
    }),
    {
      name: STORAGE_KEYS.USER,
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ user: s.user, isAuthenticated: s.isAuthenticated }),
    }
  )
);
