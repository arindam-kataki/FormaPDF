# a_database_models.py
"""
SQLAlchemy Models for PDF Research Platform
PostgreSQL-optimized schema with proper relationships and indexes
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, JSON, Float, Index, UniqueConstraint,
    CheckConstraint, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates, backref
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from datetime import datetime
import uuid

Base = declarative_base()


class Assembly(Base):
    """Research assembly - main container for documents and research"""
    __tablename__ = 'assemblies'

    # Primary key and unique identifier
    id = Column(Integer, primary_key=True, autoincrement=True)
    guid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    researcher = Column(String(255))
    research_type = Column(String(100), default='General Research')

    # Keywords as array (PostgreSQL specific, falls back to JSON for SQLite)
    keywords = Column(ARRAY(String), default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())

    # Settings and configuration (JSONB for PostgreSQL, JSON for SQLite)
    settings = Column(JSONB, default=dict)
    ai_config = Column(JSONB, default=dict)

    # Status and counts (denormalized for performance)
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    document_count = Column(Integer, default=0, nullable=False)
    annotation_count = Column(Integer, default=0, nullable=False)
    ai_conversation_count = Column(Integer, default=0, nullable=False)

    # Storage information
    storage_path = Column(String(500))
    total_size_bytes = Column(Integer, default=0)

    # Relationships
    documents = relationship(
        "Document",
        back_populates="assembly",
        cascade="all, delete-orphan",
        order_by="Document.created_at"
    )
    user_toc_entries = relationship(
        "UserTOC",
        back_populates="assembly",
        cascade="all, delete-orphan"
    )
    assembly_notes = relationship(
        "AssemblyNote",
        back_populates="assembly",
        cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index('idx_assembly_guid', 'guid'),
        Index('idx_assembly_researcher', 'researcher'),
        Index('idx_assembly_created', 'created_at'),
        Index('idx_assembly_active', 'is_active', 'is_archived'),
    )

    def __repr__(self):
        return f"<Assembly(id={self.id}, name='{self.name}', documents={self.document_count})>"

    @validates('name')
    def validate_name(self, key, value):
        """Validate assembly name"""
        if not value or not value.strip():
            raise ValueError("Assembly name cannot be empty")
        return value.strip()


class Document(Base):
    """Document within an assembly"""
    __tablename__ = 'documents'

    # Primary key and foreign key
    id = Column(Integer, primary_key=True, autoincrement=True)
    assembly_id = Column(Integer, ForeignKey('assemblies.id', ondelete='CASCADE'), nullable=False)

    # File information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500))
    file_type = Column(String(50), nullable=False)  # pdf, docx, xlsx, etc.
    file_path = Column(String(1000))  # Relative path within assembly

    # File metadata
    content_hash = Column(String(64), index=True)  # SHA-256 hash
    file_size = Column(Integer, default=0)  # Size in bytes
    page_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())

    # Document metadata (JSONB for PostgreSQL)
    document_metadata = Column('metadata', JSONB, default=dict)  # Column name in DB is still 'metadata'
    extracted_text = Column(Text)  # Full text for search

    # Processing status
    is_processed = Column(Boolean, default=False)
    is_ocr_complete = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    processing_errors = Column(JSONB, default=list)

    # Statistics (denormalized)
    annotation_count = Column(Integer, default=0)

    # Relationships
    assembly = relationship("Assembly", back_populates="documents")
    annotations = relationship(
        "Annotation",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Annotation.page_number, Annotation.y1"
    )

    # Indexes
    __table_args__ = (
        Index('idx_document_assembly', 'assembly_id'),
        Index('idx_document_hash', 'content_hash'),
        Index('idx_document_type', 'file_type'),
        UniqueConstraint('assembly_id', 'content_hash', name='uq_assembly_document_hash'),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.file_type}')>"


class Annotation(Base):
    """Annotation on a document"""
    __tablename__ = 'annotations'

    # Primary key and foreign key
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)

    # Location in document
    page_number = Column(Integer, nullable=False, default=1)

    # Coordinates (normalized 0-1 for portability across different renderings)
    x1 = Column(Float, nullable=False)  # Left
    y1 = Column(Float, nullable=False)  # Top
    x2 = Column(Float, nullable=False)  # Right
    y2 = Column(Float, nullable=False)  # Bottom

    # Content
    selected_text = Column(Text)
    annotation_text = Column(Text)
    annotation_type = Column(String(50), default='highlight')  # highlight, note, question, insight

    # Visual properties
    color = Column(String(7), default='#ffff00')  # Hex color
    opacity = Column(Float, default=0.3)

    # Metadata
    tags = Column(ARRAY(String), default=list)
    is_resolved = Column(Boolean, default=False)
    priority = Column(Integer, default=0)  # 0=normal, 1=high, 2=critical

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255))  # User who created it

    # Relationships
    document = relationship("Document", back_populates="annotations")
    ai_conversations = relationship(
        "AIConversation",
        back_populates="annotation",
        cascade="all, delete-orphan"
    )
    cross_references_from = relationship(
        "CrossReference",
        foreign_keys="CrossReference.source_annotation_id",
        back_populates="source_annotation",
        cascade="all, delete-orphan"
    )
    cross_references_to = relationship(
        "CrossReference",
        foreign_keys="CrossReference.target_annotation_id",
        back_populates="target_annotation"
    )

    # Indexes
    __table_args__ = (
        Index('idx_annotation_document', 'document_id'),
        Index('idx_annotation_page', 'document_id', 'page_number'),
        Index('idx_annotation_type', 'annotation_type'),
        Index('idx_annotation_created', 'created_at'),
        CheckConstraint('x1 >= 0 AND x1 <= 1', name='check_x1_bounds'),
        CheckConstraint('y1 >= 0 AND y1 <= 1', name='check_y1_bounds'),
        CheckConstraint('x2 >= 0 AND x2 <= 1', name='check_x2_bounds'),
        CheckConstraint('y2 >= 0 AND y2 <= 1', name='check_y2_bounds'),
        CheckConstraint('x2 > x1', name='check_x_order'),
        CheckConstraint('y2 > y1', name='check_y_order'),
    )

    def __repr__(self):
        return f"<Annotation(id={self.id}, type='{self.annotation_type}', page={self.page_number})>"


class AIConversation(Base):
    """AI conversation linked to an annotation"""
    __tablename__ = 'ai_conversations'

    # Primary key and foreign key
    id = Column(Integer, primary_key=True, autoincrement=True)
    annotation_id = Column(Integer, ForeignKey('annotations.id', ondelete='CASCADE'), nullable=False)

    # Conversation data
    messages = Column(JSONB, nullable=False, default=list)  # List of message objects
    context = Column(Text)  # Context provided to AI

    # AI provider information
    ai_provider = Column(String(50), nullable=False)  # openai, anthropic, local
    model_name = Column(String(100))  # gpt-4, claude-3, etc.
    model_parameters = Column(JSONB, default=dict)  # Temperature, max_tokens, etc.

    # Usage tracking
    total_tokens = Column(Integer, default=0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)  # Estimated cost in USD

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Summary and insights
    summary = Column(Text)
    key_insights = Column(JSONB, default=list)

    # Relationships
    annotation = relationship("Annotation", back_populates="ai_conversations")

    # Indexes
    __table_args__ = (
        Index('idx_ai_conversation_annotation', 'annotation_id'),
        Index('idx_ai_conversation_provider', 'ai_provider'),
        Index('idx_ai_conversation_created', 'created_at'),
    )

    def __repr__(self):
        return f"<AIConversation(id={self.id}, provider='{self.ai_provider}', tokens={self.total_tokens})>"


class UserTOC(Base):
    """User-created table of contents for an assembly"""
    __tablename__ = 'user_toc'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    assembly_id = Column(Integer, ForeignKey('assemblies.id', ondelete='CASCADE'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'))
    parent_id = Column(Integer, ForeignKey('user_toc.id', ondelete='CASCADE'))

    # TOC entry information
    title = Column(String(500), nullable=False)
    page_number = Column(Integer)
    section_number = Column(String(50))  # 1.2.3 style numbering
    level = Column(Integer, default=1)  # Heading level (1-6)

    # Navigation and ordering
    order_index = Column(Integer, nullable=False, default=0)

    # Entry type
    entry_type = Column(String(50), default='section')  # section, bookmark, note

    # Metadata
    notes = Column(Text)
    color = Column(String(7))  # Hex color for visual organization

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - FIXED self-referential relationship
    assembly = relationship("Assembly", back_populates="user_toc_entries")
    document = relationship("Document")

    # Self-referential relationship with proper configuration
    children = relationship(
        "UserTOC",
        backref=backref('parent', remote_side=[id]),
        cascade="all, delete-orphan",
        foreign_keys=[parent_id]
    )

    # Indexes
    __table_args__ = (
        Index('idx_toc_assembly', 'assembly_id'),
        Index('idx_toc_document', 'document_id'),
        Index('idx_toc_order', 'assembly_id', 'order_index'),
    )

    def __repr__(self):
        return f"<UserTOC(id={self.id}, title='{self.title}', level={self.level})>"

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'assembly_id': self.assembly_id,
            'document_id': self.document_id,
            'parent_id': self.parent_id,
            'title': self.title,
            'page_number': self.page_number,
            'section_number': self.section_number,
            'level': self.level,
            'order_index': self.order_index,
            'entry_type': self.entry_type,
            'notes': self.notes,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
class CrossReference(Base):
    """Cross-references between annotations"""
    __tablename__ = 'cross_references'

    # Primary key and foreign keys
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_annotation_id = Column(Integer, ForeignKey('annotations.id', ondelete='CASCADE'), nullable=False)
    target_annotation_id = Column(Integer, ForeignKey('annotations.id', ondelete='CASCADE'), nullable=False)

    # Reference information
    reference_type = Column(String(50), default='related')  # related, contradicts, supports, defines
    notes = Column(Text)
    confidence = Column(Float, default=1.0)  # Confidence score for AI-generated references

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))  # User or 'AI'

    # Relationships
    source_annotation = relationship(
        "Annotation",
        foreign_keys=[source_annotation_id],
        back_populates="cross_references_from"
    )
    target_annotation = relationship(
        "Annotation",
        foreign_keys=[target_annotation_id],
        back_populates="cross_references_to"
    )

    # Indexes and constraints
    __table_args__ = (
        Index('idx_cross_ref_source', 'source_annotation_id'),
        Index('idx_cross_ref_target', 'target_annotation_id'),
        UniqueConstraint('source_annotation_id', 'target_annotation_id', name='uq_cross_reference'),
        CheckConstraint('source_annotation_id != target_annotation_id', name='check_different_annotations'),
    )

    def __repr__(self):
        return f"<CrossReference(source={self.source_annotation_id}, target={self.target_annotation_id}, type='{self.reference_type}')>"


class AssemblyNote(Base):
    """General notes for an assembly (not tied to specific documents)"""
    __tablename__ = 'assembly_notes'

    # Primary key and foreign key
    id = Column(Integer, primary_key=True, autoincrement=True)
    assembly_id = Column(Integer, ForeignKey('assemblies.id', ondelete='CASCADE'), nullable=False)

    # Note content
    title = Column(String(500))
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default='general')  # general, summary, todo, idea

    # Metadata
    tags = Column(ARRAY(String), default=list)
    priority = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255))

    # Relationships
    assembly = relationship("Assembly", back_populates="assembly_notes")

    # Indexes
    __table_args__ = (
        Index('idx_assembly_note_assembly', 'assembly_id'),
        Index('idx_assembly_note_type', 'note_type'),
        Index('idx_assembly_note_created', 'created_at'),
    )

    def __repr__(self):
        return f"<AssemblyNote(id={self.id}, title='{self.title}', type='{self.note_type}')>"


# Vector storage for semantic search (integrates with ChromaDB/pgvector)
class DocumentEmbedding(Base):
    """Document embeddings for semantic search"""
    __tablename__ = 'document_embeddings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)

    # Chunk information
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_tokens = Column(Integer)

    # Embedding data (stored as JSON array for compatibility)
    # In production, use pgvector extension for PostgreSQL
    embedding = Column(JSONB)
    embedding_model = Column(String(100))
    embedding_dimension = Column(Integer)

    # Metadata
    page_numbers = Column(ARRAY(Integer))  # Pages this chunk spans

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_embedding_document', 'document_id'),
        Index('idx_embedding_chunk', 'document_id', 'chunk_index'),
        UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk'),
    )

    def __repr__(self):
        return f"<DocumentEmbedding(document_id={self.document_id}, chunk={self.chunk_index})>"