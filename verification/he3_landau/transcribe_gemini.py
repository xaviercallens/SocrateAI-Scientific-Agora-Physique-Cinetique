"""
Independent multimodal transcription of Table IX (Kollar & Vollhardt 2000, arXiv:cond-mat/9906222,
page 19) with Gemini, compared cell by cell with the deterministic PDF-text-layer extraction.

Why, when the text layer already has the numbers: a model reading the RENDERED IMAGE is an
independent reader, so exact agreement with the text layer checks both. More importantly, this is
the tool for sources with no text layer, such as scanned copies of Greywall's original papers. It
should be trusted there only once it has shown exact agreement on a page like this one, where the
answer is known.

KEY. Read from the environment variable GEMINI_API_KEY, else from ~/.config/agora/gemini.env
(a line GEMINI_API_KEY=...; keep that file chmod 600). It is sent only in the x-goog-api-key
request header: never in a URL, never printed, never logged.

ENDPOINT. Google's Generative Language API by default; override the base URL with GEMINI_BASE_URL
for another endpoint that speaks the same generateContent protocol. Models are passed on the command
line; --list-models shows which ones the key can use.

Run:
  python3 verification/he3_landau/transcribe_gemini.py --list-models
  python3 verification/he3_landau/transcribe_gemini.py MODEL_A [MODEL_B ...]
"""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import extract_table_ix as X  # noqa: E402

BASE = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
KEY_FILE = Path.home() / ".config" / "agora" / "gemini.env"
PROMPT = (
    "This image is page 19 of a physics paper. It contains one table (Table IX) with 5 columns: "
    "P [bar], V [cm^3], gamma/R, (d gamma / dP)/R [10^-2 bar^-1], kappa(0,P) [10^-2 bar^-1]. "
    "Transcribe EVERY data row exactly as printed, digit for digit, keeping every printed digit and "
    "trailing zero, as strings. Do not round, compute, correct or infer anything. If a cell is "
    "unreadable, put \"?\" in it."
)
SCHEMA = {
    "type": "OBJECT",
    "properties": {"rows": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}}},
    "required": ["rows"],
}


def api_key():
    k = os.environ.get("GEMINI_API_KEY")
    if not k and KEY_FILE.exists():
        for line in KEY_FILE.read_text().splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                k = line.split("=", 1)[1].strip().strip("'\"")
    if not k:
        raise SystemExit(f"No key: set GEMINI_API_KEY or create {KEY_FILE} (chmod 600) with GEMINI_API_KEY=...")
    return k


def call(path, body=None):
    req = urllib.request.Request(f"{BASE}/{path}", data=None if body is None else json.dumps(body).encode(),
                                 headers={"x-goog-api-key": api_key(), "Content-Type": "application/json"},
                                 method="GET" if body is None else "POST")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=180).read())
    except urllib.error.HTTPError as e:
        # the error body never contains the key; show it so model/permission problems are visible
        raise SystemExit(f"HTTP {e.code} from {BASE}/{path.split('?')[0]}: {e.read().decode()[:400]}")


def render_page(pdf):
    png = X.CACHE / f"page{X.PAGE}.png"
    if not png.exists():
        subprocess.run(["pdftoppm", "-r", "200", "-png", "-singlefile", "-f", str(X.PAGE), "-l", str(X.PAGE),
                        str(pdf), str(png.with_suffix(""))], check=True)
    return png


def transcribe(model, png):
    body = {"contents": [{"parts": [{"text": PROMPT},
                                    {"inline_data": {"mime_type": "image/png",
                                                     "data": base64.b64encode(png.read_bytes()).decode()}}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                                 "responseSchema": SCHEMA}}
    r = call(f"models/{model}:generateContent", body)
    text = r["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)["rows"]


def compare(reference, rows):
    ref = X.PRINTED  # cells exactly as printed in the text layer
    mismatches = []
    for i in range(max(len(ref), len(rows))):
        a = ref[i] if i < len(ref) else ["<missing>"] * 5
        b = rows[i] if i < len(rows) else ["<missing>"] * 5
        for j in range(5):
            aj, bj = a[j] if j < len(a) else "<missing>", b[j] if j < len(b) else "<missing>"
            if aj.strip() != str(bj).strip():
                mismatches.append((i, X.COLUMNS[j], aj, bj))
    return mismatches


def main():
    if "--list-models" in sys.argv:
        for m in call("models?pageSize=200").get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                print(m["name"].split("/", 1)[1], "-", m.get("displayName", ""))
        return 0
    models = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not models:
        raise SystemExit(__doc__)
    pdf, sha = X.fetch_pdf()
    reference = X.extract_rows(pdf)
    png = render_page(pdf)
    report = {"pdf_sha256": sha, "page": X.PAGE, "reference": "PDF text layer", "models": {}}
    all_exact = True
    for model in models:
        rows = transcribe(model, png)
        mm = compare(reference, rows)
        cells = 30 * 5
        print(f"{model}: {cells - len(mm)}/{cells} cells identical to the text layer")
        for i, col, a, b in mm[:20]:
            print(f"    row P={i}: {col}: text layer {a!r}  vs  {model} {b!r}")
        report["models"][model] = {"rows": rows, "mismatches": [list(m) for m in mm]}
        all_exact &= not mm
    out = X.CACHE / "gemini_transcriptions.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nwrote {out}")
    print("ALL MODELS EXACT" if all_exact else "MISMATCHES FOUND (see above): do not trust unchecked "
          "transcriptions from these models")
    return 0 if all_exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
