import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { casesApi } from "./api";

// Edit a case's details (assigned lawyer only; the backend enforces it).
// Only changed fields are sent; an empty field clears it. A change to the
// next hearing date shows on the timeline.
const FIELDS = [
  ["case_number", "Case number", "text", 64],
  ["court_code", "Court", "text", 60],
  ["petitioner", "Petitioner / plaintiff", "text", 200],
  ["respondent", "Respondent / defendant", "text", 200],
  ["filing_date", "Filing date", "date"],
  ["next_hearing_date", "Next hearing", "date"],
];

export default function CaseDetailsForm({ c, onDone }) {
  const initial = Object.fromEntries([...FIELDS.map(([k]) => [k, c[k] || ""]), ["description", c.description || ""]]);
  const [values, setValues] = useState(initial);
  const set = (k) => (e) => setValues((v) => ({ ...v, [k]: e.target.value }));

  const save = useMutation({
    mutationFn: (payload) => casesApi.update(c.id, payload),
    onSuccess: () => {
      toast.success("Case details saved.");
      onDone(true);
    },
    onError: (e) =>
      toast.error(e?.response?.data?.error?.message || "Could not save the details.", {
        description: e?.response?.data?.error?.hint,
      }),
  });

  const submit = (e) => {
    e.preventDefault();
    const changed = Object.fromEntries(
      Object.entries(values)
        .filter(([k, v]) => v.trim() !== initial[k])
        .map(([k, v]) => [k, v.trim() || null])
    );
    if (Object.keys(changed).length === 0) return onDone(false);
    save.mutate(changed);
  };

  return (
    <form onSubmit={submit} className="pt-4 space-y-4">
      {FIELDS.map(([k, label, type, max]) => (
        <div key={k}>
          <label htmlFor={`cd-${k}`} className="ds-label">{label}</label>
          <input id={`cd-${k}`} type={type} value={values[k]} onChange={set(k)} maxLength={max} className="ds-input" />
        </div>
      ))}
      <div>
        <label htmlFor="cd-description" className="ds-label">Case summary</label>
        <textarea id="cd-description" rows={4} maxLength={4000} value={values.description} onChange={set("description")}
          className="ds-input py-3" />
      </div>
      <div className="flex gap-3">
        <button type="submit" className="ds-btn-primary" disabled={save.isPending}>
          {save.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Saving" /> : "Save"}
        </button>
        <button type="button" className="ds-btn-secondary" onClick={() => onDone(false)}>Cancel</button>
      </div>
    </form>
  );
}
