# a_assembly_manager.py
"""
Assembly Manager for PDF Research Platform
Handles assembly creation, loading, saving with PostgreSQL backend
"""

import os
import sys
import json
import uuid
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from sqlalchemy import create_engine, select, update, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Import database configuration and models
from a_database_config import DatabaseConfig
from a_database_models import (
    Base, Assembly, Document, Annotation, AIConversation,
    UserTOC, CrossReference, AssemblyNote, DocumentEmbedding
)

logger = logging.getLogger(__name__)


class AssemblyManager:
    """
    Manages research assemblies with PostgreSQL backend
    Handles creation, loading, saving, and document management
    """

    VERSION = "1.0.0"
    EXTENSION = ".asmb"

    def __init__(self):
        """Initialize Assembly Manager with PostgreSQL connection"""

        # Setup logging
        DatabaseConfig.setup_logging()

        # Get database URL from configuration
        self.database_url = DatabaseConfig.get_database_url()
        logger.info(f"Initializing AssemblyManager with {DatabaseConfig.DB_TYPE}")

        # Create engine with PostgreSQL optimizations
        self.engine = create_engine(
            self.database_url,
            **DatabaseConfig.get_engine_config()
        )

        # Ensure database and tables exist
        self._ensure_database()

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)

        # Setup file storage
        self.storage_root = DatabaseConfig.get_storage_path()
        self.assemblies_root = self.storage_root / "assemblies"
        self.assemblies_root.mkdir(parents=True, exist_ok=True)

        logger.info(f"Storage root: {self.storage_root}")
        logger.info(f"Database URL: {DatabaseConfig.get_database_url(include_password=False)}")

    def _ensure_database(self):
        """Ensure database and tables exist"""
        try:
            # Create database if needed (PostgreSQL)
            if DatabaseConfig.DB_TYPE == 'postgresql':
                DatabaseConfig.create_database_if_not_exists()

            # Create all tables
            Base.metadata.create_all(self.engine)
            logger.info("Database tables verified/created")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def create_assembly(self, assembly_data: Dict[str, Any]) -> Tuple[int, str, Path]:
        """
        Create a new research assembly and save immediately to PostgreSQL

        Args:
            assembly_data: Dictionary containing assembly metadata

        Returns:
            Tuple of (assembly_id, assembly_guid, assembly_path)
        """
        session = self.Session()

        try:
            # Generate unique GUID
            assembly_guid = str(uuid.uuid4())

            # Create database record - THIS SAVES TO POSTGRESQL IMMEDIATELY
            assembly = Assembly(
                guid=assembly_guid,
                name=assembly_data['name'],
                description=assembly_data.get('description', ''),
                researcher=assembly_data.get('researcher', ''),
                research_type=assembly_data.get('research_type', 'General Research'),
                keywords=assembly_data.get('keywords', []),
                settings={
                    'version': self.VERSION,
                    'created_with': 'SYNAIPLIC Research Platform',
                    'document_settings': assembly_data.get('document_settings', {}),
                    'annotation_settings': assembly_data.get('annotation_settings', {}),
                    'search_settings': assembly_data.get('search_settings', {}),
                },
                ai_config={
                    'provider': assembly_data.get('ai_provider', 'GPT-4 (OpenAI)'),
                    'features': assembly_data.get('ai_features', {}),
                    'api_key': assembly_data.get('api_key', ''),  # Should be encrypted in production
                }
            )

            # Save to PostgreSQL
            session.add(assembly)
            session.commit()
            session.refresh(assembly)  # Get the generated ID

            assembly_id = assembly.id
            logger.info(f"✅ Created assembly in PostgreSQL: ID={assembly_id}, GUID={assembly_guid}")

            # Create file system structure for document storage
            assembly_path = self.assemblies_root / assembly_guid
            assembly_path.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (assembly_path / "documents").mkdir(exist_ok=True)
            (assembly_path / "annotations").mkdir(exist_ok=True)
            (assembly_path / "ai_conversations").mkdir(exist_ok=True)
            (assembly_path / "exports").mkdir(exist_ok=True)
            (assembly_path / "thumbnails").mkdir(exist_ok=True)

            # Update assembly with storage path
            assembly.storage_path = str(assembly_path)
            session.commit()

            # Create assembly metadata file (for quick loading and backup)
            assembly_file = assembly_path / f"assembly{self.EXTENSION}"
            self._save_assembly_metadata(assembly_file, assembly_data, assembly_id, assembly_guid)

            logger.info(f"✅ Assembly created successfully: '{assembly_data['name']}' (ID: {assembly_id})")

            return assembly_id, assembly_guid, assembly_path

        except IntegrityError as e:
            session.rollback()
            logger.error(f"❌ Database integrity error: {e}")
            raise ValueError(f"Assembly creation failed - possible duplicate name: {e}")

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Database error creating assembly: {e}")
            raise Exception(f"Failed to create assembly in database: {e}")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Unexpected error creating assembly: {e}")
            raise

        finally:
            session.close()

    def _save_assembly_metadata(self, assembly_file: Path, assembly_data: Dict,
                                assembly_id: int, assembly_guid: str):
        """Save assembly metadata to .asmb file for quick loading"""
        metadata = {
            'format_version': self.VERSION,
            'assembly_id': assembly_id,
            'assembly_guid': assembly_guid,
            'name': assembly_data['name'],
            'description': assembly_data.get('description', ''),
            'researcher': assembly_data.get('researcher', ''),
            'research_type': assembly_data.get('research_type', 'General Research'),
            'keywords': assembly_data.get('keywords', []),
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'database_type': DatabaseConfig.DB_TYPE,
            'storage_settings': assembly_data.get('storage', {})
        }

        with open(assembly_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def load_assembly(self, assembly_path: str) -> Dict[str, Any]:
        """
        Load an existing assembly from database

        Args:
            assembly_path: Path to .asmb file or assembly GUID

        Returns:
            Assembly data dictionary
        """
        # Handle both file path and GUID
        if os.path.isfile(assembly_path):
            # Load metadata from file
            with open(assembly_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            assembly_id = metadata['assembly_id']
        else:
            # Assume it's an assembly ID or GUID
            assembly_id = assembly_path

        session = self.Session()

        try:
            # Load from PostgreSQL
            if isinstance(assembly_id, str) and '-' in assembly_id:
                # It's a GUID
                assembly = session.query(Assembly).filter_by(guid=assembly_id).first()
            else:
                # It's an ID
                assembly = session.query(Assembly).filter_by(id=int(assembly_id)).first()

            if not assembly:
                raise ValueError(f"Assembly not found: {assembly_id}")

            # Update last accessed time
            assembly.last_accessed = datetime.utcnow()
            session.commit()

            # Get documents
            documents = session.query(Document).filter_by(
                assembly_id=assembly.id
            ).order_by(Document.created_at).all()

            # Get assembly notes
            notes = session.query(AssemblyNote).filter_by(
                assembly_id=assembly.id
            ).order_by(AssemblyNote.created_at.desc()).all()

            # Build assembly data
            assembly_data = {
                'id': assembly.id,
                'guid': assembly.guid,
                'name': assembly.name,
                'description': assembly.description,
                'researcher': assembly.researcher,
                'research_type': assembly.research_type,
                'keywords': assembly.keywords or [],
                'settings': assembly.settings or {},
                'ai_config': assembly.ai_config or {},
                'created': assembly.created_at.isoformat(),
                'modified': assembly.updated_at.isoformat(),
                'last_accessed': assembly.last_accessed.isoformat(),
                'document_count': assembly.document_count,
                'annotation_count': assembly.annotation_count,
                'documents': [self._document_to_dict(doc) for doc in documents],
                'notes': [self._note_to_dict(note) for note in notes],
                'storage_path': assembly.storage_path,
                'is_active': assembly.is_active,
                'is_archived': assembly.is_archived
            }

            logger.info(f"✅ Loaded assembly: '{assembly.name}' (ID: {assembly.id}, {len(documents)} documents)")

            return assembly_data

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error loading assembly: {e}")
            raise Exception(f"Failed to load assembly from database: {e}")

        finally:
            session.close()

    def update_assembly(self, assembly_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update assembly metadata in PostgreSQL

        Args:
            assembly_id: Assembly ID
            updates: Dictionary of fields to update

        Returns:
            True if successful
        """
        session = self.Session()

        try:
            assembly = session.query(Assembly).filter_by(id=assembly_id).first()

            if not assembly:
                raise ValueError(f"Assembly not found: {assembly_id}")

            # Update allowed fields
            allowed_fields = ['name', 'description', 'researcher', 'research_type',
                              'keywords', 'settings', 'ai_config']

            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(assembly, field, value)

            # Update modified timestamp
            assembly.updated_at = datetime.utcnow()

            session.commit()

            # Update metadata file
            if assembly.storage_path:
                assembly_file = Path(assembly.storage_path) / f"assembly{self.EXTENSION}"
                if assembly_file.exists():
                    with open(assembly_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    metadata.update({
                        'name': assembly.name,
                        'description': assembly.description,
                        'researcher': assembly.researcher,
                        'research_type': assembly.research_type,
                        'keywords': assembly.keywords,
                        'modified': datetime.now().isoformat()
                    })

                    with open(assembly_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Updated assembly: {assembly_id}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Database error updating assembly: {e}")
            raise Exception(f"Failed to update assembly: {e}")

        finally:
            session.close()

    def add_document(self, assembly_id: int, file_path: str,
                     copy_to_assembly: bool = True) -> int:
        """
        Add a document to an assembly

        Args:
            assembly_id: Assembly ID
            file_path: Path to document file
            copy_to_assembly: Whether to copy file to assembly folder

        Returns:
            Document ID
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        session = self.Session()

        try:
            # Get assembly
            assembly = session.query(Assembly).filter_by(id=assembly_id).first()
            if not assembly:
                raise ValueError(f"Assembly not found: {assembly_id}")

            # Calculate file hash to check for duplicates
            file_hash = self._calculate_file_hash(file_path)

            # Check for duplicate
            existing = session.query(Document).filter_by(
                assembly_id=assembly_id,
                content_hash=file_hash
            ).first()

            if existing:
                logger.warning(f"Document already exists in assembly: {file_path.name}")
                return existing.id

            # Copy file to assembly if requested
            if copy_to_assembly and assembly.storage_path:
                docs_dir = Path(assembly.storage_path) / "documents"
                docs_dir.mkdir(exist_ok=True)

                dest_path = docs_dir / file_path.name

                # Handle name conflicts
                if dest_path.exists():
                    base = dest_path.stem
                    ext = dest_path.suffix
                    counter = 1
                    while dest_path.exists():
                        dest_path = docs_dir / f"{base}_{counter}{ext}"
                        counter += 1

                shutil.copy2(file_path, dest_path)
                stored_path = str(dest_path.relative_to(assembly.storage_path))
            else:
                stored_path = str(file_path.absolute())

            # Create document record
            document = Document(
                assembly_id=assembly_id,
                filename=file_path.name,
                original_filename=file_path.name,
                file_type=file_path.suffix[1:].lower() if file_path.suffix else 'unknown',
                file_path=stored_path,
                content_hash=file_hash,
                file_size=file_path.stat().st_size,
                page_count=self._get_page_count(file_path),
                document_metadata={
                    'added_date': datetime.now().isoformat(),
                    'original_path': str(file_path)
                }
            )

            session.add(document)

            # Update assembly document count
            assembly.document_count = session.query(Document).filter_by(
                assembly_id=assembly_id
            ).count() + 1
            assembly.total_size_bytes = (assembly.total_size_bytes or 0) + document.file_size
            assembly.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(document)

            logger.info(f"✅ Added document to assembly: {file_path.name} (ID: {document.id})")

            return document.id

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Database error adding document: {e}")
            raise Exception(f"Failed to add document: {e}")

        finally:
            session.close()

    def remove_document(self, document_id: int, delete_file: bool = False) -> bool:
        """
        Remove a document from the assembly

        Args:
            document_id: Document ID
            delete_file: Whether to delete the actual file

        Returns:
            True if successful
        """
        session = self.Session()

        try:
            document = session.query(Document).filter_by(id=document_id).first()

            if not document:
                raise ValueError(f"Document not found: {document_id}")

            assembly = document.assembly
            file_size = document.file_size

            # Delete file if requested
            if delete_file and document.file_path and assembly.storage_path:
                file_path = Path(assembly.storage_path) / document.file_path
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted file: {file_path}")

            # Delete document (cascades to annotations)
            session.delete(document)

            # Update assembly counts
            assembly.document_count = max(0, assembly.document_count - 1)
            assembly.total_size_bytes = max(0, (assembly.total_size_bytes or 0) - file_size)
            assembly.annotation_count = session.query(Annotation).join(Document).filter(
                Document.assembly_id == assembly.id
            ).count()
            assembly.updated_at = datetime.utcnow()

            session.commit()

            logger.info(f"✅ Removed document: {document_id}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Database error removing document: {e}")
            raise Exception(f"Failed to remove document: {e}")

        finally:
            session.close()

    def get_all_assemblies(self) -> List[Dict[str, Any]]:
        """
        Get all assemblies from database

        Returns:
            List of assembly dictionaries
        """
        session = self.Session()

        try:
            assemblies = session.query(Assembly).filter_by(
                is_active=True,
                is_archived=False
            ).order_by(Assembly.updated_at.desc()).all()

            result = []
            for assembly in assemblies:
                result.append({
                    'id': assembly.id,
                    'guid': assembly.guid,
                    'name': assembly.name,
                    'description': assembly.description,
                    'researcher': assembly.researcher,
                    'research_type': assembly.research_type,
                    'document_count': assembly.document_count,
                    'annotation_count': assembly.annotation_count,
                    'created': assembly.created_at.isoformat(),
                    'modified': assembly.updated_at.isoformat(),
                    'last_accessed': assembly.last_accessed.isoformat() if assembly.last_accessed else None,
                    'storage_path': assembly.storage_path
                })

            logger.info(f"Found {len(result)} assemblies")
            return result

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error getting assemblies: {e}")
            raise Exception(f"Failed to get assemblies: {e}")

        finally:
            session.close()

    def get_recent_assemblies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently accessed assemblies

        Args:
            limit: Maximum number of assemblies to return

        Returns:
            List of assembly dictionaries
        """
        session = self.Session()

        try:
            assemblies = session.query(Assembly).filter_by(
                is_active=True,
                is_archived=False
            ).order_by(Assembly.last_accessed.desc()).limit(limit).all()

            result = []
            for assembly in assemblies:
                result.append({
                    'id': assembly.id,
                    'guid': assembly.guid,
                    'name': assembly.name,
                    'description': assembly.description,
                    'document_count': assembly.document_count,
                    'modified': assembly.updated_at.isoformat(),
                    'last_accessed': assembly.last_accessed.isoformat() if assembly.last_accessed else None,
                    'path': str(self.assemblies_root / assembly.guid / f"assembly{self.EXTENSION}")
                })

            return result

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error getting recent assemblies: {e}")
            raise Exception(f"Failed to get recent assemblies: {e}")

        finally:
            session.close()

    def search_assemblies(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for assemblies by name, description, or keywords

        Args:
            query: Search query

        Returns:
            List of matching assembly dictionaries
        """
        session = self.Session()

        try:
            search_term = f"%{query}%"

            # Search in name, description, and researcher
            assemblies = session.query(Assembly).filter(
                and_(
                    Assembly.is_active == True,
                    Assembly.is_archived == False,
                    or_(
                        Assembly.name.ilike(search_term),
                        Assembly.description.ilike(search_term),
                        Assembly.researcher.ilike(search_term)
                    )
                )
            ).all()

            result = []
            for assembly in assemblies:
                result.append({
                    'id': assembly.id,
                    'guid': assembly.guid,
                    'name': assembly.name,
                    'description': assembly.description,
                    'researcher': assembly.researcher,
                    'document_count': assembly.document_count,
                    'modified': assembly.updated_at.isoformat()
                })

            logger.info(f"Search found {len(result)} assemblies matching '{query}'")
            return result

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error searching assemblies: {e}")
            raise Exception(f"Failed to search assemblies: {e}")

        finally:
            session.close()

    def archive_assembly(self, assembly_id: int) -> bool:
        """
        Archive an assembly (soft delete)

        Args:
            assembly_id: Assembly ID

        Returns:
            True if successful
        """
        session = self.Session()

        try:
            assembly = session.query(Assembly).filter_by(id=assembly_id).first()

            if not assembly:
                raise ValueError(f"Assembly not found: {assembly_id}")

            assembly.is_archived = True
            assembly.updated_at = datetime.utcnow()

            session.commit()

            logger.info(f"✅ Archived assembly: {assembly_id}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Database error archiving assembly: {e}")
            raise Exception(f"Failed to archive assembly: {e}")

        finally:
            session.close()

    def delete_assembly(self, assembly_id: int, delete_files: bool = False) -> bool:
        """
        Permanently delete an assembly

        Args:
            assembly_id: Assembly ID
            delete_files: Whether to delete associated files

        Returns:
            True if successful
        """
        session = self.Session()

        try:
            assembly = session.query(Assembly).filter_by(id=assembly_id).first()

            if not assembly:
                raise ValueError(f"Assembly not found: {assembly_id}")

            storage_path = assembly.storage_path

            # Delete from database (cascades to all related records)
            session.delete(assembly)
            session.commit()

            # Delete files if requested
            if delete_files and storage_path:
                storage_dir = Path(storage_path)
                if storage_dir.exists():
                    shutil.rmtree(storage_dir)
                    logger.info(f"Deleted assembly files: {storage_dir}")

            logger.info(f"✅ Permanently deleted assembly: {assembly_id}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Database error deleting assembly: {e}")
            raise Exception(f"Failed to delete assembly: {e}")

        finally:
            session.close()

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_page_count(self, file_path: Path) -> int:
        """Get page count for document"""
        # TODO: Implement actual page counting based on file type
        file_type = file_path.suffix.lower()

        if file_type == '.pdf':
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(str(file_path))
                page_count = len(doc)
                doc.close()
                return page_count
            except:
                return 0

        return 1  # Default for other file types

    def _document_to_dict(self, document: Document) -> Dict[str, Any]:
        """Convert document object to dictionary"""
        return {
            'id': document.id,
            'filename': document.filename,
            'file_type': document.file_type,
            'file_path': document.file_path,
            'file_size': document.file_size,
            'page_count': document.page_count,
            'annotation_count': document.annotation_count,
            'created': document.created_at.isoformat(),
            'modified': document.updated_at.isoformat(),
            'last_accessed': document.last_accessed.isoformat() if document.last_accessed else None,
            'metadata': document.document_metadata or {},
            'is_processed': document.is_processed,
            'is_indexed': document.is_indexed
        }

    def _note_to_dict(self, note: AssemblyNote) -> Dict[str, Any]:
        """Convert assembly note to dictionary"""
        return {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'note_type': note.note_type,
            'tags': note.tags or [],
            'priority': note.priority,
            'is_pinned': note.is_pinned,
            'created': note.created_at.isoformat(),
            'modified': note.updated_at.isoformat(),
            'created_by': note.created_by
        }

    def close(self):
        """Close manager and cleanup resources"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            logger.info("AssemblyManager closed")


# Utility functions for standalone use
def test_connection():
    """Test database connection"""
    success, message = DatabaseConfig.test_connection()
    print(f"{'✅' if success else '❌'} {message}")
    return success


def init_database():
    """Initialize database tables"""
    return DatabaseConfig.init_database()


if __name__ == "__main__":
    # Test the manager when run directly
    print("Testing AssemblyManager with PostgreSQL")
    print("=" * 50)

    # Test connection
    if not test_connection():
        print("Failed to connect to database. Check your configuration.")
        sys.exit(1)

    # Initialize database
    if init_database():
        print("✅ Database initialized successfully")

    # Create manager
    manager = AssemblyManager()

    # List existing assemblies
    assemblies = manager.get_all_assemblies()
    print(f"\nFound {len(assemblies)} existing assemblies:")
    for assembly in assemblies:
        print(f"  - {assembly['name']} (ID: {assembly['id']}, {assembly['document_count']} documents)")

    manager.close()