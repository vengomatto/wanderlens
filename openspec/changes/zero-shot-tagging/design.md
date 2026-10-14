# Design

## Context

See `proposal.md`. The hosted tagger (`models/vision.py:HostedVLM`) implements the
`VisionModel.describe(paths) -> list[str]` seam used by `pipeline/profile.py`;
tag results are cached by model + prompt version. `OnnxClipEmbedder` already
provides `embed_image` and `embed_text` locally.

## Decisions

### A local tagger behind the same seam
`models/tagging.py:ZeroShotTagger(embedder)` builds one text embedding per
vocabulary prompt on construction, and `describe(paths)` embeds each photo, takes
a scaled softmax over the prompt similarities, and returns the labels whose
probability clears a small threshold (top-k, capped). It exposes
`model = "clip-zero-shot"` and `prompt_version = "zeroshot-v1"`, so the existing
tag cache keys it separately from the hosted model, and `canonicalize` maps the
returned canonical labels trivially. Because it implements `describe`, the
pipeline is untouched.

### Prompts from the vocabulary
A `PROMPTS` map from each canonical attribute to a short phrase ("a photo of a
sandy beach"); any attribute without a bespoke phrase falls back to
`"a photo of {attribute.replace('_',' ')}"`.

### Opt-in hosted path
`ingest --tag` builds the local tagger with the CLIP embedder (reused for the
photo embeddings in the same run). `--vlm` (with a key) uses `HostedVLM` instead.
`config.tag_provider` (`clip` default) mirrors the choice for non-CLI callers.

## Risks / Trade-offs

- **CLIP scene accuracy on the long tail** is imperfect → the hosted path stays
  for that, and the prompt set can grow; the plan flags verifying against persona
  fixtures (A0 follow-up).
- **Every photo is embedded twice** (once for the profile, once by the tagger) →
  reuse the same embedder instance; the cost is a local matrix multiply.
