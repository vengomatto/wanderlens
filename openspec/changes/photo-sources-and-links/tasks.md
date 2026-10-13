# Tasks

## 1. More image sources

- [x] 1.1 Make Openverse a default media source and add `UnsplashMediaProvider` and `PexelsMediaProvider` behind the image-source port, enabled when their key is set; verify tests with injected fake sessions for both providers and a defaults test.
- [x] 1.2 Thread the source keys through config (`WANDERLENS_UNSPLASH_KEY`, `WANDERLENS_PEXELS_KEY`) and `build_media_chain(sources, keys)`, and pass them from the recommend pipeline; verify a test that keys enable the providers and absence disables them.

## 2. Photo links

- [x] 2.1 Put the outbound photo-search links on the recommendation card (`RecView.photo_links`); verify a `TestClient` render shows them.
- [x] 2.2 Move the links into a dedicated "More photos" section on the destination page, shown regardless of the case; verify a render shows the section.

## 3. Documentation and verification

- [x] 3.1 Update `README.md` for the default Openverse source, the keyed Unsplash/Pexels sources, and the photo links; verify the documented config works.
- [x] 3.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
