from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = 'your_revision_id'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "role_change_logs",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column("target_user_id", sa.UUID(), nullable=False),
        sa.Column("old_role", sa.String(50)),
        sa.Column("new_role", sa.String(50)),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table("role_change_logs")