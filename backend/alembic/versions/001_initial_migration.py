"""Initial migration - create voting tables

Revision ID: 001
Revises: 
Create Date: 2025-11-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create contestants table
    op.create_table(
        'contestants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('first_name', sa.String(255), nullable=False),
        sa.Column('last_name', sa.String(255), nullable=False),
        sa.Column('last_name_normalized', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_contestants_last_name_normalized', 'contestants', ['last_name_normalized'])
    
    # Create device_tokens table
    op.create_table(
        'device_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('total_votes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('total_votes <= 3', name='check_max_votes'),
    )
    op.create_index('ix_device_tokens_token', 'device_tokens', ['token'])
    
    # Create votes table
    op.create_table(
        'votes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('contestant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('device_token_id', UUID(as_uuid=True), nullable=False),
        sa.Column('voted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['contestant_id'], ['contestants.id']),
        sa.ForeignKeyConstraint(['device_token_id'], ['device_tokens.id']),
        sa.UniqueConstraint('contestant_id', 'device_token_id', name='unique_vote_per_contestant'),
    )
    op.create_index('ix_votes_voted_at', 'votes', ['voted_at'])


def downgrade() -> None:
    op.drop_table('votes')
    op.drop_table('device_tokens')
    op.drop_table('contestants')
