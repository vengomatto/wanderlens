from io import BytesIO

import piexif
from PIL import Image

from wanderlens.models.vision import MAX_IMAGE_PX, prepare_image


def test_prepare_image_strips_exif_and_downscales(tmp_path):
    path = tmp_path / "big.jpg"
    exif = {
        "0th": {},
        "Exif": {},
        "GPS": {
            piexif.GPSIFD.GPSLatitudeRef: b"N",
            piexif.GPSIFD.GPSLatitude: ((44, 1), (10, 1), (0, 1)),
            piexif.GPSIFD.GPSLongitudeRef: b"E",
            piexif.GPSIFD.GPSLongitude: ((9, 1), (34, 1), (0, 1)),
        },
        "1st": {},
        "thumbnail": None,
    }
    Image.new("RGB", (4000, 3000), (10, 20, 30)).save(path, exif=piexif.dump(exif))

    data = prepare_image(str(path))

    assert len(data) < path.stat().st_size
    with Image.open(BytesIO(data)) as image:
        assert max(image.size) <= MAX_IMAGE_PX
        assert not image.getexif()
