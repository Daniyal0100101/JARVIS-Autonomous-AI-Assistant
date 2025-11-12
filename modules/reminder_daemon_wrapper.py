"""Wrapper functions for daemon-managed reminders and tasks.

This module provides updated add_reminder() and check_reminders() functions
that leverage the background task_daemon for autonomous operation.

Import these to replace the legacy versions in utils.py:
    from modules.reminder_daemon_wrapper import add_reminder, check_reminders
"""

from datetime import datetime, timedelta
import time
from typing import Dict, Any


def add_reminder(reminder_time_str: str, message: str) -> Dict[str, Any]:
    """Add a reminder at a specific time (daemon-managed, autonomous).
    
    The reminder will fire automatically at the specified time without requiring
    the user to manually check. State persists across restarts.
    
    Args:
        reminder_time_str (str): Time in "HH:MM AM/PM" format (e.g., "3:30 PM")
        message (str): The reminder message
    
    Returns:
        dict: Status and details of the reminder
            {
                "status": "success"|"error",
                "message": str,
                "reminder_id": str or None,
                "scheduled_time": str or None,
                "daemon_managed": bool
            }
    """
    if not message or not reminder_time_str:
        return {
            "status": "error",
            "message": "Both time and reminder message are required",
            "reminder_id": None,
            "scheduled_time": None,
            "daemon_managed": False
        }
    
    try:
        # Try parsing with multiple time formats
        reminder_time = None
        for time_format in ["%I:%M %p", "%H:%M"]:
            try:
                reminder_time = datetime.strptime(reminder_time_str, time_format)
                break
            except ValueError:
                continue
        
        if reminder_time is None:
            return {
                "status": "error",
                "message": "Invalid time format. Use '3:30 PM' or '15:30'",
                "reminder_id": None,
                "scheduled_time": None,
                "daemon_managed": False
            }
        
        # Set to today's date
        now = datetime.now()
        reminder_time = reminder_time.replace(
            year=now.year,
            month=now.month,
            day=now.day
        )
        
        # If time is in past, schedule for tomorrow
        if reminder_time < now:
            reminder_time += timedelta(days=1)
        
        # Add to daemon for autonomous firing
        try:
            from .task_daemon import get_daemon
            daemon = get_daemon()
            reminder_id = daemon.add_reminder(reminder_time, message)
            
            return {
                "status": "success",
                "message": "Reminder set successfully (autonomous daemon active)",
                "reminder_id": reminder_id,
                "scheduled_time": reminder_time.strftime("%Y-%m-%d %I:%M %p"),
                "daemon_managed": True
            }
        except ImportError:
            # Fallback to legacy in-memory storage if daemon not available
            from modules import reminders
            reminder_id = f"reminder_{len(reminders)}_{int(time.time())}"
            reminders.append((reminder_time, message, reminder_id))
            
            return {
                "status": "success",
                "message": "Reminder set successfully (legacy fallback mode)",
                "reminder_id": reminder_id,
                "scheduled_time": reminder_time.strftime("%Y-%m-%d %I:%M %p"),
                "daemon_managed": False
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating reminder: {str(e)}",
            "reminder_id": None,
            "scheduled_time": None,
            "daemon_managed": False
        }


def check_reminders() -> Dict[str, Any]:
    """Check active reminders status (daemon auto-fires due reminders).
    
    With the daemon active, reminders fire automatically at scheduled times.
    This function is primarily used to query the status of pending reminders.
    
    Returns:
        dict: Status and list of active/due reminders
            {
                "status": "success"|"error",
                "daemon_managed": bool,
                "message": str,
                "active_count": int,
                "active_reminders": list,
                "due_reminders": list (if legacy mode)
            }
    """
    try:
        try:
            from .task_daemon import get_daemon
            daemon = get_daemon()
            active_reminders = daemon.get_active_reminders()
            
            active_list = []
            for reminder in active_reminders:
                try:
                    reminder_time = datetime.fromisoformat(reminder['time'])
                    active_list.append({
                        "id": reminder['id'],
                        "time": reminder_time.strftime("%Y-%m-%d %I:%M %p"),
                        "message": reminder['message'],
                        "status": "pending",
                        "created_at": reminder.get('created_at', 'N/A')
                    })
                except Exception as e:
                    pass  # Skip malformed reminders
            
            return {
                "status": "success",
                "message": "Daemon is managing reminders autonomously",
                "daemon_managed": True,
                "active_count": len(active_list),
                "active_reminders": active_list
            }
        
        except ImportError:
            # Fallback to legacy checking
            from modules.text_to_speech import speak
            from modules import reminders
            
            now = datetime.now()
            due_reminders = []
            active_reminders_list = []
            
            for reminder in reminders[:]:
                reminder_time, message, reminder_id = reminder
                if now >= reminder_time:
                    due_reminders.append({
                        "id": reminder_id,
                        "time": reminder_time.strftime("%Y-%m-%d %I:%M %p"),
                        "message": message,
                        "status": "due"
                    })
                    reminders.remove(reminder)
                    speak(f"Reminder: {message}")
                else:
                    active_reminders_list.append({
                        "id": reminder_id,
                        "time": reminder_time.strftime("%Y-%m-%d %I:%M %p"),
                        "message": message,
                        "status": "pending"
                    })
            
            return {
                "status": "success",
                "daemon_managed": False,
                "message": "Using legacy reminder system",
                "due_count": len(due_reminders),
                "active_count": len(active_reminders_list),
                "due_reminders": due_reminders,
                "active_reminders": active_reminders_list
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking reminders: {str(e)}",
            "daemon_managed": False,
            "active_count": 0,
            "active_reminders": []
        }


def remove_reminder(reminder_id: str) -> Dict[str, Any]:
    """Remove a reminder by ID (daemon-managed).
    
    Args:
        reminder_id (str): ID of reminder to remove
    
    Returns:
        dict: Status of removal operation
    """
    try:
        from .task_daemon import get_daemon
        daemon = get_daemon()
        success = daemon.remove_reminder(reminder_id)
        
        return {
            "status": "success" if success else "error",
            "message": "Reminder removed" if success else "Reminder not found",
            "reminder_id": reminder_id if success else None,
            "daemon_managed": True
        }
    except ImportError:
        from modules import reminders
        original_len = len(reminders)
        reminders[:] = [r for r in reminders if r[2] != reminder_id]
        
        if len(reminders) < original_len:
            return {
                "status": "success",
                "message": "Reminder removed",
                "reminder_id": reminder_id,
                "daemon_managed": False
            }
        else:
            return {
                "status": "error",
                "message": "Reminder not found",
                "reminder_id": None,
                "daemon_managed": False
            }


def get_daemon_status() -> Dict[str, Any]:
    """Get the status of the background task daemon.
    
    Returns:
        dict: Daemon status information
    """
    try:
        from .task_daemon import get_daemon
        daemon = get_daemon()
        
        active_reminders = daemon.get_active_reminders()
        active_tasks = daemon.get_active_tasks()
        
        return {
            "status": "success",
            "daemon_running": daemon.running,
            "reminders_count": len(active_reminders),
            "tasks_count": len(active_tasks),
            "check_interval": daemon.check_interval,
            "message": f"Daemon running with {len(active_reminders)} reminders and {len(active_tasks)} tasks"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting daemon status: {str(e)}",
            "daemon_running": False
        }
