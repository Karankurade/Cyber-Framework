import hashlib


def get_image_hash(content):

    return hashlib.sha256(
        content.encode()
    ).hexdigest()
