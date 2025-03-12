"""Subject table

Revision ID: 019263619afa
Revises: 8bb015a91201
Create Date: 2025-03-11 19:24:56.371831

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '019263619afa'
down_revision = '8bb015a91201'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('subject',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('topics', sa.String(length=256), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['course.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('subject', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_subject_course_id'), ['course_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('subject', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_subject_course_id'))

    op.drop_table('subject')
    # ### end Alembic commands ###
