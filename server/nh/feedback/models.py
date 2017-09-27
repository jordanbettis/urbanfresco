from nh.core.db import Base
from nh.core import config
from nh.auth.models import User

from sqlalchemy import (
    ForeignKey, Column, Integer, Unicode, Boolean, UnicodeText, DateTime)

from sqlalchemy import func
from sqlalchemy.orm import relationship

class FeedbackItem(Base):
    """ Feedback from a user """
    __tablename__ = "nh_feedback_feedbackitem"
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("nh_auth_user.id"))
    user = relationship("User")

    can_publish = Column(Boolean, nullable=False, default=False)
    published = Column(Boolean, nullable=False, default=False)
    dismissed = Column(Boolean, nullable=False, default=False)

    name = Column(Unicode(200))
    email = Column(Unicode(200))

    message = Column(UnicodeText(), nullable=False)

    created = Column(DateTime, nullable=False, default=func.current_timestamp())
    changed = Column(DateTime, nullable=False, default=func.current_timestamp(),
                     onupdate=func.current_timestamp())

    
