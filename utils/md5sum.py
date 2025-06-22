import hashlib
from utils.constants import DEFAULT_CHUNK_SIZE

def md5sum(filename):
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(DEFAULT_CHUNK_SIZE), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_md5(file_path, expected_md5):
    """Verify MD5 hash of a file against expected value."""
    actual_md5 = md5sum(file_path)
    return actual_md5.lower() == expected_md5.lower()
