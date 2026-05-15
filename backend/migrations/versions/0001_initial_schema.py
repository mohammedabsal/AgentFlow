"""initial schema for AgentFlow

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "agents",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("tools", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("model_provider", sa.String(length=64), nullable=False, server_default="openai"),
        sa.Column("memory_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("retry_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_agents_workspace_id"), "agents", ["workspace_id"], unique=False)

    op.create_table(
        "workflows",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("graph", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("workspace_id", "name", name="uq_workflows_workspace_name"),
    )
    op.create_index(op.f("ix_workflows_workspace_id"), "workflows", ["workspace_id"], unique=False)

    op.create_table(
        "executions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("workflow_id", sa.String(length=36), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("input", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("state", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_executions_workflow_id"), "executions", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_executions_trace_id"), "executions", ["trace_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_executions_trace_id"), table_name="executions")
    op.drop_index(op.f("ix_executions_workflow_id"), table_name="executions")
    op.drop_table("executions")

    op.drop_index(op.f("ix_workflows_workspace_id"), table_name="workflows")
    op.drop_table("workflows")

    op.drop_index(op.f("ix_agents_workspace_id"), table_name="agents")
    op.drop_table("agents")

    op.drop_table("workspaces")
