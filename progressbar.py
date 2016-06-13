import sys


class ProgressBar:
    """A ProgressBar represents and prints progress."""
    def __init__(self, title, maximum=None):
        self.title = title + ': '
        self.maximum = maximum
        if self.maximum is not None: assert self.maximum > 0

        self.progress = 0
        self.format = '%d' if maximum is None \
            else '%' + str(len(str(maximum))) + 'd/' + str(maximum)

    def next(self):
        """next advances the ProgressBar one iteration."""
        if self.maximum is None or self.progress <= self.maximum:
            # If first print, print title, else clear last print.
            prefix = self.title if self.progress == 0 \
                else ''.join(['\b' for i in xrange(0, len(str(self.progress)))]) if self.maximum is None \
                else ''.join(['\b' for i in xrange(0, 2 * len(str(self.maximum)) + 1)])

            self.progress += 1
            sys.stdout.write(prefix + (self.format % self.progress))
            sys.stdout.flush()
