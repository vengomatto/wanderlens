import numpy as np

from wanderlens.core.vocabulary import canonicalize
from wanderlens.models.tagging import PROMPTS, ZeroShotTagger


class FakeEmbedder:
    def __init__(self):
        self.labels = list(PROMPTS)

    def embed_text(self, text):
        vector = np.zeros(len(self.labels), dtype=np.float32)
        for index, label in enumerate(self.labels):
            if PROMPTS[label] == text:
                vector[index] = 1.0
        return vector

    def embed_image(self, path):
        name = path.rsplit("/", 1)[-1].replace(".jpg", "")
        vector = np.zeros(len(self.labels), dtype=np.float32)
        if name in self.labels:
            vector[self.labels.index(name)] = 1.0
        return vector


def test_zero_shot_tagger_assigns_matching_attribute():
    tagger = ZeroShotTagger(FakeEmbedder())
    assert tagger.describe(["/x/beach.jpg"]) == ["beach"]


def test_zero_shot_tagger_has_distinct_cache_key():
    tagger = ZeroShotTagger(FakeEmbedder())
    assert tagger.model == "clip-zero-shot"
    assert tagger.prompt_version == "zeroshot-v1"


def test_returned_labels_canonicalize():
    tagger = ZeroShotTagger(FakeEmbedder())
    tags = tagger.describe(["/x/old_town.jpg"])
    assert "old_town" in tags
    assert "old_town" in canonicalize(tags[0])


def test_unreadable_image_is_skipped():
    class Boom(FakeEmbedder):
        def embed_image(self, path):
            raise RuntimeError("bad")

    assert ZeroShotTagger(Boom()).describe(["/x/beach.jpg"]) == []
