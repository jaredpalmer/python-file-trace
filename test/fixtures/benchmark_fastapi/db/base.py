"""SQLAlchemy base class."""


class Base:
    """Declarative base for all models."""

    __tablename__: str

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {c: getattr(self, c) for c in dir(self) if not c.startswith("_")}
