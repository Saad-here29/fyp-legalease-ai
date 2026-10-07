import { useQuery } from "@tanstack/react-query";
import { kbApi } from "./api";

// The scraping update log (kb-v2 C3), or null while SCRAPED_V2 is off (404).
export function useUpdates() {
  const { data } = useQuery({
    queryKey: ["kb-updates"],
    queryFn: () =>
      kbApi.updates().catch((e) => {
        if (e?.response?.status === 404) return null;
        throw e;
      }),
    staleTime: 60 * 1000,
    retry: false,
  });
  return data || null;
}
