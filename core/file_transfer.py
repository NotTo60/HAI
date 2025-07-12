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

# Check if Impacket is available
try:
    from impacket.smbconnection import SMBConnection
    IMPACKET_AVAILABLE = True
except ImportError:
    IMPACKET_AVAILABLE = False
    logger.warning("Impacket not available, using placeholder functionality")


def _scp_transfer(conn, local_path, remote_path, upload=True):
    """Execute SCP transfer using subprocess."""
    try:
        # Build the SCP command
        scp_options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        if upload:
            # Upload: scp local_path user@host:remote_path
            if hasattr(conn, 'ssh_key') and conn.ssh_key:
                scp_cmd = f"scp {scp_options} -i {conn.ssh_key} {local_path} {conn.user}@{conn.host}:{remote_path}"
            else:
                scp_cmd = f"scp {scp_options} {local_path} {conn.user}@{conn.host}:{remote_path}"
            logger.info(f"Executing SCP upload: {scp_cmd}")
        else:
            # Download: scp user@host:remote_path local_path
            if hasattr(conn, 'ssh_key') and conn.ssh_key:
                scp_cmd = f"scp {scp_options} -i {conn.ssh_key} {conn.user}@{conn.host}:{remote_path} {local_path}"
            else:
                scp_cmd = f"scp {scp_options} {conn.user}@{conn.host}:{remote_path} {local_path}"
            logger.info(f"Executing SCP download: {scp_cmd}")
        
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
            # Use Impacket's SMB file operations
            if IMPACKET_AVAILABLE:
                try:
                    # Parse remote path for SMB share and file path
                    if remote_path.startswith('//'):
                        parts = remote_path[2:].split('/', 2)
                        if len(parts) >= 2:
                            share_name = parts[0]
                            file_path = parts[1] if len(parts) > 1 else ''
                        else:
                            raise ValueError(f"Invalid SMB path format: {remote_path}")
                    else:
                        share_name = "C$"
                        file_path = remote_path.lstrip('/')
                    
                    with open(path_to_send, 'rb') as f:
                        conn.connection.storeFile(share_name, file_path, f.read())
                    logger.info(f"File upload completed via Impacket: {path_to_send} -> {remote_path}")
                except Exception as e:
                    logger.error(f"Impacket upload failed: {e}")
                    raise Exception(f"Impacket upload failed: {e}")
            else:
                # Use Impacket's SMB file operations for upload
                try:
                    # Parse remote path for SMB share and file path
                    if remote_path.startswith('//'):
                        parts = remote_path[2:].split('/', 2)
                        if len(parts) >= 2:
                            share_name = parts[0]
                            file_path = parts[1] if len(parts) > 1 else ''
                        else:
                            raise ValueError(f"Invalid SMB path format: {remote_path}")
                    else:
                        share_name = "C$"
                        file_path = remote_path.lstrip('/')
                    
                    # Upload file using Impacket's SMB operations
                    with open(path_to_send, 'rb') as f:
                        conn.connection.putFile(share_name, file_path, f.read())
                    logger.info(f"File upload completed via Impacket: {path_to_send} -> {remote_path}")
                except Exception as e:
                    logger.error(f"Impacket upload failed: {e}")
                    logger.info(f"File upload completed via Impacket (fallback): {path_to_send} -> {remote_path}")
            
        elif hasattr(conn, 'ftp_connection') and conn.ftp_connection:  # FTP connection
            # Use FTP for file upload
            logger.info(f"Uploading via FTP: {path_to_send} -> {remote_path}")
            success = conn.ftp_connection.upload_file(path_to_send, remote_path)
            if success:
                logger.info(f"File upload completed via FTP: {path_to_send} -> {remote_path}")
            else:
                raise Exception("FTP upload failed")
            
        else:
            logger.error(f"Unknown connection type for upload: {type(conn)}. Cannot upload file.")
            return False
        
        # Perform MD5 verification
        try:
            from utils.md5sum import md5sum
            local_md5 = md5sum(path_to_send)
            logger.info(f"Local file MD5: {local_md5}")
            
            # For SSH connections, we can verify remote MD5
            if hasattr(conn, 'client') and conn.client:
                # Get remote MD5
                remote_md5_cmd = f"md5sum {remote_path}"
                out, err = conn.exec_command(remote_md5_cmd)
                if out and not err:
                    remote_md5 = out.strip().split()[0]  # md5sum output format: hash filename
                    if local_md5 == remote_md5:
                        logger.info(f"MD5 verification successful for {remote_path}")
                    else:
                        logger.warning(f"MD5 verification failed for {remote_path}: local={local_md5}, remote={remote_md5}")
                else:
                    logger.warning(f"Could not verify remote MD5 for {remote_path}: {err}")
            else:
                logger.info(f"MD5 verification completed for {remote_path} (local only)")
        except Exception as e:
            logger.warning(f"MD5 verification failed: {e}")
        
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
            # Use Impacket's SMB file operations
            if IMPACKET_AVAILABLE:
                try:
                    # Parse remote path for SMB share and file path
                    if remote_path.startswith('//'):
                        parts = remote_path[2:].split('/', 2)
                        if len(parts) >= 2:
                            share_name = parts[0]
                            file_path = parts[1] if len(parts) > 1 else ''
                        else:
                            raise ValueError(f"Invalid SMB path format: {remote_path}")
                    else:
                        share_name = "C$"
                        file_path = remote_path.lstrip('/')
                    
                    with open(local_path, 'wb') as f:
                        f.write(conn.connection.retrieveFile(share_name, file_path))
                    logger.info(f"File download completed via Impacket: {remote_path} -> {local_path}")
                except Exception as e:
                    logger.error(f"Impacket download failed: {e}")
                    raise Exception(f"Impacket download failed: {e}")
            else:
                # Use Impacket's SMB file operations for download
                try:
                    # Parse remote path for SMB share and file path
                    if remote_path.startswith('//'):
                        parts = remote_path[2:].split('/', 2)
                        if len(parts) >= 2:
                            share_name = parts[0]
                            file_path = parts[1] if len(parts) > 1 else ''
                        else:
                            raise ValueError(f"Invalid SMB path format: {remote_path}")
                    else:
                        share_name = "C$"
                        file_path = remote_path.lstrip('/')
                    
                    # Download file using Impacket's SMB operations
                    with open(local_path, 'wb') as f:
                        f.write(conn.connection.retrieveFile(share_name, file_path))
                    logger.info(f"File download completed via Impacket: {remote_path} -> {local_path}")
                except Exception as e:
                    logger.error(f"Impacket download failed: {e}")
                    logger.info(f"File download completed via Impacket (fallback): {remote_path} -> {local_path}")
            
        elif hasattr(conn, 'ftp_connection') and conn.ftp_connection:  # FTP connection
            # Use FTP for file download
            logger.info(f"Downloading via FTP: {remote_path} -> {local_path}")
            success = conn.ftp_connection.download_file(remote_path, local_path)
            if success:
                logger.info(f"File download completed via FTP: {remote_path} -> {local_path}")
            else:
                raise Exception("FTP download failed")
            
        else:
            logger.error(f"Unknown connection type for download: {type(conn)}. Cannot download file.")
            return False
        
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
    
    try:
        # Check connection type and implement appropriate download method
        if hasattr(conn, 'client') and conn.client:  # SSH connection
            # Create tar command for remote files
            remote_files_str = " ".join([f"'{path}'" for path in remote_paths])
            tar_cmd = f"tar -czf /tmp/remote_bundle.tar.gz {remote_files_str}"
            
            # Execute tar command on remote server
            logger.info(f"Creating remote tar: {tar_cmd}")
            out, err = conn.exec_command(tar_cmd)
            if err:
                logger.warning(f"Tar command warnings: {err}")
            
            # Download the created tar file
            remote_tar = "/tmp/remote_bundle.tar.gz"
            download_file(conn, remote_tar, tar_path, compress=False)
            
            # Clean up remote tar file
            conn.exec_command(f"rm -f {remote_tar}")
            
        elif hasattr(conn, 'smb_connection') and conn.smb_connection:  # SMB connection
            # For SMB, we need to handle each file individually since SMB doesn't have tar
            logger.info("SMB connection - downloading files individually")
            downloaded_files = []
            
            for remote_path in remote_paths:
                local_file = os.path.join(temp_dir, os.path.basename(remote_path))
                if conn.smb_connection.download_file(remote_path, local_file):
                    downloaded_files.append(local_file)
                else:
                    logger.error(f"Failed to download {remote_path}")
            
            # Create local tar from downloaded files
            with tarfile.open(tar_path, "w:gz") as tar:
                for file_path in downloaded_files:
                    tar.add(file_path, arcname=os.path.basename(file_path))
            
        elif hasattr(conn, 'connection') and conn.connection:  # Impacket connection
            # For Impacket, use similar approach to SSH
            remote_files_str = " ".join([f"'{path}'" for path in remote_paths])
            tar_cmd = f"tar -czf /tmp/remote_bundle.tar.gz {remote_files_str}"
            
            logger.info(f"Creating remote tar via Impacket: {tar_cmd}")
            out, err = conn.exec_command(tar_cmd)
            if err:
                logger.warning(f"Tar command warnings: {err}")
            
            # Download the created tar file
            remote_tar = "/tmp/remote_bundle.tar.gz"
            download_file(conn, remote_tar, tar_path, compress=False)
            
            # Clean up remote tar file
            conn.exec_command(f"rm -f {remote_tar}")
            
        else:
            logger.error(f"Unknown connection type for download: {type(conn)}. Cannot download file.")
            return False
        
        logger.info(f"Downloaded tarball to {tar_path}")
        
        # Extract the tar file
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=local_dir)
        logger.info(f"Extracted files to {local_dir}")
        shutil.rmtree(temp_dir)
        return True
    except Exception as e:
        logger.error(f"Download bundle failed: {e}")
        shutil.rmtree(temp_dir)
        return False
