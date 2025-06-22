"""
State persistence system for HAI.

This module provides functionality to save and load the current state of all objects,
allowing operations to be resumed from another machine or after system restarts.
"""

import json
import pickle
import gzip
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from utils.constants import (
    STATE_DIR, STATE_VERSION, STATE_BACKUP_COUNT, TIMESTAMP_FORMAT, BACKUP_RETENTION_DAYS,
    STATE_FILE_EXTENSION
)


class StateFormat(Enum):
    """Supported state file formats."""
    JSON = "json"
    PICKLE = "pickle"
    COMPRESSED_JSON = "json.gz"
    COMPRESSED_PICKLE = "pickle.gz"


@dataclass
class StateMetadata:
    """Metadata for state files."""
    version: str
    created_at: str
    last_modified: str
    checksum: str
    format: str
    compression: bool
    encrypted: bool
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class OperationState:
    """State of a single operation."""
    operation_id: str
    operation_type: str
    servers: List[str]  # List of server hostnames
    successful_servers: List[str]
    failed_servers: List[str]
    in_progress_servers: List[str]
    start_time: str
    last_update: str
    status: str  # "running", "completed", "failed", "paused"
    results: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SessionState:
    """State of a user session."""
    session_id: str
    user: str
    start_time: str
    last_activity: str
    active_operations: List[str]
    completed_operations: List[str]
    server_cache: Dict[str, Any]
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}


@dataclass
class SystemState:
    """Complete system state."""
    metadata: StateMetadata
    sessions: Dict[str, SessionState]
    operations: Dict[str, OperationState]
    server_inventory: Dict[str, Any]
    configuration: Dict[str, Any]
    statistics: Dict[str, Any]
    cache: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.cache is None:
            self.cache = {}


class StateManager:
    """Manages state persistence and recovery."""
    
    def __init__(self, state_dir: Optional[str] = None):
        """
        Initialize state manager.
        
        Args:
            state_dir: Directory to store state files (defaults to state/)
        """
        self.state_dir = Path(state_dir) if state_dir else Path(STATE_DIR)
        self.state_dir.mkdir(exist_ok=True)
        
        # Current state
        self.current_state = None
        self.is_modified = False
    
    def _generate_checksum(self, data: bytes) -> str:
        """Generate SHA-256 checksum for data."""
        return hashlib.sha256(data).hexdigest()
    
    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip."""
        return gzip.compress(data)
    
    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data using gzip."""
        return gzip.decompress(data)
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data (placeholder for future implementation)."""
        # For now, just return the data as-is
        # In production, implement proper encryption
        return data
    
    def _decrypt_data(self, data: bytes) -> bytes:
        """Decrypt data (placeholder for future implementation)."""
        # For now, just return the data as-is
        # In production, implement proper decryption
        return data
    
    def _serialize_state(self, state: SystemState, format: StateFormat) -> bytes:
        """Serialize state to bytes."""
        if format == StateFormat.JSON:
            data = json.dumps(asdict(state), indent=2, default=str).encode('utf-8')
        elif format == StateFormat.PICKLE:
            data = pickle.dumps(state)
        elif format == StateFormat.COMPRESSED_JSON:
            data = json.dumps(asdict(state), indent=2, default=str).encode('utf-8')
            data = self._compress_data(data)
        elif format == StateFormat.COMPRESSED_PICKLE:
            data = pickle.dumps(state)
            data = self._compress_data(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return data
    
    def _deserialize_state(self, data: bytes, format: StateFormat) -> SystemState:
        """Deserialize state from bytes."""
        if format == StateFormat.COMPRESSED_JSON:
            data = self._decompress_data(data)
            format = StateFormat.JSON
        elif format == StateFormat.COMPRESSED_PICKLE:
            data = self._decompress_data(data)
            format = StateFormat.PICKLE
        
        if format == StateFormat.JSON:
            state_dict = json.loads(data.decode('utf-8'))
            return SystemState(**state_dict)
        elif format == StateFormat.PICKLE:
            return pickle.loads(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _detect_format(self, file_path: Path) -> StateFormat:
        """Detect the format of a state file."""
        if file_path.suffix == '.gz':
            # Check the original extension
            base_name = file_path.stem
            if base_name.endswith('.json'):
                return StateFormat.COMPRESSED_JSON
            elif base_name.endswith('.pickle'):
                return StateFormat.COMPRESSED_PICKLE
        elif file_path.suffix == '.json':
            return StateFormat.JSON
        elif file_path.suffix == '.pickle':
            return StateFormat.PICKLE
        
        # Default to JSON
        return StateFormat.JSON
    
    def create_backup(self, backup_name: str = None) -> Path:
        """Create a backup of the current state file."""
        if not self.state_dir.exists():
            self.logger.log_warning("No state directory to backup")
            return None
        
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        backup_name = backup_name or f"backup_{timestamp}"
        backup_file = self.state_dir / f"{backup_name}{STATE_FILE_EXTENSION}"
        
        try:
            shutil.copy2(self.state_dir, backup_file)
            self.logger.log_info(f"Backup created: {backup_file}")
            return backup_file
        except Exception as e:
            self.logger.log_error(f"Failed to create backup: {e}")
            return None
    
    def cleanup_old_backups(self, max_age_days: int = None):
        """Clean up old backup files."""
        max_age_days = max_age_days or BACKUP_RETENTION_DAYS
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        backup_pattern = f"backup_*{STATE_FILE_EXTENSION}"
        backup_files = list(self.state_dir.glob(backup_pattern))
        
        for backup_file in backup_files:
            try:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_time:
                    backup_file.unlink()
                    self.logger.log_info(f"Removed old backup: {backup_file}")
            except Exception as e:
                self.logger.log_error(f"Failed to remove backup {backup_file}: {e}")
    
    def save_state(self, state_name: str, data: Dict[str, Any], 
                   backup: bool = True, metadata: Dict[str, Any] = None) -> str:
        """
        Save application state to file.
        
        Args:
            state_name: Name of the state file
            data: Data to save
            backup: Whether to create backup
            metadata: Additional metadata to save
            
        Returns:
            Path to saved state file
        """
        # Prepare state data
        state_data = {
            "data": data,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Create filename
        filename = f"{state_name}{STATE_FILE_EXTENSION}"
        filepath = self.state_dir / filename
        
        # Save state
        with open(filepath, 'w') as f:
            json.dump(state_data, f, indent=2, default=str)
        
        # Create backup if requested
        if backup:
            self._create_backup(filepath)
        
        return str(filepath)
    
    def load_state(self, state_name: str, fallback: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load application state from file.
        
        Args:
            state_name: Name of the state file
            fallback: Fallback data if file doesn't exist
            
        Returns:
            Loaded state data
        """
        filename = f"{state_name}{STATE_FILE_EXTENSION}"
        filepath = self.state_dir / filename
        
        if not filepath.exists():
            if fallback is not None:
                return fallback
            raise FileNotFoundError(f"State file not found: {filepath}")
        
        try:
            with open(filepath, 'r') as f:
                state_data = json.load(f)
            
            return state_data.get("data", {})
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid state file format: {e}")
    
    def create_new_state(self, description: str = "") -> SystemState:
        """Create a new system state."""
        now = datetime.now().isoformat()
        
        metadata = StateMetadata(
            version=STATE_VERSION,
            created_at=now,
            last_modified=now,
            checksum="",
            format="json",
            compression=False,
            encrypted=False,
            description=description
        )
        
        state = SystemState(
            metadata=metadata,
            sessions={},
            operations={},
            server_inventory={},
            configuration={},
            statistics={},
            cache={}
        )
        
        self.current_state = state
        self.is_modified = True
        
        return state
    
    def update_operation_state(self, operation_id: str, operation_type: str,
                              servers: List[str], successful: List[str] = None,
                              failed: List[str] = None, in_progress: List[str] = None,
                              results: Dict[str, Any] = None, status: str = "running"):
        """Update the state of an operation."""
        if not self.current_state:
            self.current_state = self.create_new_state()
        
        now = datetime.now().isoformat()
        
        if operation_id not in self.current_state.operations:
            # Create new operation state
            operation_state = OperationState(
                operation_id=operation_id,
                operation_type=operation_type,
                servers=servers,
                successful_servers=successful or [],
                failed_servers=failed or [],
                in_progress_servers=in_progress or servers,
                start_time=now,
                last_update=now,
                status=status,
                results=results or {}
            )
        else:
            # Update existing operation state
            operation_state = self.current_state.operations[operation_id]
            operation_state.last_update = now
            operation_state.status = status
            
            if successful is not None:
                operation_state.successful_servers = successful
            if failed is not None:
                operation_state.failed_servers = failed
            if in_progress is not None:
                operation_state.in_progress_servers = in_progress
            if results is not None:
                operation_state.results.update(results)
        
        self.current_state.operations[operation_id] = operation_state
        self.is_modified = True
        
        self.logger.log_info(f"Operation state updated: {operation_id}")
    
    def get_operation_state(self, operation_id: str) -> Optional[OperationState]:
        """Get the state of an operation."""
        if not self.current_state:
            return None
        
        return self.current_state.operations.get(operation_id)
    
    def get_running_operations(self) -> List[OperationState]:
        """Get all running operations."""
        if not self.current_state:
            return []
        
        return [
            op for op in self.current_state.operations.values()
            if op.status == "running"
        ]
    
    def get_completed_operations(self) -> List[OperationState]:
        """Get all completed operations."""
        if not self.current_state:
            return []
        
        return [
            op for op in self.current_state.operations.values()
            if op.status == "completed"
        ]
    
    def save_session_state(self, session_id: str, user: str, 
                          active_operations: List[str] = None,
                          server_cache: Dict[str, Any] = None,
                          preferences: Dict[str, Any] = None):
        """Save session state."""
        if not self.current_state:
            self.current_state = self.create_new_state()
        
        now = datetime.now().isoformat()
        
        if session_id not in self.current_state.sessions:
            # Create new session state
            session_state = SessionState(
                session_id=session_id,
                user=user,
                start_time=now,
                last_activity=now,
                active_operations=active_operations or [],
                completed_operations=[],
                server_cache=server_cache or {},
                preferences=preferences or {}
            )
        else:
            # Update existing session state
            session_state = self.current_state.sessions[session_id]
            session_state.last_activity = now
            
            if active_operations is not None:
                session_state.active_operations = active_operations
            if server_cache is not None:
                session_state.server_cache.update(server_cache)
            if preferences is not None:
                session_state.preferences.update(preferences)
        
        self.current_state.sessions[session_id] = session_state
        self.is_modified = True
        
        self.logger.log_info(f"Session state saved: {session_id}")
    
    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Get session state."""
        if not self.current_state:
            return None
        
        return self.current_state.sessions.get(session_id)
    
    def update_server_inventory(self, inventory: Dict[str, Any]):
        """Update server inventory in state."""
        if not self.current_state:
            self.current_state = self.create_new_state()
        
        self.current_state.server_inventory = inventory
        self.is_modified = True
        
        self.logger.log_info("Server inventory updated")
    
    def update_configuration(self, config: Dict[str, Any]):
        """Update configuration in state."""
        if not self.current_state:
            self.current_state = self.create_new_state()
        
        self.current_state.configuration = config
        self.is_modified = True
        
        self.logger.log_info("Configuration updated")
    
    def update_statistics(self, stats: Dict[str, Any]):
        """Update statistics in state."""
        if not self.current_state:
            self.current_state = self.create_new_state()
        
        self.current_state.statistics = stats
        self.is_modified = True
        
        self.logger.log_info("Statistics updated")
    
    def auto_save(self):
        """Automatically save state if modified."""
        if self.is_modified and self.current_state:
            self.save_state(self.current_state)
    
    def export_state(self, state_name: str, export_path: str) -> str:
        """
        Export a state file to a different location.
        
        Args:
            state_name: Name of the state file
            export_path: Path to export to
            
        Returns:
            Path to exported file
        """
        filename = f"{state_name}{STATE_FILE_EXTENSION}"
        filepath = self.state_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"State file not found: {filepath}")
        
        export_filepath = Path(export_path)
        shutil.copy2(filepath, export_filepath)
        
        return str(export_filepath)
    
    def import_state(self, import_path: str, state_name: str = None) -> str:
        """
        Import a state file from a different location.
        
        Args:
            import_path: Path to import from
            state_name: Name for the imported state (defaults to filename)
            
        Returns:
            Name of the imported state
        """
        import_filepath = Path(import_path)
        
        if not import_filepath.exists():
            raise FileNotFoundError(f"Import file not found: {import_filepath}")
        
        # Determine state name
        if state_name is None:
            state_name = import_filepath.stem
        
        # Copy to state directory
        filename = f"{state_name}{STATE_FILE_EXTENSION}"
        filepath = self.state_dir / filename
        
        shutil.copy2(import_filepath, filepath)
        
        return state_name
    
    def _create_backup(self, filepath: Path):
        """Create a backup of the state file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
        backup_path = self.state_dir / "backups" / backup_name
        
        # Create backup directory
        backup_path.parent.mkdir(exist_ok=True)
        
        # Copy file
        shutil.copy2(filepath, backup_path)
        
        # Clean old backups
        self._cleanup_old_backups(backup_path.parent)
    
    def _cleanup_old_backups(self, backup_dir: Path):
        """Remove old backup files, keeping only the most recent ones."""
        backup_files = list(backup_dir.glob("*.json"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Keep only the most recent backups
        for backup_file in backup_files[STATE_BACKUP_COUNT:]:
            backup_file.unlink()
    
    def get_state_info(self, state_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a state file.
        
        Args:
            state_name: Name of the state file
            
        Returns:
            State metadata or None if not found
        """
        filename = f"{state_name}{STATE_FILE_EXTENSION}"
        filepath = self.state_dir / filename
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r') as f:
                state_data = json.load(f)
            
            return {
                "filepath": str(filepath),
                "size": filepath.stat().st_size,
                "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                "metadata": state_data.get("metadata", {}),
                "timestamp": state_data.get("timestamp"),
                "version": state_data.get("version")
            }
        except (json.JSONDecodeError, KeyError):
            return None


# Global state manager instance
state_manager = StateManager()


def get_state_manager(state_dir: Optional[str] = None) -> StateManager:
    """Get the global state manager instance."""
    if state_dir:
        return StateManager(state_dir)
    return state_manager


def save_current_state(description: str = "") -> bool:
    """Save current state using global state manager."""
    state_manager = get_state_manager()
    if state_manager.current_state:
        return state_manager.save_state(state_manager.current_state)
    return False


def load_saved_state(state_name: str = None) -> Optional[SystemState]:
    """Load saved state using global state manager."""
    state_manager = get_state_manager()
    if state_name:
        return state_manager.load_state(state_name)
    else:
        # Try to load the most recent state
        state_files = list(state_manager.state_dir.glob(f"*{STATE_FILE_EXTENSION}"))
        if state_files:
            # Sort by modification time and get the most recent
            latest_state = max(state_files, key=lambda x: x.stat().st_mtime)
            state_name = latest_state.stem
            return state_manager.load_state(state_name)
        return None


def create_new_session(session_id: str, user: str) -> bool:
    """Create a new session."""
    state_manager = get_state_manager()
    state_manager.save_session_state(session_id, user)
    return True


def get_session_info(session_id: str) -> Optional[SessionState]:
    """Get session information."""
    return get_state_manager().get_session_state(session_id) 