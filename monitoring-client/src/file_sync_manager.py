"""File synchronization manager for OTA file transfers."""

import os
import time
import threading
import requests
from pathlib import Path
from typing import List, Dict, Optional
from queue import Queue
from .logger import get_logger
from .config import Config, retrieve_client_id

logger = get_logger()


class FileSyncManager:
    """Manages file synchronization from server to client."""
    
    def __init__(self, config: Config, employee_name: str):
        """
        Initialize file sync manager.
        
        Args:
            config: Configuration object
            employee_name: Name of the employee
        """
        self.config = config
        self.employee_name = employee_name
        self.client_id = retrieve_client_id()  # Get or generate unique client ID
        self.download_path = self._get_download_path()
        self.poll_interval = self._get_poll_interval()
        self.max_parallel = 5
        self.running = False
        self.download_queue: Queue = Queue()
        self.active_downloads: List[threading.Thread] = []
        self.downloaded_files: set = set()  # Set of file IDs
        self.file_id_to_name: Dict[str, str] = {}  # Map file ID to filename for deletion
        self.check_counter: int = 0  # Counter for logging
        
        # Ensure download directory exists
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 File sync manager initialized. Download path: {self.download_path}")
        logger.info(f"🆔 Client ID: {self.client_id}")
        logger.info(f"⏱️  File sync will check every {self.poll_interval} seconds")
    
    def _get_download_path(self) -> Path:
        """Get the download path from environment or use default."""
        path_str = os.getenv('FILE_DOWNLOAD_PATH', 'C:\\Downloads\\CompanyFiles')
        return Path(path_str)
    
    def _get_poll_interval(self) -> int:
        """
        Get the polling interval in seconds.
        NOTE: This is no longer used since file sync now happens on every app usage poll.
        Kept for backward compatibility with config.
        """
        try:
            return int(os.getenv('FILE_SYNC_INTERVAL', '10'))
        except ValueError:
            return 10
    
    def start(self):
        """Start the file sync manager."""
        if self.running:
            logger.warning("⚠️  File sync manager already running")
            return
        
        self.running = True
        
        print(f"✅ FILE SYNC: Started (checks on every app usage poll)")
        logger.info(f"✅ File sync manager started")
        logger.info(f"📁 Download path: {self.download_path}")
        logger.info(f"👤 Employee: {self.employee_name}")
        logger.info(f"⏱️  Will check on every app usage poll (no separate interval)")
        
        # Do an immediate check
        logger.info("🔍 Performing initial file check...")
        print("🔍 FILE SYNC: Performing initial check...")
        try:
            self._check_pending_files()
            self._process_download_queue()
        except Exception as e:
            logger.error(f"❌ Error in initial file check: {e}", exc_info=True)
            print(f"❌ FILE SYNC: Error in initial check: {e}")
    
    def stop(self):
        """Stop the file sync manager."""
        self.running = False
        print("🛑 FILE SYNC: Stopped")
        logger.info("🛑 File sync manager stopped")
    
    def update(self):
        """
        Update file sync - check for files on every call.
        This is called from the app usage tracker's polling loop (every 10 seconds).
        """
        if not self.running:
            return
        
        self.check_counter += 1
        
        # Check on every update (no separate interval)
        try:
            self._check_pending_files()
            self._process_download_queue()
        except Exception as e:
            logger.error(f"❌ Error in file sync update: {e}", exc_info=True)
            print(f"❌ FILE SYNC: Error - {e}")
    
    def check_and_download(self):
        """
        Force an immediate check for pending files and process downloads.
        This can be called manually or from WebSocket events.
        """
        if not self.running:
            return
        
        print("🔍 FILE SYNC: Force check triggered")
        logger.info("🔍 File sync: Force check triggered")
        
        try:
            self._check_pending_files()
            self._process_download_queue()
        except Exception as e:
            logger.error(f"❌ Error in check_and_download: {e}", exc_info=True)
            print(f"❌ FILE SYNC: Error - {e}")
    
    def _check_pending_files(self):
        """Check server for pending files and sync deletions."""
        try:
            # Extract base URL (remove /api/monitoring/data if present)
            base_url = self.config.server_url.replace('/api/monitoring/data', '')
            
            # First, check for pending files to download
            pending_url = f"{base_url}/api/files/pending/{self.employee_name}?client_id={self.client_id}"
            
            print(f"🌐 FILE SYNC: Checking {pending_url}")
            logger.info(f"🌐 Checking pending files at: {pending_url}")
            logger.debug(f"👤 Employee name: {self.employee_name}")
            logger.debug(f"🆔 Client ID: {self.client_id}")
            
            headers = {
                'Authorization': f'Bearer {self.config.auth_token}'
            }
            
            response = requests.get(pending_url, headers=headers, timeout=10)
            
            logger.debug(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                files = data.get('files', [])
                
                if len(files) > 0:
                    print(f"📦 FILE SYNC: Found {len(files)} pending file(s)!")
                    logger.info(f"📦 Found {len(files)} pending file(s)")
                # Only log "no pending files" occasionally to reduce noise
                elif self.check_counter % 6 == 1:  # Every ~60 seconds (6 polls * 10s)
                    print(f"✅ FILE SYNC: No pending files (check #{self.check_counter})")
                    logger.info(f"✅ No pending files")
                
                for file_info in files:
                    file_id = file_info['id']
                    filename = file_info['filename']
                    filesize = file_info.get('fileSize', 0)
                    
                    print(f"📄 FILE SYNC: {filename} ({filesize} bytes, ID: {file_id})")
                    logger.info(f"📄 File: {filename} (ID: {file_id}, Size: {filesize})")
                    
                    if file_id not in self.downloaded_files:
                        self.download_queue.put(file_info)
                        print(f"✅ FILE SYNC: Queued for download: {filename}")
                        logger.info(f"✅ Queued file for download: {filename}")
                    else:
                        print(f"⏭️  FILE SYNC: Already downloaded: {filename}")
                        logger.debug(f"⏭️  File already downloaded: {filename}")
            else:
                print(f"⚠️  FILE SYNC: HTTP {response.status_code}")
                logger.warning(f"⚠️  Failed to check pending files: HTTP {response.status_code}")
                logger.debug(f"Response body: {response.text[:200]}")
            
            # Now check for deleted files by getting list of active files
            print("🔍 FILE SYNC: Checking for deleted files...")
            logger.info("🔍 Checking for deleted files...")
            self._sync_deletions(base_url, headers)
        
        except Exception as e:
            print(f"❌ FILE SYNC: Error checking files - {e}")
            logger.error(f"❌ Error checking pending files: {e}", exc_info=True)
    
    def _sync_deletions(self, base_url: str, headers: Dict):
        """
        Check for deleted files and remove them from local storage.
        
        Args:
            base_url: Base URL of the server
            headers: HTTP headers with auth token
        """
        try:
            # Get list of all active files from server
            active_url = f"{base_url}/api/files/active/{self.employee_name}"
            
            print(f"🌐 FILE SYNC: Checking active files at {active_url}")
            logger.info(f"🔍 Checking for deleted files at: {active_url}")
            
            response = requests.get(active_url, headers=headers, timeout=10)
            
            print(f"📊 FILE SYNC: Active files response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                active_files = data.get('files', [])
                
                # Build set of filenames that should exist
                server_filenames = {f['filename'] for f in active_files}
                
                print(f"📋 FILE SYNC: Server has {len(server_filenames)} active file(s): {server_filenames}")
                logger.info(f"📋 Server has {len(server_filenames)} active file(s)")
                
                # Check local files
                if self.download_path.exists():
                    local_files = list(self.download_path.iterdir())
                    local_filenames = [f.name for f in local_files if f.is_file()]
                    
                    print(f"📂 FILE SYNC: Local has {len(local_filenames)} file(s): {local_filenames}")
                    
                    for local_file in local_files:
                        if local_file.is_file():
                            filename = local_file.name
                            
                            # If file exists locally but not on server, delete it
                            if filename not in server_filenames:
                                try:
                                    local_file.unlink()
                                    print(f"🗑️  FILE SYNC: Deleted orphaned file: {filename}")
                                    logger.info(f"🗑️  Deleted orphaned file: {filename}")
                                    
                                    # Remove from tracking
                                    file_id_to_remove = None
                                    for fid, fname in self.file_id_to_name.items():
                                        if fname == filename:
                                            file_id_to_remove = fid
                                            break
                                    
                                    if file_id_to_remove:
                                        if file_id_to_remove in self.downloaded_files:
                                            self.downloaded_files.remove(file_id_to_remove)
                                        if file_id_to_remove in self.file_id_to_name:
                                            del self.file_id_to_name[file_id_to_remove]
                                
                                except Exception as e:
                                    print(f"❌ FILE SYNC: Error deleting {filename}: {e}")
                                    logger.error(f"Error deleting orphaned file {filename}: {e}")
                else:
                    print("📂 FILE SYNC: Download directory doesn't exist")
            else:
                print(f"⚠️  FILE SYNC: Could not check for deletions: HTTP {response.status_code}")
                logger.warning(f"Could not check for deletions: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"❌ FILE SYNC: Error syncing deletions: {e}")
            logger.error(f"Error syncing deletions: {e}", exc_info=True)
    
    def _process_download_queue(self):
        """Process the download queue with parallel downloads."""
        # Clean up completed threads
        self.active_downloads = [t for t in self.active_downloads if t.is_alive()]
        
        queue_size = self.download_queue.qsize()
        active_count = len(self.active_downloads)
        
        if queue_size > 0 or active_count > 0:
            print(f"📥 FILE SYNC: Queue={queue_size}, Active={active_count}")
            logger.info(f"📥 Download queue: {queue_size} pending, {active_count} active")
        
        # Start new downloads up to max parallel limit
        while len(self.active_downloads) < self.max_parallel and not self.download_queue.empty():
            file_info = self.download_queue.get()
            print(f"🚀 FILE SYNC: Starting download thread for: {file_info['filename']}")
            logger.info(f"🚀 Starting download thread for: {file_info['filename']}")
            thread = threading.Thread(
                target=self._download_file,
                args=(file_info,),
                daemon=True
            )
            thread.start()
            self.active_downloads.append(thread)
    
    def _download_file(self, file_info: Dict):
        """
        Download a file from the server.
        
        Args:
            file_info: Dictionary containing file information
        """
        file_id = file_info['id']
        filename = file_info['filename']
        
        try:
            print(f"⬇️  FILE SYNC: Downloading {filename}...")
            logger.info(f"⬇️  Starting download: {filename}")
            logger.debug(f"File ID: {file_id}, Size: {file_info.get('fileSize', 'unknown')}")
            
            # Update status to downloading
            self._update_status(file_id, 'downloading')
            
            # Extract base URL (remove /api/monitoring/data if present)
            base_url = self.config.server_url.replace('/api/monitoring/data', '')
            
            # Download file
            url = f"{base_url}/api/files/{file_id}/download"
            logger.debug(f"🌐 Download URL: {url}")
            
            headers = {
                'Authorization': f'Bearer {self.config.auth_token}'
            }
            params = {
                'employeeName': self.employee_name
            }
            
            logger.debug(f"📡 Sending download request...")
            response = requests.get(
                url,
                headers=headers,
                params=params,
                stream=True,
                timeout=300  # 5 minutes timeout for large files
            )
            
            logger.debug(f"📊 Download response status: {response.status_code}")
            
            if response.status_code == 200:
                # Save file
                file_path = self.download_path / filename
                print(f"💾 FILE SYNC: Saving to {file_path}")
                logger.info(f"💾 Saving file to: {file_path}")
                
                bytes_downloaded = 0
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            bytes_downloaded += len(chunk)
                
                print(f"✅ FILE SYNC: Downloaded {filename} ({bytes_downloaded} bytes)")
                logger.info(f"✅ Download completed: {filename} ({bytes_downloaded} bytes)")
                logger.debug(f"File saved at: {file_path}")
                
                # Update status to completed
                self._update_status(file_id, 'completed')
                self.downloaded_files.add(file_id)
                
                # Track file ID to filename mapping for deletion
                self.file_id_to_name[file_id] = filename
                
            else:
                error_msg = f"Download failed with status {response.status_code}"
                print(f"❌ FILE SYNC: {error_msg} - {filename}")
                logger.error(f"❌ {error_msg}: {filename}")
                logger.debug(f"Response body: {response.text[:200]}")
                self._update_status(file_id, 'failed', error_msg)
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ FILE SYNC: Error downloading {filename} - {error_msg}")
            logger.error(f"❌ Error downloading file {filename}: {error_msg}", exc_info=True)
            self._update_status(file_id, 'failed', error_msg)
    
    def _update_status(self, file_id: str, status: str, error: Optional[str] = None):
        """
        Update download status on server.
        
        Args:
            file_id: File transfer ID
            status: Status to update (downloading, completed, failed)
            error: Optional error message
        """
        try:
            # Extract base URL (remove /api/monitoring/data if present)
            base_url = self.config.server_url.replace('/api/monitoring/data', '')
            
            url = f"{base_url}/api/files/{file_id}/status"
            headers = {
                'Authorization': f'Bearer {self.config.auth_token}',
                'Content-Type': 'application/json'
            }
            data = {
                'employeeName': self.employee_name,
                'status': status
            }
            
            if error:
                data['error'] = error
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to update status: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def handle_file_uploaded(self, payload: Dict):
        """
        Handle file uploaded WebSocket event.
        
        Args:
            payload: Event payload containing file information
        """
        filename = payload.get('filename', 'unknown')
        print(f"📢 FILE SYNC: New file uploaded - {filename}")
        logger.info(f"📢 Received file upload notification: {filename}")
        
        # Immediately check for pending files
        print("🔍 FILE SYNC: Checking for new files...")
        self.check_and_download()
    
    def handle_file_deleted(self, payload: Dict):
        """
        Handle file deleted WebSocket event.
        Deletes the local file from the download directory.
        
        Args:
            payload: Event payload containing file ID and filename
        """
        file_id = payload.get('fileId')
        
        print(f"🗑️  FILE SYNC: Received deletion request for file ID: {file_id}")
        logger.info(f"🗑️  Received file deletion notification: {file_id}")
        
        # Try to get filename from mapping
        filename = self.file_id_to_name.get(file_id)
        
        if not filename:
            # If not in mapping, try to get from payload
            filename = payload.get('filename')
            print(f"⚠️  FILE SYNC: Filename not in cache, using payload: {filename}")
            logger.warning(f"Filename not in cache for file ID {file_id}, using payload")
        
        if filename:
            file_path = self.download_path / filename
            
            try:
                if file_path.exists():
                    file_path.unlink()
                    print(f"✅ FILE SYNC: Deleted local file: {filename}")
                    logger.info(f"✅ Deleted local file: {file_path}")
                else:
                    print(f"⚠️  FILE SYNC: File not found locally: {filename}")
                    logger.warning(f"File not found locally: {file_path}")
            except Exception as e:
                print(f"❌ FILE SYNC: Error deleting file {filename}: {e}")
                logger.error(f"❌ Error deleting file {filename}: {e}", exc_info=True)
        else:
            print(f"❌ FILE SYNC: Cannot delete - filename unknown for ID: {file_id}")
            logger.error(f"Cannot delete file - filename unknown for ID: {file_id}")
        
        # Remove from tracking sets
        if file_id in self.downloaded_files:
            self.downloaded_files.remove(file_id)
            print(f"🗑️  FILE SYNC: Removed {file_id} from downloaded files tracking")
        
        if file_id in self.file_id_to_name:
            del self.file_id_to_name[file_id]
            print(f"🗑️  FILE SYNC: Removed {file_id} from filename mapping")
