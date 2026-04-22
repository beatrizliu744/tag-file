import sqlite3
import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional

class DatabaseManager:
    """SQLite database manager for Tag File application"""
    
    def __init__(self, db_path: str):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL UNIQUE,
                tags TEXT NOT NULL DEFAULT '/',
                description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_file(self, filename: str, filepath: str, tags: str, description: str = '') -> int:
        """Add a new file record to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO files (filename, filepath, tags, description)
                VALUES (?, ?, ?, ?)
            ''', (filename, filepath, tags, description))
            conn.commit()
            file_id = cursor.lastrowid
            return file_id
        except sqlite3.IntegrityError as e:
            print(f"Error adding file: {e}")
            return -1
        finally:
            conn.close()
    
    def get_all_files(self) -> List[Tuple]:
        """Get all files from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, filename, filepath, tags, description FROM files ORDER BY updated_at DESC')
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_file_by_id(self, file_id: int) -> Optional[Tuple]:
        """Get a specific file by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, filename, filepath, tags, description FROM files WHERE id = ?', (file_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def update_file(self, file_id: int, filename: str = None, filepath: str = None, 
                    tags: str = None, description: str = None) -> bool:
        """Update file record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if filename is not None:
            updates.append('filename = ?')
            params.append(filename)
        if filepath is not None:
            updates.append('filepath = ?')
            params.append(filepath)
        if tags is not None:
            updates.append('tags = ?')
            params.append(tags)
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        
        if not updates:
            return False
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(file_id)
        
        query = f"UPDATE files SET {', '.join(updates)} WHERE id = ?"
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating file: {e}")
            return False
        finally:
            conn.close()
    
    def delete_file(self, file_id: int) -> bool:
        """Delete file record from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting file: {e}")
            return False
        finally:
            conn.close()
    
    def search_files(self, query: str) -> List[Tuple]:
        """Search files by filename, tags, or description"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT id, filename, filepath, tags, description FROM files
            WHERE filename LIKE ? OR tags LIKE ? OR description LIKE ?
            ORDER BY updated_at DESC
        ''', (search_term, search_term, search_term))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_files_by_tag(self, tag: str) -> List[Tuple]:
        """Get all files with a specific tag or tag prefix"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Handle tag hierarchy (e.g., 'Finance/Audit' should match 'Finance/Audit' and 'Finance/Audit/2024')
        tag_pattern = f"{tag}%" if not tag.endswith('/') else f"{tag}%"
        cursor.execute('''
            SELECT id, filename, filepath, tags, description FROM files
            WHERE tags LIKE ? OR tags = ?
            ORDER BY updated_at DESC
        ''', (tag_pattern, tag))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_tag_tree(self) -> Dict:
        """Build a hierarchical tag tree from all files"""
        all_files = self.get_all_files()
        tag_tree = {}
        
        for file_id, filename, filepath, tags, description in all_files:
            if tags == '/':
                tag_list = []
            else:
                tag_list = tags.strip('/').split('/')
            
            current = tag_tree
            for tag in tag_list:
                if tag not in current:
                    current[tag] = {}
                current = current[tag]
        
        return tag_tree
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT tags FROM files')
        results = cursor.fetchall()
        conn.close()
        
        tags = set()
        for (tag_str,) in results:
            if tag_str != '/':
                for tag in tag_str.strip('/').split('/'): 
                    tags.add(tag)
        
        return sorted(list(tags))