import { useQuery } from "@tanstack/react-query";
import { documentsApi } from "./api";

// File types this server can extract text from. Images are listed only when
// OCR is installed; until the server says so, assume it isn't.
const BASE_TYPES = ["PDF", "DOCX", "TXT"];
const EXTENSIONS = { PDF: ".pdf", DOCX: ".docx", TXT: ".txt", PNG: ".png", JPG: ".jpg,.jpeg" };

export function useUploadTypes() {
  const { data } = useQuery({
    queryKey: ["upload-capabilities"],
    queryFn: documentsApi.capabilities,
    staleTime: Infinity,
  });
  const types = data?.accepted_types || BASE_TYPES;
  return { types, accept: types.map((t) => EXTENSIONS[t]).join(",") };
}
