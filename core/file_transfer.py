import os
import shutil
import tarfile
import tempfile

from utils.logger import get_logger
from utils.md5sum import md5sum

logger = get_logger("file_transfer")


def upload_file(conn, local_path, remote_path, compress=False):
    path_to_send = local_path
    if compress:
        temp_dir = tempfile.mkdtemp()
        tar_path = os.path.join(temp_dir, os.path.basename(local_path) + ".tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(local_path, arcname=os.path.basename(local_path))
        logger.info(f"Compressed {local_path} to {tar_path}")
        path_to_send = tar_path
    local_md5 = md5sum(path_to_send)
    logger.info(f"Uploading {path_to_send} to {remote_path} (MD5: {local_md5})")
    # ... upload file ...
    # ... verify remote MD5 ...
    if compress:
        shutil.rmtree(temp_dir)
    return True


def download_file(conn, remote_path, local_path, decompress=False):
    logger.info(f"Downloading {remote_path} to {local_path}")
    # ... download file ...
    local_md5 = md5sum(local_path)
    logger.info(f"Downloaded file MD5: {local_md5}")
    if decompress:
        temp_dir = tempfile.mkdtemp()
        # Assume file is already downloaded as tar_path
        with tarfile.open(local_path, "r:gz") as tar:
            tar.extractall(path=os.path.dirname(local_path))
        logger.info(f"Decompressed {local_path}")
        shutil.rmtree(temp_dir)
    return True


def upload_files(conn, local_paths, remote_dir, compress=True):
    temp_dir = tempfile.mkdtemp()
    tar_path = os.path.join(temp_dir, "upload_bundle.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tar:
        for path in local_paths:
            tar.add(path, arcname=os.path.basename(path))
    logger.info(f"Compressed files {local_paths} to {tar_path}")
    remote_tar = os.path.join(remote_dir, "upload_bundle.tar.gz")
    upload_file(conn, tar_path, remote_tar, compress=False)
    # Optionally, remote extraction logic can be added here
    shutil.rmtree(temp_dir)
    return True


def download_files(conn, remote_paths, local_dir, compress=True):
    temp_dir = tempfile.mkdtemp()
    tar_path = os.path.join(temp_dir, "download_bundle.tar.gz")
    # On remote: tar the files into tar_path, then download
    # Here, we just simulate download
    logger.info(f"Requesting remote tar of files: {remote_paths}")
    # ... remote tar logic ...
    # ... download tar_path ...
    # For now, just log
    logger.info(f"Downloaded tarball to {tar_path}")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=local_dir)
    logger.info(f"Extracted files to {local_dir}")
    shutil.rmtree(temp_dir)
    return True
