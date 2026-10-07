# LegalEase kb-v2 C7: embed the exported chunks on a Google Colab GPU.
#
# In Colab: Runtime > Change runtime type > T4 GPU. Upload chunks_for_colab.jsonl
# (Files panel, left), paste this whole file into ONE cell and run it. When it
# finishes it downloads vectors_for_legalease.zip (or find it in the Files panel).
# Unzip its .npz files into backend/storage/kb/vector_cache/ and run
# scripts/kb/build_index_v2_all.py --budget 0.
#
# Locally (the round-trip test, CPU):
#   python scripts/kb/colab_embed.py chunks.jsonl out_dir --device cpu --no-zip
#
# Output: colab_<date-time>_00001.npz, ... (a new name each run, so files from
# two runs never overwrite each other in the cache folder), with exactly the keys and arrays
# the builder's vector cache reads: "keys" (the chunk's key from the export,
# sha256 of model name + chunk text) and "vectors" (float32, L2-normalised,
# 384 columns), the same model and normalisation as the app
# (app/ai/embeddings.py: normalize_embeddings=True).

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile

MODEL = "paraphrase-multilingual-MiniLM-L12-v2"      # settings.EMBEDDING_MODEL_NAME; part of every key
SHARD = 20000                                       # vectors per .npz file
BATCH = 256


def key(text):
    """The builder's vector_key: sha256 of "<model>\n<chunk text>"."""
    return hashlib.sha256(f"{MODEL}\n{text}".encode()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("chunks", nargs="?", default="/content/chunks_for_colab.jsonl")
    ap.add_argument("out", nargs="?", default="/content/legalease_vectors")
    ap.add_argument("--device", default=None, help="cuda / cpu (default: cuda when available)")
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--no-zip", action="store_true")
    args, _unknown = ap.parse_known_args(argv)      # Colab adds its own -f argument

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "sentence-transformers"])
        from sentence_transformers import SentenceTransformer
    import numpy as np

    with open(args.chunks, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    bad = [r["key"] for r in rows if key(r["text"]) != r["key"]]
    if bad:
        raise SystemExit(f"{len(bad)} keys don't match their text (wrong model name or edited file); stopping")
    print(f"{len(rows)} chunks; keys checked")

    import torch
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = SentenceTransformer(MODEL if "/" in MODEL else f"sentence-transformers/{MODEL}", device=device)
    os.makedirs(args.out, exist_ok=True)
    t0, written = time.time(), []
    run = time.strftime("%Y%m%d-%H%M%S")
    for s in range(0, len(rows), SHARD):
        part = rows[s:s + SHARD]
        vecs = model.encode([r["text"] for r in part], batch_size=args.batch, convert_to_numpy=True,
                            show_progress_bar=True, normalize_embeddings=True).astype(np.float32)
        path = os.path.join(args.out, f"colab_{run}_{s // SHARD + 1:05d}.npz")
        np.savez(path, keys=np.array([r["key"] for r in part]), vectors=vecs)
        written.append(path)
        done = s + len(part)
        print(f"{done}/{len(rows)} embedded ({done / max(time.time() - t0, 1e-6):.0f} chunks/s) -> {path}")
    print(f"{len(rows)} vectors in {time.time() - t0:.0f} s on {device}")
    if not args.no_zip:
        zpath = os.path.join(os.path.dirname(args.out) or ".", "vectors_for_legalease.zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
            for p in written:
                z.write(p, os.path.basename(p))
        print(f"zip: {zpath}")
        try:
            from google.colab import files
            files.download(zpath)
        except ImportError:
            pass
    return written


if __name__ == "__main__":
    main()
