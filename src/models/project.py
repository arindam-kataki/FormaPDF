import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class ProjectInfo:
    """Project information structure"""
    name: str
    pdf_path: str
    created_date: str
    modified_date: str
    version: str = "1.0"
    author: str = ""
    description: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ProjectManager:
    """Manages .fpdf project files and recent projects"""

    EXTENSION = ".fpdf"
    VERSION = "1.0"
    MAX_RECENT_PROJECTS = 10

    def __init__(self, config_dir: Path = None):
        """Initialize project manager

        Args:
            config_dir: Directory to store configuration and recent projects
        """
        if config_dir is None:
            # Default to user's app data directory
            if os.name == 'nt':  # Windows
                config_dir = Path.home() / "AppData" / "Local" / "PDFVoiceEditor"
            else:  # macOS/Linux
                config_dir = Path.home() / ".pdf_voice_editor"

        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.recent_projects_file = self.config_dir / "recent_projects.json"

    def create_project(self, pdf_path: str, project_path: str = None,
                       project_info: ProjectInfo = None) -> str:
        """Create a new project file

        Args:
            pdf_path: Path to the PDF file
            project_path: Where to save the project file (optional)
            project_info: Project metadata (optional)

        Returns:
            Path to the created project file
        """
        pdf_path = Path(pdf_path).resolve()

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Generate project path if not provided
        if project_path is None:
            project_name = pdf_path.stem
            project_path = pdf_path.parent / f"{project_name}{self.EXTENSION}"
        else:
            project_path = Path(project_path)
            if not project_path.suffix:
                project_path = project_path.with_suffix(self.EXTENSION)

        # Create project info if not provided
        if project_info is None:
            project_info = ProjectInfo(
                name=pdf_path.stem,
                pdf_path=str(pdf_path),
                created_date=datetime.now().isoformat(),
                modified_date=datetime.now().isoformat()
            )

        # Create project data structure
        project_data = {
            "format_version": self.VERSION,
            "project_info": asdict(project_info),
            "pdf_reference": {
                "path": str(pdf_path),
                "filename": pdf_path.name,
                "size_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
                "modified_date": datetime.fromtimestamp(
                    pdf_path.stat().st_mtime
                ).isoformat() if pdf_path.exists() else None
            },
            "form_data": {},
            "voice_commands": [],
            "field_definitions": [],
            "annotations": [],
            "user_preferences": {
                "zoom_level": 100,
                "current_page": 1,
                "view_mode": "single_page",
                "show_grid": False,
                "voice_enabled": False
            },
            "history": {
                "created": datetime.now().isoformat(),
                "last_opened": datetime.now().isoformat(),
                "save_count": 1,
                "total_edits": 0
            }
        }

        # Save project file
        self._save_project_file(project_path, project_data)

        # Add to recent projects
        self.add_to_recent(str(project_path))

        return str(project_path)

    def open_project(self, project_path: str) -> Dict[str, Any]:
        """Open an existing project file

        Args:
            project_path: Path to the project file

        Returns:
            Project data dictionary
        """
        project_path = Path(project_path)

        if not project_path.exists():
            raise FileNotFoundError(f"Project file not found: {project_path}")

        if project_path.suffix != self.EXTENSION:
            raise ValueError(f"Invalid project file extension. Expected {self.EXTENSION}")

        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid project file format: {e}")

        # Validate project format
        if not self._validate_project_data(project_data):
            raise ValueError("Invalid project file structure")

        # Update last opened time
        project_data["history"]["last_opened"] = datetime.now().isoformat()
        self._save_project_file(project_path, project_data)

        # Add to recent projects
        self.add_to_recent(str(project_path))

        return project_data

    def save_project(self, project_path: str, project_data: Dict[str, Any]) -> None:
        """Save project data to file

        Args:
            project_path: Path to the project file
            project_data: Project data to save
        """
        # Update modification time and save count
        project_data["project_info"]["modified_date"] = datetime.now().isoformat()
        project_data["history"]["save_count"] = project_data["history"].get("save_count", 0) + 1

        self._save_project_file(project_path, project_data)

    def get_recent_projects(self) -> List[Dict[str, str]]:
        """Get list of recent projects

        Returns:
            List of recent project info dictionaries
        """
        if not self.recent_projects_file.exists():
            return []

        try:
            with open(self.recent_projects_file, 'r', encoding='utf-8') as f:
                recent_data = json.load(f)

            # Filter out non-existent files
            valid_projects = []
            for project in recent_data.get("projects", []):
                if Path(project["path"]).exists():
                    valid_projects.append(project)

            # Update the file if we removed any invalid entries
            if len(valid_projects) != len(recent_data.get("projects", [])):
                self._save_recent_projects(valid_projects)

            return valid_projects

        except (json.JSONDecodeError, KeyError):
            return []

    def add_to_recent(self, project_path: str) -> None:
        """Add project to recent projects list

        Args:
            project_path: Path to the project file
        """
        project_path = Path(project_path).resolve()

        # Load existing recent projects
        recent_projects = self.get_recent_projects()

        # Remove if already exists (to move to top)
        recent_projects = [p for p in recent_projects if p["path"] != str(project_path)]

        # Get project info
        try:
            project_data = self.open_project(str(project_path))
            project_info = {
                "path": str(project_path),
                "name": project_data["project_info"]["name"],
                "pdf_path": project_data["pdf_reference"]["path"],
                "last_opened": datetime.now().isoformat(),
                "created": project_data["history"]["created"]
            }
        except Exception:
            # Fallback if we can't read the project file
            project_info = {
                "path": str(project_path),
                "name": project_path.stem,
                "pdf_path": "",
                "last_opened": datetime.now().isoformat(),
                "created": datetime.now().isoformat()
            }

        # Add to beginning of list
        recent_projects.insert(0, project_info)

        # Limit to max recent projects
        recent_projects = recent_projects[:self.MAX_RECENT_PROJECTS]

        # Save updated list
        self._save_recent_projects(recent_projects)

    def remove_from_recent(self, project_path: str) -> None:
        """Remove project from recent projects list

        Args:
            project_path: Path to the project file
        """
        recent_projects = self.get_recent_projects()
        recent_projects = [p for p in recent_projects if p["path"] != project_path]
        self._save_recent_projects(recent_projects)

    def clear_recent_projects(self) -> None:
        """Clear all recent projects"""
        self._save_recent_projects([])

    def _save_project_file(self, project_path: Path, project_data: Dict[str, Any]) -> None:
        """Save project data to file"""
        try:
            with open(project_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Failed to save project file: {e}")

    def _save_recent_projects(self, projects: List[Dict[str, str]]) -> None:
        """Save recent projects list to file"""
        recent_data = {
            "projects": projects,
            "last_updated": datetime.now().isoformat()
        }

        try:
            with open(self.recent_projects_file, 'w', encoding='utf-8') as f:
                json.dump(recent_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Fail silently for recent projects

    def _validate_project_data(self, project_data: Dict[str, Any]) -> bool:
        """Validate project data structure"""
        required_keys = [
            "format_version", "project_info", "pdf_reference",
            "form_data", "voice_commands", "field_definitions"
        ]

        return all(key in project_data for key in required_keys)

    @staticmethod
    def is_project_file(file_path: str) -> bool:
        """Check if file is a valid project file

        Args:
            file_path: Path to check

        Returns:
            True if file appears to be a valid project file
        """
        path = Path(file_path)

        if not path.exists() or path.suffix != ProjectManager.EXTENSION:
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Basic validation
            return (
                    "format_version" in data and
                    "project_info" in data and
                    "pdf_reference" in data
            )
        except (json.JSONDecodeError, IOError):
            return False