from abc import ABCMeta, abstractmethod


class DistanceModel:
    """Abstract class for document similarity models"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def score(self, previous, current):
        """Compute the distance between current and previous"""
        return


class BasicDistanceModel(DistanceModel):
    """Distance between adjacent revisions is always 1"""

    def __init__(self, title):
        self.title = title

    def score(self, previous, current):
        return 1
