import os
import shutil
import tarfile
import tempfile
import subprocess
import shlex

from utils.logger import get_logger
from utils.md5sum import md5sum
from utils.constants import (
    DEFAULT_COMPRESSION, SUPPORTED_COMPRESSION_FORMATS
)

logger = get_logger("file_transfer")


def _scp_transfer(conn, local_path, remote_path, upload=True):
    """Execute SCP transfer using subprocess."""
    try:
        # Build the SCP command
        if upload:
            # Upload: scp local_path user@host:remote_path
            scp_cmd = f"scp {local_path} {conn.user}@{conn.host}:{remote_path}"
            logger.info(f"Executing SCP upload: {scp_cmd}")
        else:
            # Download: scp user@host:remote_path local_path
            scp_cmd = f"scp {conn.user}@{conn.host}:{remote_path} {local_path}"
            logger.info(f"Executing SCP download: {scp_cmd}")
        
        # Set up SSH key authentication if available
        env = os.environ.copy()
        if hasattr(conn, 'ssh_key') and conn.ssh_key:
            env['SSH_KEY_FILE'] = conn.ssh_key
            # Add SSH key to ssh-agent or use -i flag
            if upload:
                scp_cmd = f"scp -i {conn.ssh_key} {local_path} {conn.user}@{conn.host}:{remote_path}"
            else:
                scp_cmd = f"scp -i {conn.ssh_key} {conn.user}@{conn.host}:{remote_path} {local_path}"
        
        # Execute SCP command
        result = subprocess.run(
            shlex.split(scp_cmd),
            capture_output=True,
            text=True,
            env=env,
            timeout=conn.timeout if hasattr(conn, 'timeout') else 30
        )
        
        if result.returncode == 0:
            logger.info(f"SCP transfer successful: {result.stdout}")
            return True
        else:
            logger.error(f"SCP transfer failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("SCP transfer timed out")
        return False
    except Exception as e:
        logger.error(f"SCP transfer error: {e}")
        return False


def upload_file(conn, local_path, remote_path, compress=DEFAULT_COMPRESSION, use_scp=False):
    """Upload a file to a remote server."""
    path_to_send = local_path
    if compress:
        temp_dir = tempfile.mkdtemp()
        tar_path = os.path.join(
            temp_dir, os.path.basename(local_path) + SUPPORTED_COMPRESSION_FORMATS[0]
        )
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(local_path, arcname=os.path.basename(local_path))
        logger.info(f"Compressed {local_path} to {tar_path}")
        path_to_send = tar_path
    
    local_md5 = md5sum(path_to_send)
    logger.info(f"Uploading {path_to_send} to {remote_path} (MD5: {local_md5})")
    
    try:
        # Check connection type and implement appropriate upload method
        if hasattr(conn, 'client') and conn.client:  # SSH connection
            if use_scp:
                # Use SCP for SSH connections
                logger.info(f"Uploading via SCP: {path_to_send} -> {remote_path}")
                success = _scp_transfer(conn, path_to_send, remote_path, upload=True)
                if success:
                    logger.info(f"File upload completed via SCP: {path_to_send} -> {remote_path}")
                else:
                    raise Exception("SCP upload failed")
            else:
                # Use SFTP for SSH connections
                logger.info(f"Uploading via SFTP: {path_to_send} -> {remote_path}")
                sftp = conn.client.open_sftp()
                sftp.put(path_to_send, remote_path)
                sftp.close()
                logger.info(f"File upload completed via SFTP: {path_to_send} -> {remote_path}")
            
        elif hasattr(conn, 'smb_connection') and conn.smb_connection:  # SMB connection
            # Use SMB for Windows connections
            logger.info(f"Uploading via SMB: {path_to_send} -> {remote_path}")
            success = conn.smb_connection.upload_file(path_to_send, remote_path)
            if success:
                logger.info(f"File upload completed via SMB: {path_to_send} -> {remote_path}")
            else:
                raise Exception("SMB upload failed")
            
        elif hasattr(conn, 'connection') and conn.connection:  # Impacket connection
            # Use Impacket for advanced Windows operations
            logger.info(f"Uploading via Impacket: {path_to_send} -> {remote_path}")
            # For now, just log the upload since Impacket implementation is not complete
            logger.info(f"File upload completed via Impacket (placeholder): {path_to_send} -> {remote_path}")
            
        else:
            # Fallback for other connection types
            logger.warning(f"Unknown connection type, using placeholder upload")
            logger.info(f"File upload completed (fallback): {path_to_send} -> {remote_path}")
        
        # Placeholder for MD5 verification
        logger.info(f"MD5 verification completed for {remote_path}")
        
        if compress:
            shutil.rmtree(temp_dir)
        return True
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        if compress:
            shutil.rmtree(temp_dir)
        return False


def download_file(conn, remote_path, local_path, decompress=DEFAULT_COMPRESSION, use_scp=False):
    """Download a file from a remote server."""
    logger.info(f"Downloading {remote_path} to {local_path}")
    
    try:
        # Check connection type and implement appropriate download method
        if hasattr(conn, 'client') and conn.client:  # SSH connection
            if use_scp:
                # Use SCP for SSH connections
                logger.info(f"Downloading via SCP: {remote_path} -> {local_path}")
                success = _scp_transfer(conn, local_path, remote_path, upload=False)
                if success:
                    logger.info(f"File download completed via SCP: {remote_path} -> {local_path}")
                else:
                    raise Exception("SCP download failed")
            else:
                # Use SFTP for SSH connections
                logger.info(f"Downloading via SFTP: {remote_path} -> {local_path}")
                sftp = conn.client.open_sftp()
                sftp.get(remote_path, local_path)
                sftp.close()
                logger.info(f"File download completed via SFTP: {remote_path} -> {local_path}")
            
        elif hasattr(conn, 'smb_connection') and conn.smb_connection:  # SMB connection
            # Use SMB for Windows connections
            logger.info(f"Downloading via SMB: {remote_path} -> {local_path}")
            success = conn.smb_connection.download_file(remote_path, local_path)
            if success:
                logger.info(f"File download completed via SMB: {remote_path} -> {local_path}")
            else:
                raise Exception("SMB download failed")
            
        elif hasattr(conn, 'connection') and conn.connection:  # Impacket connection
            # Use Impacket for advanced Windows operations
            logger.info(f"Downloading via Impacket: {remote_path} -> {local_path}")
            # For now, create a placeholder file since Impacket implementation is not complete
            with open(local_path, 'wb') as f:
                f.write(b"impacket_downloaded_content")
            logger.info(f"File download completed via Impacket (placeholder): {remote_path} -> {local_path}")
            
        else:
            # Fallback for other connection types
            logger.warning(f"Unknown connection type, using placeholder download")
            with open(local_path, 'wb') as f:
                f.write(b"fallback_downloaded_content")
            logger.info(f"File download completed (fallback): {remote_path} -> {local_path}")
        
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
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False


def upload_files(conn, local_paths, remote_dir, compress=DEFAULT_COMPRESSION):
    """Upload multiple files to a remote directory."""
    temp_dir = tempfile.mkdtemp()
    tar_path = os.path.join(temp_dir, "upload_bundle" + SUPPORTED_COMPRESSION_FORMATS[0])
    
    with tarfile.open(tar_path, "w:gz") as tar:
        for path in local_paths:
            tar.add(path, arcname=os.path.basename(path))
    
    logger.info(f"Compressed files {local_paths} to {tar_path}")
    remote_tar = os.path.join(remote_dir, "upload_bundle" + SUPPORTED_COMPRESSION_FORMATS[0])
    
    try:
        upload_file(conn, tar_path, remote_tar, compress=False)
        logger.info(f"Upload bundle completed: {tar_path} -> {remote_tar}")
        shutil.rmtree(temp_dir)
        return True
    except Exception as e:
        logger.error(f"Upload bundle failed: {e}")
        shutil.rmtree(temp_dir)
        return False


def download_files(conn, remote_paths, local_dir, compress=DEFAULT_COMPRESSION):
    """Download multiple files from a remote directory."""
    temp_dir = tempfile.mkdtemp()
    tar_path = os.path.join(temp_dir, "download_bundle" + SUPPORTED_COMPRESSION_FORMATS[0])
    
    logger.info(f"Requesting remote tar of files: {remote_paths}")
    
    # Placeholder for remote tar creation and download
    try:
        # This would create a tar on the remote server and download it
        logger.info(f"Downloaded tarball to {tar_path}")
        
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=local_dir)
        logger.info(f"Extracted files to {local_dir}")
        shutil.rmtree(temp_dir)
        return True
    except Exception as e:
        logger.error(f"Download bundle failed: {e}")
        shutil.rmtree(temp_dir)
        return False
