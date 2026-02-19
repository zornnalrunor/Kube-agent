"""
State Manager Module
Gère l'état du workflow agentique et la persistance
"""
import json
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from core.config import Config, StateBackend

Base = declarative_base()


class WorkflowStatus(str, Enum):
    """Statuts possibles d'un workflow"""
    PENDING = "pending"
    PLANNING = "planning"
    PROVISIONING = "provisioning"
    CONFIGURING = "configuring"
    VALIDATING = "validating"
    DOCUMENTING = "documenting"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class AgentStatus(str, Enum):
    """Statuts possibles d'un agent"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class WorkflowState(BaseModel):
    """Modèle d'état d'un workflow"""
    workflow_id: str
    status: WorkflowStatus
    platform: str
    environment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    config: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class AgentExecution(BaseModel):
    """Modèle d'exécution d'un agent"""
    execution_id: str
    workflow_id: str
    agent_name: str
    status: AgentStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    logs: List[str] = Field(default_factory=list)


# SQLAlchemy Models
class WorkflowStateDB(Base):
    """Table pour les workflows"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True)
    workflow_id = Column(String(100), unique=True, nullable=False)
    status = Column(String(50), nullable=False)
    platform = Column(String(50), nullable=False)
    environment = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    config = Column(JSON, nullable=False)
    outputs = Column(JSON, nullable=False)
    errors = Column(JSON, nullable=False)


class AgentExecutionDB(Base):
    """Table pour les exécutions d'agents"""
    __tablename__ = "agent_executions"
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(String(100), unique=True, nullable=False)
    workflow_id = Column(String(100), nullable=False)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    error_message = Column(Text)
    logs = Column(JSON, nullable=False)


class StateManager:
    """Gestionnaire d'état centralisé pour le système agentique"""
    
    def __init__(self, config: Config):
        self.config = config
        self.backend = config.state_backend
        
        if self.backend == StateBackend.SQLITE:
            db_path = Path(config.state_db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.engine = create_engine(f"sqlite:///{db_path}")
        elif self.backend == StateBackend.POSTGRESQL:
            if not config.state_db_url:
                raise ValueError("PostgreSQL URL is required")
            self.engine = create_engine(config.state_db_url)
        else:  # FILE backend
            self.file_path = Path(config.data_dir) / "state.json"
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_file_backend()
            return
        
        # Create tables
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _init_file_backend(self):
        """Initialize file-based backend"""
        if not self.file_path.exists():
            self.file_path.write_text(json.dumps({
                "workflows": {},
                "executions": {}
            }, indent=2))
    
    def _get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def create_workflow(self, workflow: WorkflowState) -> WorkflowState:
        """Crée un nouveau workflow"""
        if self.backend == StateBackend.FILE:
            data = json.loads(self.file_path.read_text())
            data["workflows"][workflow.workflow_id] = workflow.model_dump(mode='json')
            self.file_path.write_text(json.dumps(data, indent=2, default=str))
            return workflow
        
        session = self._get_session()
        try:
            db_workflow = WorkflowStateDB(
                workflow_id=workflow.workflow_id,
                status=workflow.status.value,
                platform=workflow.platform,
                environment=workflow.environment,
                created_at=workflow.created_at,
                updated_at=workflow.updated_at,
                config=workflow.config,
                outputs=workflow.outputs,
                errors=workflow.errors,
            )
            session.add(db_workflow)
            session.commit()
            return workflow
        finally:
            session.close()
    
    def update_workflow(self, workflow: WorkflowState) -> WorkflowState:
        """Met à jour un workflow existant"""
        workflow.updated_at = datetime.utcnow()
        
        if self.backend == StateBackend.FILE:
            data = json.loads(self.file_path.read_text())
            data["workflows"][workflow.workflow_id] = workflow.model_dump(mode='json')
            self.file_path.write_text(json.dumps(data, indent=2, default=str))
            return workflow
        
        session = self._get_session()
        try:
            db_workflow = session.query(WorkflowStateDB).filter_by(
                workflow_id=workflow.workflow_id
            ).first()
            if db_workflow:
                db_workflow.status = workflow.status.value
                db_workflow.updated_at = workflow.updated_at
                db_workflow.config = workflow.config
                db_workflow.outputs = workflow.outputs
                db_workflow.errors = workflow.errors
                session.commit()
            return workflow
        finally:
            session.close()
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Récupère un workflow par son ID"""
        if self.backend == StateBackend.FILE:
            data = json.loads(self.file_path.read_text())
            workflow_data = data["workflows"].get(workflow_id)
            if workflow_data:
                return WorkflowState(**workflow_data)
            return None
        
        session = self._get_session()
        try:
            db_workflow = session.query(WorkflowStateDB).filter_by(
                workflow_id=workflow_id
            ).first()
            if db_workflow:
                return WorkflowState(
                    workflow_id=db_workflow.workflow_id,
                    status=WorkflowStatus(db_workflow.status),
                    platform=db_workflow.platform,
                    environment=db_workflow.environment,
                    created_at=db_workflow.created_at,
                    updated_at=db_workflow.updated_at,
                    config=db_workflow.config,
                    outputs=db_workflow.outputs,
                    errors=db_workflow.errors,
                )
            return None
        finally:
            session.close()
    
    def create_execution(self, execution: AgentExecution) -> AgentExecution:
        """Enregistre une exécution d'agent"""
        if self.backend == StateBackend.FILE:
            data = json.loads(self.file_path.read_text())
            data["executions"][execution.execution_id] = execution.model_dump(mode='json')
            self.file_path.write_text(json.dumps(data, indent=2, default=str))
            return execution
        
        session = self._get_session()
        try:
            db_execution = AgentExecutionDB(
                execution_id=execution.execution_id,
                workflow_id=execution.workflow_id,
                agent_name=execution.agent_name,
                status=execution.status.value,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                input_data=execution.input_data,
                output_data=execution.output_data,
                error_message=execution.error_message,
                logs=execution.logs,
            )
            session.add(db_execution)
            session.commit()
            return execution
        finally:
            session.close()
    
    def update_execution(self, execution: AgentExecution) -> AgentExecution:
        """Met à jour une exécution d'agent"""
        if self.backend == StateBackend.FILE:
            data = json.loads(self.file_path.read_text())
            data["executions"][execution.execution_id] = execution.model_dump(mode='json')
            self.file_path.write_text(json.dumps(data, indent=2, default=str))
            return execution
        
        session = self._get_session()
        try:
            db_execution = session.query(AgentExecutionDB).filter_by(
                execution_id=execution.execution_id
            ).first()
            if db_execution:
                db_execution.status = execution.status.value
                db_execution.completed_at = execution.completed_at
                db_execution.output_data = execution.output_data
                db_execution.error_message = execution.error_message
                db_execution.logs = execution.logs
                session.commit()
            return execution
        finally:
            session.close()
    
    def get_workflow_executions(self, workflow_id: str) -> List[AgentExecution]:
        """Récupère toutes les exécutions d'un workflow"""
        if self.backend == StateBackend.FILE:
            data = json.loads(self.file_path.read_text())
            executions = []
            for exec_data in data["executions"].values():
                if exec_data["workflow_id"] == workflow_id:
                    executions.append(AgentExecution(**exec_data))
            return executions
        
        session = self._get_session()
        try:
            db_executions = session.query(AgentExecutionDB).filter_by(
                workflow_id=workflow_id
            ).all()
            return [
                AgentExecution(
                    execution_id=e.execution_id,
                    workflow_id=e.workflow_id,
                    agent_name=e.agent_name,
                    status=AgentStatus(e.status),
                    started_at=e.started_at,
                    completed_at=e.completed_at,
                    input_data=e.input_data,
                    output_data=e.output_data,
                    error_message=e.error_message,
                    logs=e.logs,
                )
                for e in db_executions
            ]
        finally:
            session.close()
