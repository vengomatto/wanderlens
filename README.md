# Wanderlens

Learn a travel **Taste Profile** from a personal **Photo Archive** and recommend
new **Destinations**. Single-user today, built to become a portable open-source
app later.

## What it does

1. **Ingest** photos from a local folder (EXIF timestamp, GPS, dimensions).
2. **Profile** them: group photos into trips (time + GPS), resolve each trip to a
   country/city offline, embed every photo locally with CLIP, and tag a sample
   with a hosted vision model.
3. **Recommend** new destinations: embed candidate Destinations, rank them
   against your taste (excluding where you've already been), and explain each
   using your own photos.
4. **Evaluate** by holding out a visited place and checking whether it resurfaces.

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev,embeddings]'
```

The CLIP ONNX model is downloaded automatically on first use into
`data/models/`. Offline place data goes in `data/catalog/`:

```bash
mkdir -p data/catalog
curl -sL https://download.geonames.org/export/dump/cities500.zip -o /tmp/c.zip
python3 -c "import zipfile; zipfile.ZipFile('/tmp/c.zip').extractall('data/catalog')"
curl -sL https://download.geonames.org/export/dump/countryInfo.txt -o data/catalog/countryInfo.txt
```

## Use

```bash
# read photos and build the taste profile (add --tag to also run the VLM)
.venv/bin/python -m wanderlens ingest [--tag]

.venv/bin/python -m wanderlens profile show
.venv/bin/python -m wanderlens recommend --count 5
.venv/bin/python -m wanderlens eval [--holdout Malta]
```

`--tag` sends a small sample of photos (~3 per trip) to the configured vision
model. Without it, subject tags are skipped; geography and aesthetics are still
computed locally.

## Architecture

Ports and adapters. The `core/` never imports a photo manager or a model runtime:

```
wanderlens/
  core/       taste + recommendation, ports, vocabulary (no external imports)
  sources/    Photo Source adapters (local folder; Immich deferred)
  catalog/    place data (GeoNames/Wikidata), normalization, offline cache
  models/     the only place that imports onnxruntime/tokenizers or calls a VLM
  pipeline/   ingest, profile, recommend, evaluate
  cli/        argparse entry point
```

Data (`data/`) is git-ignored: photos, the SQLite database, model files, catalog.

## Testing

```bash
.venv/bin/python -m pytest -q
bash scripts/smoke.sh   # end-to-end over data/photos
```

## Status & limitations

- v1 is single-user; every persisted row carries a `user` id for the future
  multi-user/open-source app.
- Destination text comes from GeoNames names only, which is a weak matching
  signal — enrich with Wikidata descriptions before trusting ranking quality.
  See `docs/ROADMAP.md` and `openspec/changes/wanderlens-v1/`.
