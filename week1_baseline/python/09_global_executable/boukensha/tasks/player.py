from boukensha.tasks.base import Base


class Player(Base):
    """Concrete task implementation for the player agent."""

    @classmethod
    def task_name(cls) -> str:
        return "player"
