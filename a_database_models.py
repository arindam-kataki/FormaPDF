# a_database_models.py
"""
SQLAlchemy Models for PDF Research Platform
Defines the database schema that Alembic will manage
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import os

Base = declarative_base()


class Assembly(Base):
    __tablename__ = 'assemblies'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSON)  # Store assembly-specific settings

    # Relationships
    documents = relationship("Document", back_populates="assembly", cascade="all, delete-orphan")
    user_toc = relationship("UserTOC", back_populates="assembly", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assembly(id={self.id}, name='{self.name}')>"


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    assembly_id = Column(Integer, ForeignKey('assemblies.id'), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500))  # Original name before any processing
    file_type = Column(String(50), nullable=False)  # pdf, docx, xlsx, etc.
    file_path = Column(String(1000))  # Relative path to stored file
    content_hash = Column(String(64))  # SHA-256 hash for duplicate detection
    file_size = Column(Integer)  # File size in bytes
    page_count = Column(Integer)  # Number of pages/sheets
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    document_metadata = Column(JSON)  # Store document-specific metadata

    # Relationships
    assembly = relationship("Assembly", back_populates="documents")
    annotations = relationship("Annotation", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.file_type}')>"


class Annotation(Base):
    __tablename__ = 'annotations'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    page_number = Column(Integer, nullable=False, default=1)

    # Coordinate system (normalized 0-1 for different document types)
    x1 = Column(Float)  # Left boundary
    y1 = Column(Float)  # Top boundary
    x2 = Column(Float)  # Right boundary
    y2 = Column(Float)  # Bottom boundary

    selected_text = Column(Text)  # The text that was selected
    annotation_text = Column(Text)  # User's annotation/note
    annotation_type = Column(String(50), default='note')  # note, question, insight, highlight

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Visual properties
    color = Column(String(7), default='#ffff00')  # Hex color code
    opacity = Column(Float, default=0.3)

    # Relationships
    document = relationship("Document", back_populates="annotations")
    ai_conversations = relationship("AIConversation", back_populates="annotation", cascade="all, delete-orphan")
    source_references = relationship("CrossReference", foreign_keys="[CrossReference.source_annotation_id]",
                                     back_populates="source_annotation")
    target_references = relationship("CrossReference", foreign_keys="[CrossReference.target_annotation_id]",
                                     back_populates="target_annotation")

    def __repr__(self):
        return f"<Annotation(id={self.id}, type='{self.annotation_type}', page={self.page_number})>"


class AIConversation(Base):
    __tablename__ = 'ai_conversations'

    id = Column(Integer, primary_key=True)
    annotation_id = Column(Integer, ForeignKey('annotations.id'), nullable=False)

    # Conversation data
    conversation_data = Column(JSON)  # Store full conversation history
    ai_provider = Column(String(50))  # openai, anthropic, local, etc.
    model_name = Column(String(100))  # gpt-4, claude-3, etc.

    # Usage tracking
    token_count = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    annotation = relationship("Annotation", back_populates="ai_conversations")

    def __repr__(self):
        return f"<AIConversation(id={self.id}, provider='{self.ai_provider}', tokens={self.token_count})>"


class UserTOC(Base):
    __tablename__ = 'user_toc'

    id = Column(Integer, primary_key=True)
    assembly_id = Column(Integer, ForeignKey('assemblies.id'), nullable=False)

    title = Column(String(500), nullable=False)
    description = Column(Text)

    # Navigation target
    document_id = Column(Integer, ForeignKey('documents.id'))
    page_number = Column(Integer)
    annotation_id = Column(Integer, ForeignKey('annotations.id'))  # Link to specific annotation

    # Hierarchy
    parent_id = Column(Integer, ForeignKey('user_toc.id'))
    order_index = Column(Integer, default=0)  # For ordering within same level

    toc_type = Column(String(50), default='section')  # section, milestone, reference, etc.

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assembly = relationship("Assembly", back_populates="user_toc")
    document = relationship("Document")
    annotation = relationship("Annotation")
    parent = relationship("UserTOC", remote_side=[id])
    children = relationship("UserTOC", back_populates="parent")

    def __repr__(self):
        return f"<UserTOC(id={self.id}, title='{self.title}', type='{self.toc_type}')>"


class CrossReference(Base):
    __tablename__ = 'cross_references'

    id = Column(Integer, primary_key=True)
    source_annotation_id = Column(Integer, ForeignKey('annotations.id'), nullable=False)
    target_annotation_id = Column(Integer, ForeignKey('annotations.id'), nullable=False)

    reference_type = Column(String(50), default='related')  # related, contradicts, supports, etc.
    reference_note = Column(Text)  # Optional explanation of the relationship

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_annotation = relationship("Annotation", foreign_keys=[source_annotation_id],
                                     back_populates="source_references")
    target_annotation = relationship("Annotation", foreign_keys=[target_annotation_id],
                                     back_populates="target_references")

    def __repr__(self):
        return f"<CrossReference(id={self.id}, type='{self.reference_type}')>"


# Database Configuration and Helper Functions
class DatabaseConfig:
    """Database configuration management"""

    def __init__(self, db_type='sqlite', **kwargs):
        self.db_type = db_type
        self.config = kwargs

    def get_database_url(self):
        """Get SQLAlchemy database URL"""
        if self.db_type == 'sqlite':
            db_path = self.config.get('path', 'data/projects.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return f"sqlite:///{db_path}"

        elif self.db_type == 'postgresql':
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 5432)
            database = self.config.get('database', 'synaiptic')
            username = self.config.get('username')
            password = self.config.get('password')

            if not username or not password:
                raise ValueError("PostgreSQL requires username and password")

            return f"postgresql://{username}:{password}@{host}:{port}/{database}"

        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")


def create_database_engine(config: DatabaseConfig):
    """Create SQLAlchemy engine with proper configuration"""
    database_url = config.get_database_url()

    if config.db_type == 'sqlite':
        # SQLite-specific configuration
        engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            connect_args={"check_same_thread": False}
        )

    elif config.db_type == 'postgresql':
        # PostgreSQL-specific configuration
        engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )

    return engine


def create_session_factory(engine):
    """Create sessionmaker for database operations"""
    return sessionmaker(bind=engine)


# Migration and initialization helpers
def init_database(config: DatabaseConfig):
    """Initialize database with all tables"""
    engine = create_database_engine(config)

    # Create all tables
    Base.metadata.create_all(engine)

    print(f"✅ Database initialized with {config.db_type}")
    return engine


if __name__ == "__main__":
    # Example usage
    config = DatabaseConfig(db_type='sqlite', path='data/test_synaiptic.db')
    engine = init_database(config)

    # Test session
    Session = create_session_factory(engine)
    session = Session()

    # Create a test assembly
    assembly = Assembly(name="Test Assembly", description="A test assembly for SYNAIPTIC migrations")
    session.add(assembly)
    session.commit()

    print(f"Created test assembly: {assembly}")
    session.close()