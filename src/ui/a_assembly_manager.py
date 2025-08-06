# a_assembly_manager.py
"""
Assembly Manager for SYNAIPTIC Research Platform
Manages assembly creation, storage, and database operations with GUID-based file organization
"""

import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from a_database_models import DatabaseConfig, create_database_engine, Assembly, Base

logger = logging.getLogger(__name__)


class AssemblyManager:
    """
    Manages research assemblies with database storage and GUID-based file organization

    Storage Structure:
    STORAGE_ROOT/
    ├── assemblies/
    │   ├── {guid}/
    │   │   ├── assembly.asmb
    │   │   ├── documents/
    │   │   ├── annotations/
    │   │   └── ai_conversations/
    ├── config/
    └── database/
    """

    EXTENSION = ".asmb"
    VERSION = "1.0"

    def __init__(self, storage_root: Path = None, database_config: DatabaseConfig = None):
        """
        Initialize Assembly Manager

        Args:
            storage_root: Root directory for all assembly storage
            database_config: Database configuration
        """
        # Set up storage root
        if storage_root is None:
            storage_root = self._get_default_storage_root()

        self.storage_root = Path(storage_root)
        self.assemblies_root = self.storage_root / "assemblies"
        self.config_root = self.storage_root / "config"
        self.database_root = self.storage_root / "database"

        # Create directory structure
        self.assemblies_root.mkdir(parents=True, exist_ok=True)
        self.config_root.mkdir(parents=True, exist_ok=True)
        self.database_root.mkdir(parents=True, exist_ok=True)

        # Set up database
        if database_config is None:
            database_config = DatabaseConfig(
                db_type='sqlite',
                path=str(self.database_root / 'synaiptic.db')
            )

        self.database_config = database_config
        self.engine = create_database_engine(database_config)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)

        logger.info(f"✅ Assembly Manager initialized")
        logger.info(f"   Storage root: {self.storage_root}")
        logger.info(f"   Database: {database_config.get_database_url()}")

    def _get_default_storage_root(self) -> Path:
        """Get platform-appropriate default storage location"""
        if os.name == 'nt':  # Windows
            storage_root = Path.home() / "AppData" / "Local" / "SYNAIPTIC"
        elif os.name == 'posix':  # macOS/Linux
            if Path.home() / "Library" / "Application Support":  # macOS
                storage_root = Path.home() / "Library" / "Application Support" / "SYNAIPTIC"
            else:  # Linux
                storage_root = Path.home() / ".synaiptic"
        else:
            storage_root = Path.home() / ".synaiptic"

        return storage_root

    def create_assembly(self, assembly_data: Dict[str, Any]) -> Tuple[int, str, Path]:
        """
        Create a new research assembly

        Args:
            assembly_data: Assembly information from dialog

        Returns:
            Tuple of (assembly_id, assembly_guid, assembly_path)
        """
        session = self.Session()

        try:
            # Validate assembly name is unique
            assembly_name = assembly_data["name"].strip()
            if self.is_assembly_name_duplicate(assembly_name):
                raise ValueError(f"Assembly name '{assembly_name}' already exists. Please choose a different name.")

            # Generate GUID if not provided
            assembly_guid = assembly_data.get("guid", str(uuid.uuid4()))

            # Create database record
            assembly = Assembly(
                name=assembly_data["name"],
                description=assembly_data.get("description", ""),
                settings={
                    "research_type": assembly_data.get("research_type", "General Research"),
                    "researcher": assembly_data.get("researcher", ""),
                    "keywords": assembly_data.get("keywords", ""),
                    "ai_provider": assembly_data.get("ai_provider", "GPT-4 (OpenAI)"),
                    "guid": assembly_guid,
                    "version": self.VERSION
                }
            )

            session.add(assembly)
            session.commit()

            assembly_id = assembly.id

            # Create file system structure
            assembly_path = self.assemblies_root / assembly_guid
            assembly_path.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (assembly_path / "documents").mkdir(exist_ok=True)
            (assembly_path / "annotations").mkdir(exist_ok=True)
            (assembly_path / "ai_conversations").mkdir(exist_ok=True)

            # Create assembly metadata file
            assembly_file = assembly_path / f"assembly{self.EXTENSION}"
            self._save_assembly_metadata(assembly_file, assembly_data, assembly_id)

            logger.info(f"✅ Created assembly: {assembly_data['name']} (ID: {assembly_id}, GUID: {assembly_guid})")

            return assembly_id, assembly_guid, assembly_path

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Database error creating assembly: {e}")
            raise Exception(f"Failed to create assembly in database: {e}")
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error creating assembly: {e}")
            raise
        finally:
            session.close()

    def _save_assembly_metadata(self, assembly_file: Path, assembly_data: Dict[str, Any], assembly_id: int):
        """Save assembly metadata to .asmb file"""
        metadata = {
            "format_version": self.VERSION,
            "assembly_id": assembly_id,
            "assembly_info": {
                "name": assembly_data["name"],
                "guid": assembly_data.get("guid"),
                "research_type": assembly_data.get("research_type", ""),
                "researcher": assembly_data.get("researcher", ""),
                "description": assembly_data.get("description", ""),
                "keywords": assembly_data.get("keywords", ""),
                "ai_provider": assembly_data.get("ai_provider", ""),
                "created_date": datetime.now().isoformat(),
                "modified_date": datetime.now().isoformat()
            },
            "document_count": 0,
            "annotation_count": 0,
            "ai_conversation_count": 0,
            "storage_info": {
                "documents_path": "documents/",
                "annotations_path": "annotations/",
                "ai_conversations_path": "ai_conversations/"
            }
        }

        with open(assembly_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def get_all_assemblies(self) -> List[Dict[str, Any]]:
        """Get all assemblies from database"""
        session = self.Session()

        try:
            assemblies = session.query(Assembly).order_by(Assembly.updated_at.desc()).all()

            assembly_list = []
            for assembly in assemblies:
                settings = assembly.settings or {}

                assembly_data = {
                    "id": assembly.id,
                    "name": assembly.name,
                    "description": assembly.description,
                    "created_at": assembly.created_at.isoformat() if assembly.created_at else None,
                    "updated_at": assembly.updated_at.isoformat() if assembly.updated_at else None,
                    "document_count": len(assembly.documents),
                    "guid": settings.get("guid"),
                    "research_type": settings.get("research_type", "General Research"),
                    "researcher": settings.get("researcher", ""),
                    "keywords": settings.get("keywords", ""),
                    "ai_provider": settings.get("ai_provider", "")
                }

                assembly_list.append(assembly_data)

            return assembly_list

        except SQLAlchemyError as e:
            logger.error(f"❌ Error fetching assemblies: {e}")
            return []
        finally:
            session.close()

    def get_assembly_by_id(self, assembly_id: int) -> Optional[Dict[str, Any]]:
        """Get specific assembly by ID"""
        session = self.Session()

        try:
            assembly = session.query(Assembly).filter(Assembly.id == assembly_id).first()

            if not assembly:
                return None

            settings = assembly.settings or {}

            return {
                "id": assembly.id,
                "name": assembly.name,
                "description": assembly.description,
                "created_at": assembly.created_at.isoformat() if assembly.created_at else None,
                "updated_at": assembly.updated_at.isoformat() if assembly.updated_at else None,
                "document_count": len(assembly.documents),
                "guid": settings.get("guid"),
                "research_type": settings.get("research_type", "General Research"),
                "researcher": settings.get("researcher", ""),
                "keywords": settings.get("keywords", ""),
                "ai_provider": settings.get("ai_provider", ""),
                "settings": settings
            }

        except SQLAlchemyError as e:
            logger.error(f"❌ Error fetching assembly {assembly_id}: {e}")
            return None
        finally:
            session.close()

    def update_assembly(self, assembly_id: int, updates: Dict[str, Any]) -> bool:
        """Update assembly information"""
        session = self.Session()

        try:
            assembly = session.query(Assembly).filter(Assembly.id == assembly_id).first()

            if not assembly:
                logger.error(f"❌ Assembly {assembly_id} not found")
                return False

            # Check for name conflicts if name is being updated
            if "name" in updates:
                new_name = updates["name"].strip()
                if new_name != assembly.name and self.is_assembly_name_duplicate(new_name, assembly_id):
                    raise ValueError(f"Assembly name '{new_name}' already exists. Please choose a different name.")
                assembly.name = new_name

            # Update description
            if "description" in updates:
                assembly.description = updates["description"]

            # Update settings
            settings = assembly.settings or {}
            for key in ["researcher", "keywords", "ai_provider"]:
                if key in updates:
                    settings[key] = updates[key]

            assembly.settings = settings
            assembly.updated_at = datetime.utcnow()

            session.commit()

            # Update metadata file if it exists
            assembly_guid = settings.get("guid")
            if assembly_guid:
                assembly_path = self.assemblies_root / assembly_guid
                assembly_file = assembly_path / f"assembly{self.EXTENSION}"
                if assembly_file.exists():
                    self._update_assembly_metadata_file(assembly_file, assembly)

            logger.info(f"✅ Updated assembly {assembly_id}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Error updating assembly {assembly_id}: {e}")
            return False
        finally:
            session.close()

    def _update_assembly_metadata_file(self, assembly_file: Path, assembly: Assembly):
        """Update the .asmb metadata file"""
        try:
            with open(assembly_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Update metadata
            metadata["assembly_info"]["name"] = assembly.name
            metadata["assembly_info"]["description"] = assembly.description
            metadata["assembly_info"]["modified_date"] = datetime.now().isoformat()

            settings = assembly.settings or {}
            metadata["assembly_info"]["researcher"] = settings.get("researcher", "")
            metadata["assembly_info"]["keywords"] = settings.get("keywords", "")
            metadata["assembly_info"]["ai_provider"] = settings.get("ai_provider", "")

            with open(assembly_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"⚠️ Failed to update metadata file {assembly_file}: {e}")

    def delete_assembly(self, assembly_id: int) -> bool:
        """Delete an assembly and all its data"""
        session = self.Session()

        try:
            assembly = session.query(Assembly).filter(Assembly.id == assembly_id).first()

            if not assembly:
                logger.error(f"❌ Assembly {assembly_id} not found")
                return False

            # Get GUID for file system cleanup
            settings = assembly.settings or {}
            assembly_guid = settings.get("guid")

            # Delete from database (cascade will handle related records)
            session.delete(assembly)
            session.commit()

            # Delete file system directory
            if assembly_guid:
                assembly_path = self.assemblies_root / assembly_guid
                if assembly_path.exists():
                    import shutil
                    shutil.rmtree(assembly_path)
                    logger.info(f"🗑️ Deleted assembly directory: {assembly_path}")

            logger.info(f"✅ Deleted assembly {assembly_id}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Error deleting assembly {assembly_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting assembly files: {e}")
            return False
        finally:
            session.close()

    def get_assembly_path(self, assembly_id: int) -> Optional[Path]:
        """Get the file system path for an assembly"""
        assembly_data = self.get_assembly_by_id(assembly_id)
        if not assembly_data:
            return None

        assembly_guid = assembly_data.get("guid")
        if not assembly_guid:
            return None

        return self.assemblies_root / assembly_guid

    def get_recent_assemblies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently updated assemblies"""
        session = self.Session()

        try:
            assemblies = (
                session.query(Assembly)
                .order_by(Assembly.updated_at.desc())
                .limit(limit)
                .all()
            )

            recent_list = []
            for assembly in assemblies:
                settings = assembly.settings or {}

                recent_list.append({
                    "id": assembly.id,
                    "name": assembly.name,
                    "description": assembly.description,
                    "updated_at": assembly.updated_at.isoformat() if assembly.updated_at else None,
                    "document_count": len(assembly.documents),
                    "research_type": settings.get("research_type", "General Research")
                })

            return recent_list

        except SQLAlchemyError as e:
            logger.error(f"❌ Error fetching recent assemblies: {e}")
            return []
        finally:
            session.close()

    def is_assembly_name_duplicate(self, name: str, exclude_assembly_id: int = None) -> bool:
        """
        Check if assembly name already exists (case-insensitive)

        Args:
            name: Assembly name to check
            exclude_assembly_id: Assembly ID to exclude from check (for updates)

        Returns:
            True if name is duplicate, False otherwise
        """
        session = self.Session()

        try:
            query = session.query(Assembly).filter(Assembly.name.ilike(name.strip()))

            if exclude_assembly_id:
                query = query.filter(Assembly.id != exclude_assembly_id)

            existing_assembly = query.first()
            return existing_assembly is not None

        except SQLAlchemyError as e:
            logger.error(f"❌ Error checking assembly name duplicate: {e}")
            return False
        finally:
            session.close()

    def generate_unique_assembly_name(self, base_name: str) -> str:
        """
        Generate a unique assembly name by appending numbers if needed

        Args:
            base_name: Base name to make unique

        Returns:
            Unique assembly name
        """
        base_name = base_name.strip()

        # Try the base name first
        if not self.is_assembly_name_duplicate(base_name):
            return base_name

        # Try numbered versions
        counter = 2
        while counter <= 1000:  # Safety limit
            candidate = f"{base_name} ({counter})"
            if not self.is_assembly_name_duplicate(candidate):
                return candidate
            counter += 1

        # Fallback with timestamp
        import time
        timestamp = int(time.time() * 1000) % 100000
        return f"{base_name} ({timestamp})"

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information and statistics"""
        try:
            # Count assemblies
            session = self.Session()
            assembly_count = session.query(Assembly).count()
            session.close()

            # Calculate storage usage
            total_size = 0
            if self.storage_root.exists():
                for item in self.storage_root.rglob('*'):
                    if item.is_file():
                        total_size += item.stat().st_size

            return {
                "storage_root": str(self.storage_root),
                "assemblies_count": assembly_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "database_path": str(self.database_root / 'synaiptic.db')
            }

        except Exception as e:
            logger.error(f"❌ Error getting storage info: {e}")
            return {
                "storage_root": str(self.storage_root),
                "assemblies_count": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "database_path": "Error"
            }