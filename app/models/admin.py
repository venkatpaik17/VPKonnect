from sqlalchemy import BigInteger, Column, Date, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.db_sqlalchemy import Base


class ActivityDetail(Base):
    __tablename__ = "activity_detail"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    metric = Column(String(length=20), nullable=False)
    count = Column(BigInteger, nullable=False, server_default=text("0"))
    date = Column(Date, nullable=False, server_default=func.now())

    # for keeping day wise total count. no two rows will have same metric and date combined
    UniqueConstraint(metric, date, name="activity_detail_metric_date_unique")
