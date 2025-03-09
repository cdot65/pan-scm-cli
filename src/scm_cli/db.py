"""Database module for SCM CLI history."""

import datetime
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple


class CLIHistoryDB:
    """Database for storing CLI command history."""

    def __init__(self, db_path: str = "scm_cli_history.db") -> None:
        """Initialize the history database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()
        
    def _initialize_db(self) -> None:
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create command history table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            command TEXT NOT NULL,
            response TEXT,
            folder TEXT,
            success INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def add_command(
        self, 
        command: str, 
        response: Optional[str] = None, 
        folder: Optional[str] = None,
        success: bool = True
    ) -> int:
        """Add a command to the history.
        
        Args:
            command: The command that was executed
            response: The response from the command
            folder: The current folder context when the command was executed
            success: Whether the command executed successfully
            
        Returns:
            The ID of the inserted record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO command_history (timestamp, command, response, folder, success) VALUES (?, ?, ?, ?, ?)",
            (timestamp, command, response, folder, 1 if success else 0)
        )
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
        
    def get_history(
        self, 
        limit: int = 50,
        page: int = 1,
        folder: Optional[str] = None,
        command_filter: Optional[str] = None
    ) -> Tuple[List[Tuple[int, str, str, str, str, bool]], int]:
        """Get command history with pagination.
        
        Args:
            limit: Maximum number of records to return per page
            page: Page number (starting from 1)
            folder: Filter by folder context
            command_filter: Filter commands containing this string
            
        Returns:
            Tuple of (history_items, total_count) where:
                - history_items: List of tuples (id, timestamp, command, response, folder, success)
                - total_count: Total number of matching records (ignoring pagination)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Base query for both count and data retrieval
        base_query = "FROM command_history"
        params = []
        
        where_clauses = []
        if folder:
            where_clauses.append("folder = ?")
            params.append(folder)
            
        if command_filter:
            where_clauses.append("command LIKE ?")
            params.append(f"%{command_filter}%")
            
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        # Get total count
        count_query = f"SELECT COUNT(*) {base_query}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get paginated data
        data_query = f"SELECT id, timestamp, command, response, folder, success {base_query} ORDER BY id DESC LIMIT ? OFFSET ?"
        cursor.execute(data_query, params + [limit, offset])
        
        results = [
            (
                row[0],                  # id
                row[1],                  # timestamp
                row[2],                  # command
                row[3] if row[3] else "", # response
                row[4] if row[4] else "", # folder
                bool(row[5])             # success
            )
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return results, total_count
        
    def get_history_entry(self, entry_id: int) -> Optional[Tuple[int, str, str, str, str, bool]]:
        """Get a specific history entry by ID.
        
        Args:
            entry_id: The ID of the history entry to retrieve
            
        Returns:
            Tuple of (id, timestamp, command, response, folder, success) or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, timestamp, command, response, folder, success FROM command_history WHERE id = ?",
            (entry_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return (
            row[0],                  # id
            row[1],                  # timestamp
            row[2],                  # command
            row[3] if row[3] else "", # response
            row[4] if row[4] else "", # folder
            bool(row[5])             # success
        )
        
    def clear_history(self) -> None:
        """Clear all command history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM command_history")
        
        conn.commit()
        conn.close()