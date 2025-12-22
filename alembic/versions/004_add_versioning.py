from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'

def upgrade():
    op.create_table(
        'contract_versions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('contract_id', sa.String(36), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('yaml_content', sa.Text(), nullable=False),
        sa.Column('change_type', sa.String(20), nullable=True),
        sa.Column('change_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_contract_versions_contract_version', 'contract_versions', ['contract_id', 'version'], unique=True)
    op.create_index('ix_contract_versions_created_at', 'contract_versions', ['created_at'])
    
    op.add_column('contracts', sa.Column('version', sa.String(20), nullable=True))
    op.execute("UPDATE contracts SET version = '1.0.0' WHERE version IS NULL")
    op.alter_column('contracts', 'version', nullable=False)

def downgrade():
    op.drop_column('contracts', 'version')
    op.drop_index('ix_contract_versions_created_at', table_name='contract_versions')
    op.drop_index('ix_contract_versions_contract_version', table_name='contract_versions')
    op.drop_table('contract_versions')