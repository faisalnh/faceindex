"""
Database module for FaceIndex Local.
Handles SQLite connections and schema management.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np


class Database:
    """Manages all database operations for the application."""

    def __init__(self, db_path: str = "faceindex.db"):
        self.db_path = db_path
        self.connection = None
        self.initialize()

    def initialize(self):
        """Create database connection and tables if they don't exist."""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create all necessary tables."""
        cursor = self.connection.cursor()

        # Videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                duration REAL,
                fps REAL,
                width INTEGER,
                height INTEGER,
                roi_x INTEGER,
                roi_y INTEGER,
                roi_w INTEGER,
                roi_h INTEGER,
                processing_status TEXT DEFAULT 'pending',
                processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Persons (Clusters) table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                cluster_id INTEGER NOT NULL,
                name TEXT,
                thumbnail_path TEXT,
                face_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE,
                UNIQUE(video_id, cluster_id)
            )
        """)

        # Face Instances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                frame_number INTEGER NOT NULL,
                bbox_x INTEGER,
                bbox_y INTEGER,
                bbox_w INTEGER,
                bbox_h INTEGER,
                encoding BLOB NOT NULL,
                confidence REAL,
                thumbnail_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES persons (id) ON DELETE CASCADE,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
            )
        """)

        # Create indices for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_face_instances_person
            ON face_instances(person_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_face_instances_video
            ON face_instances(video_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_face_instances_timestamp
            ON face_instances(timestamp)
        """)

        self.connection.commit()

    def add_video(
        self,
        file_path: str,
        file_name: str,
        duration: float,
        fps: float,
        width: int,
        height: int,
        roi: Tuple[int, int, int, int],
    ) -> int:
        """Add a new video to the database."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO videos
            (file_path, file_name, duration, fps, width, height, roi_x, roi_y, roi_w, roi_h)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                file_path,
                file_name,
                duration,
                fps,
                width,
                height,
                roi[0],
                roi[1],
                roi[2],
                roi[3],
            ),
        )
        self.connection.commit()
        return cursor.lastrowid

    def update_video_status(self, video_id: int, status: str):
        """Update processing status of a video."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE videos
            SET processing_status = ?, processed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (status, video_id),
        )
        self.connection.commit()

    def add_person(
        self,
        video_id: int,
        cluster_id: int,
        name: Optional[str] = None,
        thumbnail_path: Optional[str] = None,
    ) -> int:
        """Add a new person (cluster) to the database."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO persons (video_id, cluster_id, name, thumbnail_path)
            VALUES (?, ?, ?, ?)
        """,
            (video_id, cluster_id, name, thumbnail_path),
        )
        self.connection.commit()
        return cursor.lastrowid

    def add_face_instance(
        self,
        person_id: int,
        video_id: int,
        timestamp: float,
        frame_number: int,
        bbox: Tuple[int, int, int, int],
        encoding: np.ndarray,
        confidence: float = 1.0,
        thumbnail_path: Optional[str] = None,
    ) -> int:
        """Add a face instance to the database."""
        # Convert numpy array to bytes for storage
        encoding_bytes = encoding.tobytes()

        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO face_instances
            (person_id, video_id, timestamp, frame_number,
             bbox_x, bbox_y, bbox_w, bbox_h, encoding, confidence, thumbnail_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                person_id,
                video_id,
                timestamp,
                frame_number,
                bbox[0],
                bbox[1],
                bbox[2],
                bbox[3],
                encoding_bytes,
                confidence,
                thumbnail_path,
            ),
        )

        # Update person face count
        cursor.execute(
            """
            UPDATE persons
            SET face_count = face_count + 1
            WHERE id = ?
        """,
            (person_id,),
        )

        self.connection.commit()
        return cursor.lastrowid

    def get_persons_by_video(self, video_id: int) -> List[sqlite3.Row]:
        """Get all persons for a specific video."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT * FROM persons
            WHERE video_id = ?
            ORDER BY face_count DESC
        """,
            (video_id,),
        )
        return cursor.fetchall()

    def get_face_instances_by_person(self, person_id: int) -> List[sqlite3.Row]:
        """Get all face instances for a person, ordered by timestamp."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT * FROM face_instances
            WHERE person_id = ?
            ORDER BY timestamp ASC
        """,
            (person_id,),
        )
        return cursor.fetchall()

    def get_video_by_id(self, video_id: int) -> Optional[sqlite3.Row]:
        """Get video information by ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        return cursor.fetchone()

    def get_all_videos(self) -> List[sqlite3.Row]:
        """Get all videos."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
        return cursor.fetchall()

    def update_person_name(self, person_id: int, name: str):
        """Update the name of a person."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE persons SET name = ? WHERE id = ?
        """,
            (name, person_id),
        )
        self.connection.commit()

    def merge_persons(self, source_person_id: int, target_person_id: int):
        """Merge two persons by moving all face instances from source to target."""
        cursor = self.connection.cursor()

        # Move all face instances
        cursor.execute(
            """
            UPDATE face_instances
            SET person_id = ?
            WHERE person_id = ?
        """,
            (target_person_id, source_person_id),
        )

        # Update target person face count
        cursor.execute(
            """
            UPDATE persons
            SET face_count = (
                SELECT COUNT(*) FROM face_instances WHERE person_id = ?
            )
            WHERE id = ?
        """,
            (target_person_id, target_person_id),
        )

        # Delete source person
        cursor.execute("DELETE FROM persons WHERE id = ?", (source_person_id,))

        self.connection.commit()

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
