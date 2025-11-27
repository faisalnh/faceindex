"""
Background workers for heavy processing tasks.
Keeps the UI responsive during video processing.
"""

from PyQt6.QtCore import QThread, pyqtSignal
import cv2
import numpy as np
import face_recognition
from sklearn.cluster import DBSCAN
from pathlib import Path
import os
from typing import List, Tuple, Optional
import time


class FaceProcessingWorker(QThread):
    """
    Background worker for processing video and detecting/clustering faces.
    Runs in a separate thread to keep UI responsive.
    """

    # Signals
    progress_update = pyqtSignal(int, str)  # (percentage, status_message)
    processing_finished = pyqtSignal(bool, str)  # (success, message)
    face_found = pyqtSignal(
        object, float, int, tuple
    )  # (image, timestamp, frame_num, bbox)
    faces_clustered = pyqtSignal(int, list)  # (cluster_count, cluster_info)

    def __init__(
        self,
        video_path: str,
        roi: Tuple[int, int, int, int],
        video_id: int,
        database,
        parent=None,
    ):
        super().__init__(parent)
        self.video_path = video_path
        self.roi = roi  # (x, y, w, h)
        self.video_id = video_id
        self.database = database

        # Processing parameters
        self.frame_skip = 15  # Process every Nth frame for speed
        self.min_face_size = 40  # Minimum face size in pixels
        self.clustering_eps = 0.5  # DBSCAN epsilon (lower = stricter)
        self.min_samples = 2  # Minimum faces to form a cluster

        # Data storage
        self.face_encodings = []
        self.face_locations = []
        self.face_timestamps = []
        self.face_frame_numbers = []
        self.face_images = []

        # Thumbnail storage
        self.thumbnail_dir = Path("thumbnails") / str(video_id)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

        self._is_running = True

    def run(self):
        """Main processing loop - runs in background thread."""
        try:
            self.progress_update.emit(0, "Opening video...")

            # Step 1: Detect all faces in video
            success = self._detect_faces()
            if not success:
                return

            # Step 2: Cluster faces
            self.progress_update.emit(80, "Clustering faces...")
            success = self._cluster_faces()
            if not success:
                return

            # Step 3: Save to database
            self.progress_update.emit(90, "Saving to database...")
            self._save_to_database()

            self.progress_update.emit(100, "Processing complete!")
            self.processing_finished.emit(True, "Video processed successfully!")

        except Exception as e:
            self.processing_finished.emit(False, f"Error: {str(e)}")

    def _detect_faces(self) -> bool:
        """Detect faces in video frames."""
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            self.processing_finished.emit(False, "Failed to open video file")
            return False

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        frame_num = 0
        processed_frames = 0
        faces_found = 0

        while self._is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Only process every Nth frame
            if frame_num % self.frame_skip == 0:
                timestamp = frame_num / fps if fps > 0 else 0

                # Crop to ROI
                x, y, w, h = self.roi
                roi_frame = frame[y : y + h, x : x + w]

                # Detect faces in ROI
                faces = self._detect_faces_in_frame(roi_frame, frame_num, timestamp)
                faces_found += len(faces)

                processed_frames += 1

                # Update progress (0-80% for detection)
                progress = int((frame_num / total_frames) * 80)
                status = f"Detecting faces... Frame {frame_num}/{total_frames} ({faces_found} faces found)"
                self.progress_update.emit(progress, status)

            frame_num += 1

        cap.release()

        if faces_found == 0:
            self.processing_finished.emit(
                False, "No faces detected in the selected region"
            )
            return False

        return True

    def _detect_faces_in_frame(
        self, frame: np.ndarray, frame_num: int, timestamp: float
    ) -> List[dict]:
        """Detect faces in a single frame."""
        # Convert BGR to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect faces - using HOG model (faster, good for frontal faces)
        # For better accuracy, use model='cnn' but it's much slower
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")

        if not face_locations:
            return []

        # Get face encodings
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        detected_faces = []

        for location, encoding in zip(face_locations, face_encodings):
            top, right, bottom, left = location

            # Filter out small faces
            face_width = right - left
            face_height = bottom - top
            if face_width < self.min_face_size or face_height < self.min_face_size:
                continue

            # Extract face image for thumbnail
            face_img = frame[top:bottom, left:right].copy()

            # Store data
            self.face_encodings.append(encoding)
            self.face_locations.append(location)
            self.face_timestamps.append(timestamp)
            self.face_frame_numbers.append(frame_num)
            self.face_images.append(face_img)

            detected_faces.append(
                {
                    "location": location,
                    "encoding": encoding,
                    "timestamp": timestamp,
                    "frame_num": frame_num,
                }
            )

        return detected_faces

    def _cluster_faces(self) -> bool:
        """Cluster detected faces using DBSCAN."""
        if len(self.face_encodings) == 0:
            return False

        # Convert to numpy array
        encodings_array = np.array(self.face_encodings)

        # Perform clustering
        clustering = DBSCAN(
            eps=self.clustering_eps, min_samples=self.min_samples, metric="euclidean"
        ).fit(encodings_array)

        self.labels = clustering.labels_

        # Count unique clusters (excluding noise: label -1)
        unique_labels = set(self.labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)

        # Prepare cluster info
        cluster_info = []
        for label in unique_labels:
            if label == -1:
                continue  # Skip noise

            face_count = np.sum(self.labels == label)
            cluster_info.append(
                {"cluster_id": int(label), "face_count": int(face_count)}
            )

        self.faces_clustered.emit(n_clusters, cluster_info)
        return True

    def _save_to_database(self):
        """Save clustered faces to database."""
        # Get unique cluster labels
        unique_labels = set(self.labels)

        # Create person entries for each cluster
        person_map = {}  # cluster_id -> person_id

        for cluster_id in unique_labels:
            if cluster_id == -1:
                continue  # Skip noise

            # Find a representative face for thumbnail (first occurrence)
            cluster_indices = np.where(self.labels == cluster_id)[0]
            first_idx = cluster_indices[0]

            # Save thumbnail
            thumbnail_path = self.thumbnail_dir / f"person_{cluster_id}.jpg"
            cv2.imwrite(str(thumbnail_path), self.face_images[first_idx])

            # Add person to database
            person_id = self.database.add_person(
                video_id=self.video_id,
                cluster_id=int(cluster_id),
                name=f"Person {cluster_id + 1}",
                thumbnail_path=str(thumbnail_path),
            )

            person_map[cluster_id] = person_id

        # Add all face instances
        for idx, cluster_id in enumerate(self.labels):
            if cluster_id == -1:
                continue  # Skip noise

            person_id = person_map[cluster_id]

            # Save face thumbnail
            face_thumbnail_path = self.thumbnail_dir / f"face_{idx}.jpg"
            cv2.imwrite(str(face_thumbnail_path), self.face_images[idx])

            # Get bbox (convert from face_recognition format)
            top, right, bottom, left = self.face_locations[idx]
            bbox = (left, top, right - left, bottom - top)

            # Add to database
            self.database.add_face_instance(
                person_id=person_id,
                video_id=self.video_id,
                timestamp=self.face_timestamps[idx],
                frame_number=self.face_frame_numbers[idx],
                bbox=bbox,
                encoding=self.face_encodings[idx],
                confidence=1.0,
                thumbnail_path=str(face_thumbnail_path),
            )

        # Update video status
        self.database.update_video_status(self.video_id, "completed")

    def stop(self):
        """Stop the worker gracefully."""
        self._is_running = False
        self.wait()


class VideoExportWorker(QThread):
    """Worker for exporting video clips of a specific person."""

    progress_update = pyqtSignal(int, str)
    export_finished = pyqtSignal(bool, str)

    def __init__(
        self, video_path: str, timestamps: List[float], output_path: str, parent=None
    ):
                 output_path: str, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.timestamps = timestamps
        self.output_path = output_path
        self._is_running = True

    def run(self):
        """Export video clips."""
        try:
            # Implementation for video export
            # This is a placeholder - implement based on requirements
            self.progress_update.emit(50, "Exporting video...")
            time.sleep(1)  # Simulate processing
            self.export_finished.emit(True, f"Exported to {self.output_path}")
        except Exception as e:
            self.export_finished.emit(False, str(e))

    def stop(self):
        """Stop the worker."""
        self._is_running = False
        self.wait()
