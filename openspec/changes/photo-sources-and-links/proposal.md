# Proposal

## Why

The whole photo story is legal but half-wired: external photo links (Getty,
Google, Commons) only appear on a destination page buried under the case, and the
only embedded sources are Wikimedia/Commons with Openverse opt-in. Galleries could
be richer and the link-outs should be visible where the choice happens.

## What Changes

- **Surface photo links.** Show the outbound photo-search links (Commons, Getty,
  Google Images) on the recommendation card too, and give them a dedicated
  **"More photos"** section on the destination page instead of a line under the
  case.
- **Richer embedded sources.** Enable **Openverse** by default, and add
  **Unsplash** and **Pexels** providers (free, commercial-use) enabled when their
  key is configured — all behind the existing image-source port and best-effort.
- No **BREAKING** changes; proprietary images are still never embedded.

## Capabilities

### Modified Capabilities
- `destination-media`: an Unsplash and a Pexels image source; Openverse enabled
  by default.
- `web-interface`: photo-search links on the recommendation card and a dedicated
  "More photos" section on the destination page.

## Impact

- `wanderlens/catalog/media.py`: Openverse default, `UnsplashMediaProvider`,
  `PexelsMediaProvider`, `build_media_chain(sources, keys)`.
- `wanderlens/config.py`: default `media_sources`, `unsplash_key`, `pexels_key`.
- `wanderlens/pipeline/recommend.py`: pass source keys to the media chain.
- `wanderlens/web/views.py` + templates: card photo links, dedicated section.
- New tests for the providers, the defaults, and the rendering.
