"""Background task daemon for autonomous reminder and task execution.

Runs in a separate thread, monitors reminders/tasks without blocking the main loop.
Persists state to JSON for restart recovery. Fires notifications automatically.
"""

import os
import json
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
import logging

# Configure minimal logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Paths for persistence
DAEMON_DIR = os.path.expanduser("~/.jarvis")
REMINDERS_FILE = os.path.join(DAEMON_DIR, "reminders.json")
TASKS_FILE = os.path.join(DAEMON_DIR, "tasks.json")
DAEMON_STATE_FILE = os.path.join(DAEMON_DIR, "daemon_state.json")


class TaskDaemon:
    """Background daemon for managing reminders and scheduled tasks.
    
    Runs in a separate thread, checking every 30 seconds if any reminders/tasks
    are due. When a reminder fires, it calls registered callbacks (e.g., speak, notify).
    
    All state is persisted to JSON for restart recovery.
    """
    
    def __init__(self, check_interval: int = 30):
        """
        Args:
            check_interval: Seconds between reminder checks (default 30)
        """
        self.check_interval = check_interval
        self.running = False
        self.daemon_thread = None
        self.lock = threading.Lock()
        
        # Registered callbacks for when reminders fire
        self.callbacks: Dict[str, List[Callable]] = {
            'on_reminder_due': [],
            'on_task_due': [],
            'on_error': []
        }
        
        # In-memory state
        self.reminders: List[Dict[str, Any]] = []
        self.tasks: List[Dict[str, Any]] = []
        self.fired_reminders: set = set()  # Track fired reminders to avoid duplicates
        
        # Ensure daemon directory exists
        os.makedirs(DAEMON_DIR, exist_ok=True)
        
        # Load persisted state
        self._load_state()
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for an event.
        
        Args:
            event: Event name ('on_reminder_due', 'on_task_due', 'on_error')
            callback: Callable that receives (reminder/task_dict) as argument
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def start(self) -> bool:
        """Start the background daemon thread.
        
        Returns:
            True if started successfully, False if already running
        """
        if self.running:
            logger.warning("Daemon already running")
            return False
        
        self.running = True
        self.daemon_thread = threading.Thread(target=self._run, daemon=True)
        self.daemon_thread.start()
        logger.info("Task daemon started")
        return True
    
    def stop(self) -> bool:
        """Stop the background daemon thread.
        
        Returns:
            True if stopped, False if not running
        """
        if not self.running:
            return False
        
        self.running = False
        if self.daemon_thread:
            self.daemon_thread.join(timeout=5)
        
        self._save_state()
        logger.info("Task daemon stopped")
        return True
    
    def add_reminder(self, reminder_time: datetime, message: str) -> str:
        """Add a reminder to the queue.
        
        Args:
            reminder_time: datetime when reminder should fire
            message: Reminder message
        
        Returns:
            Reminder ID
        """
        reminder_id = f"reminder_{int(time.time() * 1000)}"
        
        reminder = {
            'id': reminder_id,
            'time': reminder_time.isoformat(),
            'message': message,
            'created_at': datetime.now().isoformat(),
            'fired': False,
            'acknowledged': False
        }
        
        with self.lock:
            self.reminders.append(reminder)
            self._save_state()
        
        logger.info(f"Reminder added: {reminder_id} at {reminder_time}")
        return reminder_id
    
    def add_task(self, task_time: datetime, task_name: str, 
                 task_action: str = None) -> str:
        """Add a scheduled task to the queue.
        
        Args:
            task_time: datetime when task should execute
            task_name: Name/description of task
            task_action: Optional action to execute (e.g., function name)
        
        Returns:
            Task ID
        """
        task_id = f"task_{int(time.time() * 1000)}"
        
        task = {
            'id': task_id,
            'time': task_time.isoformat(),
            'name': task_name,
            'action': task_action,
            'created_at': datetime.now().isoformat(),
            'fired': False,
            'acknowledged': False
        }
        
        with self.lock:
            self.tasks.append(task)
            self._save_state()
        
        logger.info(f"Task added: {task_id} ({task_name}) at {task_time}")
        return task_id
    
    def get_active_reminders(self) -> List[Dict[str, Any]]:
        """Get all non-fired reminders.
        
        Returns:
            List of active reminder dicts
        """
        with self.lock:
            return [r for r in self.reminders if not r['fired']]
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all non-fired tasks.
        
        Returns:
            List of active task dicts
        """
        with self.lock:
            return [t for t in self.tasks if not t['fired']]
    
    def acknowledge_reminder(self, reminder_id: str) -> bool:
        """Mark a reminder as acknowledged (don't re-fire).
        
        Args:
            reminder_id: ID of reminder to acknowledge
        
        Returns:
            True if found and marked, False otherwise
        """
        with self.lock:
            for r in self.reminders:
                if r['id'] == reminder_id:
                    r['acknowledged'] = True
                    self._save_state()
                    return True
        return False
    
    def remove_reminder(self, reminder_id: str) -> bool:
        """Remove a reminder from the queue.
        
        Args:
            reminder_id: ID of reminder to remove
        
        Returns:
            True if removed, False if not found
        """
        with self.lock:
            original_len = len(self.reminders)
            self.reminders = [r for r in self.reminders if r['id'] != reminder_id]
            if len(self.reminders) < original_len:
                self._save_state()
                return True
        return False
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the queue.
        
        Args:
            task_id: ID of task to remove
        
        Returns:
            True if removed, False if not found
        """
        with self.lock:
            original_len = len(self.tasks)
            self.tasks = [t for t in self.tasks if t['id'] != task_id]
            if len(self.tasks) < original_len:
                self._save_state()
                return True
        return False
    
    def clear_fired_reminders(self) -> int:
        """Remove all fired reminders from history.
        
        Returns:
            Number of reminders cleared
        """
        with self.lock:
            original_len = len(self.reminders)
            self.reminders = [r for r in self.reminders if not r['fired']]
            if len(self.reminders) < original_len:
                self._save_state()
            return original_len - len(self.reminders)
    
    def _run(self) -> None:
        """Main daemon loop: check reminders every N seconds."""
        logger.info(f"Daemon loop started (checking every {self.check_interval}s)")
        
        while self.running:
            try:
                self._check_due_reminders()
                self._check_due_tasks()
            except Exception as e:
                logger.error(f"Error in daemon loop: {e}")
                self._fire_callbacks('on_error', {'error': str(e)})
            
            time.sleep(self.check_interval)
        
        logger.info("Daemon loop ended")
    
    def _check_due_reminders(self) -> None:
        """Check if any reminders are due and fire them."""
        now = datetime.now()
        
        with self.lock:
            for reminder in self.reminders:
                if reminder['fired'] or reminder['acknowledged']:
                    continue
                
                reminder_time = datetime.fromisoformat(reminder['time'])
                
                # Check if due (within a 2-minute window to catch it)
                if now >= reminder_time and (now - reminder_time).total_seconds() < 120:
                    # Mark as fired
                    reminder['fired'] = True
                    
                    # Fire callbacks
                    self._fire_callbacks('on_reminder_due', reminder)
                    
                    logger.info(f"Reminder fired: {reminder['id']}")
            
            self._save_state()
    
    def _check_due_tasks(self) -> None:
        """Check if any tasks are due and fire them."""
        now = datetime.now()
        
        with self.lock:
            for task in self.tasks:
                if task['fired'] or task['acknowledged']:
                    continue
                
                task_time = datetime.fromisoformat(task['time'])
                
                # Check if due (within a 2-minute window)
                if now >= task_time and (now - task_time).total_seconds() < 120:
                    # Mark as fired
                    task['fired'] = True
                    
                    # Fire callbacks
                    self._fire_callbacks('on_task_due', task)
                    
                    logger.info(f"Task fired: {task['id']}")
            
            self._save_state()
    
    def _fire_callbacks(self, event: str, data: Dict[str, Any]) -> None:
        """Execute all registered callbacks for an event."""
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in callback {callback.__name__}: {e}")
    
    def _save_state(self) -> None:
        """Persist daemon state to JSON files."""
        try:
            with open(REMINDERS_FILE, 'w') as f:
                json.dump(self.reminders, f, indent=2)
            
            with open(TASKS_FILE, 'w') as f:
                json.dump(self.tasks, f, indent=2)
            
            state = {
                'reminders_count': len(self.reminders),
                'tasks_count': len(self.tasks),
                'last_saved': datetime.now().isoformat()
            }
            with open(DAEMON_STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving daemon state: {e}")
    
    def _load_state(self) -> None:
        """Load daemon state from JSON files."""
        try:
            if os.path.exists(REMINDERS_FILE):
                with open(REMINDERS_FILE, 'r') as f:
                    self.reminders = json.load(f)
                logger.info(f"Loaded {len(self.reminders)} reminders from {REMINDERS_FILE}")
            
            if os.path.exists(TASKS_FILE):
                with open(TASKS_FILE, 'r') as f:
                    self.tasks = json.load(f)
                logger.info(f"Loaded {len(self.tasks)} tasks from {TASKS_FILE}")
        
        except Exception as e:
            logger.error(f"Error loading daemon state: {e}")
            self.reminders = []
            self.tasks = []


# Global daemon instance
_daemon_instance: Optional[TaskDaemon] = None


def get_daemon() -> TaskDaemon:
    """Get or create the global daemon instance."""
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = TaskDaemon(check_interval=30)
    return _daemon_instance


def initialize_daemon(speak_callback: Optional[Callable] = None,
                      notify_callback: Optional[Callable] = None) -> TaskDaemon:
    """Initialize and start the background daemon with callbacks.
    
    Args:
        speak_callback: Function to call when reminder fires (receives reminder dict)
        notify_callback: Function to call to show notification (receives task dict)
    
    Returns:
        Initialized TaskDaemon instance
    """
    daemon = get_daemon()
    
    if speak_callback:
        daemon.register_callback('on_reminder_due', speak_callback)
    
    if notify_callback:
        daemon.register_callback('on_task_due', notify_callback)
    
    daemon.start()
    return daemon


def shutdown_daemon() -> None:
    """Stop the background daemon and save state."""
    global _daemon_instance
    if _daemon_instance and _daemon_instance.running:
        _daemon_instance.stop()
        _daemon_instance = None
