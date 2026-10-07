import { useQuery } from "@tanstack/react-query";
import { kbApi } from "./api";

// Judgments (kb-v2 C2) exist only when the backend runs with JUDGMENTS_V2 on;
// otherwise /kb/judgments is a 404 and every judgment control stays hidden.
// Returns the first page's counts and facets (courts, years, topics), or null.
export function useJudgmentsInfo() {
  const { data } = useQuery({
    queryKey: ["kb-judgments-info"],
    queryFn: () =>
      kbApi.judgments({ page_size: 1 }).catch((e) => {
        if (e?.response?.status === 404) return null;
        throw e;
      }),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
  return data || null;
}
