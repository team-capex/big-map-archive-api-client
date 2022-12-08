def test_upload():
    from big_map_archive_api.api import BMA

    bma = BMA()
    bma.upload_records("../tests/records")


def test_upload_publish():
    from big_map_archive_api.api import BMA

    bma = BMA()
    bma.upload_records("../tests//records")
    bma.publish()
