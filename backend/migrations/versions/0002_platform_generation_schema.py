"""platform generation schema

Revision ID: 0002_platform_generation_schema
Revises: 0001_initial_schema
Create Date: 2026-05-15 00:00:00.000001
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_platform_generation_schema"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_projects_workspace_id"), "projects", ["workspace_id"], unique=False)

    op.create_table(
        "plans",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("roadmap", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("stack", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_plans_project_id"), "plans", ["project_id"], unique=False)

    op.create_table(
        "runs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("prompt_input", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("state", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_runs_project_id"), "runs", ["project_id"], unique=False)
    op.create_index(op.f("ix_runs_plan_id"), "runs", ["plan_id"], unique=False)
    op.create_index(op.f("ix_runs_trace_id"), "runs", ["trace_id"], unique=False)

    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_artifacts_run_id"), "artifacts", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_artifacts_run_id"), table_name="artifacts")
    op.drop_table("artifacts")

    op.drop_index(op.f("ix_runs_trace_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_plan_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_project_id"), table_name="runs")
    op.drop_table("runs")

    op.drop_index(op.f("ix_plans_project_id"), table_name="plans")
    op.drop_table("plans")

    op.drop_index(op.f("ix_projects_workspace_id"), table_name="projects")
    op.drop_table("projects")
