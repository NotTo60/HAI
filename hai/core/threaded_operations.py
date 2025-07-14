import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, List, Optional
from tqdm import tqdm
import os

from .server_schema import ServerEntry
from ..utils.constants import DEFAULT_MAX_WORKERS, DEFAULT_TIMEOUT, PROGRESS_BAR_WIDTH
from ..utils.enhanced_logger import get_enhanced_logger, get_server_logger

logger = get_enhanced_logger("threaded_operations")


@dataclass
class OperationResult:
    """Result of a single operation on a server"""
    server: ServerEntry
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: Optional[float] = None


@dataclass
class BatchResult:
    """Results of a batch operation across multiple servers"""
    successful: List[OperationResult]
    failed: List[OperationResult]
    total_servers: int
    total_successful: int
    total_failed: int
    execution_time: float
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_servers == 0:
            return 0.0
        return (self.total_successful / self.total_servers) * 100
    
    def get_successful_servers(self) -> List[ServerEntry]:
        """Get list of servers that succeeded"""
        return [result.server for result in self.successful]
    
    def get_failed_servers(self) -> List[ServerEntry]:
        """Get list of servers that failed"""
        return [result.server for result in self.failed]


class ThreadedOperations:
    """Threaded operations manager with progress tracking and statistics"""
    
    def __init__(self, max_workers: int = DEFAULT_MAX_WORKERS):
        self.max_workers = max_workers
        self.logger = get_enhanced_logger("threaded_operations")
    
    def run_command_on_servers(
        self, 
        servers: List[ServerEntry], 
        command: str,
        show_progress: bool = True,
        description: str = "Running command",
        save_state: bool = False,
        load_state: bool = False,
        timeout: int = DEFAULT_TIMEOUT
    ) -> BatchResult:
        """
        Run a command on multiple servers in parallel
        
        Args:
            servers: List of servers to run command on
            command: Command to execute
            show_progress: Whether to show progress bar
            description: Description for progress bar
            save_state: Whether to save state after operation
            load_state: Whether to load state before operation
            timeout: Timeout for the operation
            
        Returns:
            BatchResult with success/failure statistics
        """
        if load_state:
            self.logger.log_info("Loading previous state before operation...")
            # load_saved_state() # Removed as per edit hint
        self.logger.log_operation_start("run_command_on_servers", len(servers))
        result = self._run_operation_on_servers(
            servers=servers,
            operation=self._command_operation,
            operation_args=(command, timeout),
            show_progress=show_progress,
            description=description
        )
        self.logger.log_operation_complete("run_command_on_servers", {
            "total_servers": result.total_servers,
            "successful": result.total_successful,
            "failed": result.total_failed,
            "execution_time": result.execution_time
        })
        if save_state:
            self.logger.log_info("Saving state after operation...")
            # save_current_state(description=f"After run_command_on_servers: {description}") # Removed as per edit hint
            pass # Placeholder for future state saving
        return result
    
    def run_commands_on_servers(
        self, 
        servers: List[ServerEntry], 
        commands: List[str],
        show_progress: bool = True,
        description: str = "Running commands",
        timeout: int = DEFAULT_TIMEOUT
    ) -> BatchResult:
        """
        Run multiple commands on multiple servers in parallel
        
        Args:
            servers: List of servers to run commands on
            commands: List of commands to execute
            show_progress: Whether to show progress bar
            description: Description for progress bar
            timeout: Timeout for the operation
            
        Returns:
            BatchResult with success/failure statistics
        """
        return self._run_operation_on_servers(
            servers=servers,
            operation=self._commands_operation,
            operation_args=(commands, timeout),
            show_progress=show_progress,
            description=description
        )
    
    def upload_file_to_servers(
        self, 
        servers: List[ServerEntry], 
        local_path: str,
        remote_path: str,
        compress: bool = False,
        show_progress: bool = True,
        description: str = "Uploading files",
        timeout: int = DEFAULT_TIMEOUT
    ) -> BatchResult:
        """
        Upload a file to multiple servers in parallel
        
        Args:
            servers: List of servers to upload to
            local_path: Local file path
            remote_path: Remote file path
            compress: Whether to compress the file
            show_progress: Whether to show progress bar
            description: Description for progress bar
            timeout: Timeout for the operation
            
        Returns:
            BatchResult with success/failure statistics
        """
        return self._run_operation_on_servers(
            servers=servers,
            operation=self._upload_operation,
            operation_args=(local_path, remote_path, compress, timeout),
            show_progress=show_progress,
            description=description
        )
    
    def download_file_from_servers(
        self, 
        servers: List[ServerEntry], 
        remote_path: str,
        local_path: str,
        decompress: bool = False,
        show_progress: bool = True,
        description: str = "Downloading files",
        timeout: int = DEFAULT_TIMEOUT
    ) -> BatchResult:
        """
        Download a file from multiple servers in parallel
        
        Args:
            servers: List of servers to download from
            remote_path: Remote file path
            local_path: Local file path
            decompress: Whether to decompress the file
            show_progress: Whether to show progress bar
            description: Description for progress bar
            timeout: Timeout for the operation
            
        Returns:
            BatchResult with success/failure statistics
        """
        return self._run_operation_on_servers(
            servers=servers,
            operation=self._download_operation,
            operation_args=(remote_path, local_path, decompress, timeout),
            show_progress=show_progress,
            description=description
        )
    
    def custom_operation_on_servers(
        self, 
        servers: List[ServerEntry], 
        operation_func: Callable,
        operation_args: tuple = (),
        operation_kwargs: dict = None,
        show_progress: bool = True,
        description: str = "Running custom operation",
        timeout: int = DEFAULT_TIMEOUT
    ) -> BatchResult:
        """
        Run a custom operation on multiple servers in parallel
        
        Args:
            servers: List of servers to run operation on
            operation_func: Function to execute (should take connection as first arg)
            operation_args: Arguments to pass to operation function
            operation_kwargs: Keyword arguments to pass to operation function
            show_progress: Whether to show progress bar
            description: Description for progress bar
            timeout: Timeout for the operation
            
        Returns:
            BatchResult with success/failure statistics
        """
        if operation_kwargs is None:
            operation_kwargs = {}
        
        return self._run_operation_on_servers(
            servers=servers,
            operation=self._custom_operation,
            operation_args=(operation_func, operation_args, operation_kwargs, timeout),
            show_progress=show_progress,
            description=description
        )
    
    def _run_operation_on_servers(
        self,
        servers: List[ServerEntry],
        operation: Callable,
        operation_args: tuple,
        show_progress: bool = True,
        description: str = "Running operation"
    ) -> BatchResult:
        """Internal method to run operations on servers with threading"""
        import time
        start_time = time.time()
        
        successful_results = []
        failed_results = []
        
        # Create progress bar if requested
        pbar = None
        if show_progress:
            pbar = tqdm(
                total=len(servers),
                desc=description,
                unit="server",
                ncols=PROGRESS_BAR_WIDTH
            )
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_server = {
                    executor.submit(operation, server, *operation_args): server
                    for server in servers
                }
                
                # Process completed tasks
                for future in as_completed(future_to_server):
                    server = future_to_server[future]
                    try:
                        result = future.result()
                        successful_results.append(result)
                        if pbar:
                            pbar.set_postfix({
                                'Success': len(successful_results),
                                'Failed': len(failed_results)
                            })
                    except Exception as e:
                        failed_result = OperationResult(
                            server=server,
                            success=False,
                            result=None,
                            error=str(e)
                        )
                        failed_results.append(failed_result)
                        if pbar:
                            pbar.set_postfix({
                                'Success': len(successful_results),
                                'Failed': len(failed_results)
                            })
                    
                    if pbar:
                        pbar.update(1)
        
        finally:
            if pbar:
                pbar.close()
        
        execution_time = time.time() - start_time
        
        return BatchResult(
            successful=successful_results,
            failed=failed_results,
            total_servers=len(servers),
            total_successful=len(successful_results),
            total_failed=len(failed_results),
            execution_time=execution_time
        )
    
    def _command_operation(self, server: ServerEntry, command: str, timeout: int) -> OperationResult:
        """Execute a single command on a server"""
        import time
        from .connection_manager import connect_with_fallback
        from .command_runner import run_command
        start_time = time.time()
        server_logger = get_server_logger(server.hostname, server.ip)
        try:
            conn = connect_with_fallback(server)
            out, err = run_command(conn, command, timeout)
            conn.disconnect()
            execution_time = time.time() - start_time
            server_logger.log_command(command, output=out, error=err, execution_time=execution_time)
            return OperationResult(
                server=server,
                success=True,
                result={"output": out, "error": err},
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            server_logger.log_command(command, error=str(e), execution_time=execution_time)
            return OperationResult(
                server=server,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def _commands_operation(self, server: ServerEntry, commands: List[str], timeout: int) -> OperationResult:
        """Execute multiple commands on a server"""
        import time
        from .connection_manager import connect_with_fallback
        from .command_runner import run_commands
        
        start_time = time.time()
        
        try:
            conn = connect_with_fallback(server)
            results = run_commands(conn, commands, timeout)
            conn.disconnect()
            
            execution_time = time.time() - start_time
            
            return OperationResult(
                server=server,
                success=True,
                result={"results": results},
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            
            return OperationResult(
                server=server,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def _upload_operation(self, server: ServerEntry, local_path: str, remote_path: str, compress: bool, timeout: int) -> OperationResult:
        """Upload a file to a server"""
        import time
        from .connection_manager import connect_with_fallback
        from .file_transfer import upload_file
        start_time = time.time()
        server_logger = get_server_logger(server.hostname, server.ip)
        try:
            conn = connect_with_fallback(server)
            result = upload_file(conn, local_path, remote_path, compress, timeout)
            conn.disconnect()
            execution_time = time.time() - start_time
            file_size = None
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
            server_logger.log_file_transfer(
                operation="upload",
                local_path=local_path,
                remote_path=remote_path,
                status="SUCCESS",
                file_size=file_size,
                execution_time=execution_time
            )
            return OperationResult(
                server=server,
                success=True,
                result={"uploaded": result},
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            file_size = None
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
            server_logger.log_file_transfer(
                operation="upload",
                local_path=local_path,
                remote_path=remote_path,
                status="FAILED",
                file_size=file_size,
                execution_time=execution_time,
                error=str(e)
            )
            return OperationResult(
                server=server,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def _download_operation(self, server: ServerEntry, remote_path: str, local_path: str, decompress: bool, timeout: int) -> OperationResult:
        """Download a file from a server"""
        import time
        from .connection_manager import connect_with_fallback
        from .file_transfer import download_file
        start_time = time.time()
        server_logger = get_server_logger(server.hostname, server.ip)
        try:
            conn = connect_with_fallback(server)
            result = download_file(conn, remote_path, local_path, decompress, timeout)
            conn.disconnect()
            execution_time = time.time() - start_time
            file_size = None
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
            server_logger.log_file_transfer(
                operation="download",
                local_path=local_path,
                remote_path=remote_path,
                status="SUCCESS",
                file_size=file_size,
                execution_time=execution_time
            )
            return OperationResult(
                server=server,
                success=True,
                result={"downloaded": result},
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            file_size = None
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
            server_logger.log_file_transfer(
                operation="download",
                local_path=local_path,
                remote_path=remote_path,
                status="FAILED",
                file_size=file_size,
                execution_time=execution_time,
                error=str(e)
            )
            return OperationResult(
                server=server,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def _custom_operation(self, server: ServerEntry, operation_func: Callable, operation_args: tuple, operation_kwargs: dict, timeout: int) -> OperationResult:
        """Execute a custom operation on a server"""
        import time
        from .connection_manager import connect_with_fallback
        
        start_time = time.time()
        
        try:
            conn = connect_with_fallback(server)
            result = operation_func(conn, *operation_args, **operation_kwargs)
            conn.disconnect()
            
            execution_time = time.time() - start_time
            
            return OperationResult(
                server=server,
                success=True,
                result=result,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            
            return OperationResult(
                server=server,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )


# Convenience functions for easy usage
def run_command_on_servers(
    servers: List[ServerEntry], 
    command: str,
    max_workers: int = DEFAULT_MAX_WORKERS,
    show_progress: bool = True,
    description: str = "Running command",
    timeout: int = DEFAULT_TIMEOUT
) -> BatchResult:
    """Run a command on multiple servers with threading"""
    ops = ThreadedOperations(max_workers=max_workers)
    return ops.run_command_on_servers(servers, command, show_progress, description, False, True, timeout)


def run_commands_on_servers(
    servers: List[ServerEntry], 
    commands: List[str],
    max_workers: int = DEFAULT_MAX_WORKERS,
    show_progress: bool = True,
    description: str = "Running commands",
    timeout: int = DEFAULT_TIMEOUT
) -> BatchResult:
    """Run multiple commands on multiple servers with threading"""
    ops = ThreadedOperations(max_workers=max_workers)
    return ops.run_commands_on_servers(servers, commands, show_progress, description, timeout)


def upload_file_to_servers(
    servers: List[ServerEntry], 
    local_path: str,
    remote_path: str,
    compress: bool = False,
    max_workers: int = DEFAULT_MAX_WORKERS,
    show_progress: bool = True,
    description: str = "Uploading files",
    timeout: int = DEFAULT_TIMEOUT
) -> BatchResult:
    """Upload a file to multiple servers with threading"""
    ops = ThreadedOperations(max_workers=max_workers)
    return ops.upload_file_to_servers(servers, local_path, remote_path, compress, show_progress, description, timeout)


def download_file_from_servers(
    servers: List[ServerEntry], 
    remote_path: str,
    local_path: str,
    decompress: bool = False,
    max_workers: int = DEFAULT_MAX_WORKERS,
    show_progress: bool = True,
    description: str = "Downloading files",
    timeout: int = DEFAULT_TIMEOUT
) -> BatchResult:
    """Download a file from multiple servers with threading"""
    ops = ThreadedOperations(max_workers=max_workers)
    return ops.download_file_from_servers(servers, remote_path, local_path, decompress, show_progress, description, timeout)


def custom_operation_on_servers(
    servers: List[ServerEntry], 
    operation_func: Callable,
    operation_args: tuple = (),
    operation_kwargs: dict = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
    show_progress: bool = True,
    description: str = "Running custom operation",
    timeout: int = DEFAULT_TIMEOUT
) -> BatchResult:
    """Run a custom operation on multiple servers with threading"""
    ops = ThreadedOperations(max_workers=max_workers)
    return ops.custom_operation_on_servers(servers, operation_func, operation_args, operation_kwargs, show_progress, description, timeout) 