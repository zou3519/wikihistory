import bisect
import difflib


class PatchType:
    """PatchType enumerates the types of Patches: add and delete."""
    ADD = 0
    DELETE = 1


class Patch:
    """A Patch is a contiguous block of added or deleted lines."""
    def __init__(self, ptype, start, end):
        assert ptype == PatchType.ADD or ptype == PatchType.DELETE
        assert start >= 0
        assert end > start

        self.ptype = ptype
        self.start = start
        self.end = end
        self.length = end - start


class PatchSet:
    """
    A PatchSet is a set of sequentially applied Patches with one *unique* ID.
    Each Patch *implicitly* depends on preceding Patches.
    These are critical assumptions, so get them right!
    """
    def __init__(self, psid):
        self.psid = psid
        self.patches = []

    @classmethod
    def psdiff(cls, psid, old, new):
        ptype = None
        ps = cls(psid)
        start = None

        # For line in diff...
        diff = difflib.ndiff(old, new)
        index = 0
        for line in diff:
            if line[0] == ' ':
                # If equal, terminate any current patch.
                if ptype is not None:
                    ps.append_patch(Patch(ptype, start, index))
                    if ptype == PatchType.DELETE:
                        index = start
                    ptype = None
                index += 1
            elif line[0] == '+':
                # If addition, terminate any current DELETE patch.
                if ptype == PatchType.DELETE:
                    ps.append_patch(Patch(ptype, start, index))
                    index = start
                    ptype = None
                # Begin a new ADD patch, or extend an existing one.
                if ptype is None:
                    ptype = PatchType.ADD
                    start = index
                index += 1
            elif line[0] == '-':
                # If deletion, terminate any current ADD patch.
                if ptype == PatchType.ADD:
                    ps.append_patch(Patch(ptype, start, index))
                    ptype = None
                # Begin a new DELETE patch, or extend an existing one.
                if ptype is None:
                    ptype = PatchType.DELETE
                    start = index
                index += 1
            # Skip line[0] == '?' completely.

        # Terminate and add any remaining patch.
        if ptype is not None:
            ps.append_patch(Patch(ptype, start, index))

        return ps

    def append_patch(self, p):
        self.patches.append(p)


class PatchModel:
    """A PatchModel models applying PatchSets to a text object."""
    model = [(0, None)] # A sorted list of end-ordered spans and PatchSet IDs.

    def apply_patchset(self, ps):
        depends = set()
        for p in ps.patches:
            if p.ptype == PatchType.ADD:
                # Find indices and dependencies.
                sin = bisect.bisect_left(
                    [span for (span, psid) in self.model], p.start)
                ein = bisect.bisect_right(
                    [span for (span, psid) in self.model], p.start)

                for (span, psid) in self.model[sin:(ein + 1)]:
                    depends.add(psid)

                # Remove intermediates if present.
                if sin != ein:
                    del self.model[(sin + 1):ein]
                # Else, split the surrounding span.
                else:
                    (span, psid) = self.model[sin]
                    self.model.insert(sin, (p.start, psid))
                ein = sin + 1

                # Insert.
                self.model.insert(ein, (p.end, ps.psid))

                # Update proceeding spans.
                self.model[(ein + 1):len(self.model)] = \
                    [(span + p.length, psid) for (span, psid) \
                    in self.model[(ein + 1):len(self.model)]]

            elif p.ptype == PatchType.DELETE:
                # Find indices and dependencies.
                sin = bisect.bisect_right(
                    [span for (span, psid) in self.model], p.start)
                ein = bisect.bisect_left(
                    [span for (span, psid) in self.model], p.end)

                for (span, psid) in self.model[sin:(ein + 1)]:
                    depends.add(psid)

                # Adjust indices.
                if sin != bisect.bisect_left(
                    [span for (span, psid) in self.model], p.start): sin -= 1
                if ein != bisect.bisect_right(
                    [span for (span, psid) in self.model], p.end): ein += 1

                # Shrink the preceding span and remove intermediates if present
                (span, psid) = self.model[sin]
                if sin != ein:
                    self.model[sin] = (p.start, psid)
                    del self.model[(sin + 1):ein]
                # Else, split the surrounding span.
                else:
                    self.model.insert(sin, (p.start, psid))
                ein = sin + 1

                # Insert.
                self.model.insert(ein, (p.start, ps.psid))

                # Update the proceeding spans.
                self.model[(ein + 1):len(self.model)] = \
                    [(span - p.length, psid) for (span, psid) \
                    in self.model[(ein + 1):len(self.model)]]

            else:
                assert False

        depends.discard(None)
        depends.discard(ps.psid)
        return depends