import shlex
import logging
from wikiprocessor import HistoryIter
from subprocess import Popen, PIPE


class GitRepo(object):
    """Handy-dandy operations for a git repo"""

    def __init__(self, path):
        """path is the full path to a repo"""
        git_dir_arg = '--git-dir=%s/.git' % path
        work_tree_arg = '--work-tree=%s' % path
        self.git = 'git %s %s' % (git_dir_arg, work_tree_arg)
        self.path = path + "/"  # sanitation

    def rev_list(self, path=".", reverse=False):
        """get a list of revisions"""
        reverse_flag = '--reverse' if reverse else ''
        command = '%s rev-list %s master %s%s' % (
            self.git, reverse_flag, self.path, path)
        return self.run_command(command)

    def show(self, commit, path="."):
        """Call git show to view contents of a file
            commit is a hash.
            path is the path to the file.
        """
        command = '%s show %s:%s' % (self.git, commit, path)
        return self.run_command(command)

    def commit_time(self, commit):
        command = '%s show -s --format=%%at %s' % (self.git, commit)
        return self.run_command(command)

    def run_command(self, command):
        debug(command)
        process = Popen(shlex.split(command), stdout=PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        return (exit_code, output, err)


class GitRepoIter(HistoryIter):
    """Iterates through revisions of a git version-controlled file """

    def __init__(self, name, git_repo, filepath, offset):
        self.git_repo = git_repo
        self.filepath = filepath
        self.name = name
        self.offset = offset

        # TODO: This comes from WikiIter. abstract the iterator
        self.use_blacklist = False
        self.title = 'syscall'

        (exit_code, output, err) = self.git_repo.rev_list(
            path=filepath, reverse=True)
        debug("%d %s %s" % (exit_code, output, err))
        if exit_code:
            self.commits = []
        else:
            self.commits = output.strip().split("\n")
        debug("Commits: " + str(self.commits))

    @property
    def document_name(self):
        return self.name

    @property
    def using_blacklist(self):
        return False

    def __iter__(self):
        return self

    def next(self):
        if self.offset >= len(self.commits):
            print("Iterated over " + str(self.offset) + " commits")
            raise StopIteration()

        commit = self.commits[self.offset]

        (exit_code, content, err) = self.git_repo.show(commit, self.filepath)
        if exit_code:
            debug("Iterator failed to get next commit: %d %s %s" %
                  (exit_code, content, err))
            raise StopIteration()

        (exit_code, timestamp, err) = self.git_repo.commit_time(commit)
        if exit_code:
            debug("Iterator failed to get commit time: %d %s %s" %
                  (exit_code, timestamp, err))
            raise StopIteration()

        self.offset += 1
        debug(self.offset)
        return (commit, float(timestamp), content)


def debug(string):
    logging.getLogger(__name__).info(string)
