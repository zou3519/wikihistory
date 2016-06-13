import libxml2
import math
import os.path


NAMESPACE = "http://openprovenance.org/model/v1.1.a"


class OPMGraph:
    """An OPMGraph represents a provenance graph in OPM format."""
    # ***FACTORY CONSTRUCTORS***
    @classmethod
    def new_graph(cls, account):
        """new_graph constructs a new OPMGraph with default account."""
        graph = cls()

        # Create doc and query context.
        graph.doc = libxml2.newDoc("1.0")
        graph.ctxt = graph.doc.xpathNewContext()
        graph.ctxt.xpathRegisterNs('opm', NAMESPACE)

        # Create root and namespace.
        graph.root = graph.doc.newChild(None, "opmGraph", None)
        graph.ns = graph.root.newNs(NAMESPACE, "opm")
        graph.root.setNs(graph.ns)
        # opmGraph id is set at write-time; see save_to, below.

        # Create account.
        graph.account = str(account)
        graph.root.newChild(graph.ns, "accounts", None).newChild(
            graph.ns, "account", None).setProp("id", graph.account)

        # Create standard branches.
        graph.artifacts = None
        graph.causalDependencies = None

        return graph

    @classmethod
    def parse_file(cls, filename):
        """parse_file parses an OPM XML file into an OPMGraph."""
        graph = cls()

        # Parse doc and create query context.
        graph.doc = libxml2.parseFile(filename)
        graph.ctxt = graph.doc.xpathNewContext()
        graph.ctxt.xpathRegisterNs('opm', NAMESPACE)

        # Query and assign root and namespace.
        root = graph.ctxt.xpathEval('/opm:opmGraph')
        assert len(root) == 1
        graph.root = root[0]
        graph.ns = graph.root.ns()

        # Query and assign account.
        accounts = graph.ctxt.xpathEval('/opm:opmGraph/opm:accounts')
        assert len(accounts) == 1
        graph.account = accounts[0].firstElementChild().prop('id')
        # XXX: This is dodgy; may change.

        # Query and assign standard branches.
        artifacts = graph.ctxt.xpathEval('/opm:opmGraph/opm:artifacts')
        if not artifacts:
            graph.artifacts = None
        elif len(artifacts) == 1:
            graph.artifacts = artifacts[0]
        else:
            assert False

        causalDependencies = graph.ctxt.xpathEval(
            '/opm:opmGraph/opm:causalDependencies')
        if not causalDependencies:
            graph.causalDependencies = None
        elif len(causalDependencies) == 1:
            graph.causalDependencies = causalDependencies[0]
        else:
            assert False

        return graph


    # ***GET METHODS***
    def get_adj_labels(self):
        """
        get_adj_labels returns a dict encoding this OPMGraph's adjacencies and
        a second dict mapping nids to labels.
        """
        adj = {}
        labels = {}

        # Get nodes and labels.
        for node in self.ctxt.xpathEval('/opm:opmGraph/opm:agents/*|' + \
                                       '/opm:opmGraph/opm:artifacts/*|' + \
                                       '/opm:opmGraph/opm:processes/*'):
            nid = node.prop('id')
            adj[nid] = set()

            child = node.children
            label = None
            while child is not None:
                if child.name == 'label':
                    label = child.prop('value')
                child = child.next
            assert label is not None
            labels[nid] = label

        # Get edges.
        for edge in self.ctxt.xpathEval('/opm:opmGraph/opm:causalDependencies/*'):
            child = edge.children
            cause = None
            effect = None
            while child is not None:
                if child.name == 'cause':
                    cause = child.prop('ref')
                elif child.name == 'effect':
                    effect = child.prop('ref')
                child = child.next
            assert cause is not None and effect is not None
            adj[effect].add(cause)

        return (adj, labels)


    # ***SET METHODS***
    def new_artifact(self, aid, label):
        """new_artifact creates an artifact with ID aid and a label."""
        if self.artifacts is None:
            self.artifacts = self.root.newChild(self.ns, "artifacts", None)

        artifact = self.artifacts.newChild(self.ns, "artifact", None)
        artifact.setProp("id", str(aid))

        artifact.newChild(
            self.ns, "account", None).setProp("ref", self.account)
        artifact.newChild(
            self.ns, "label", None).setProp("value", str(label))

    def new_wasDerivedFrom(self, a1id, a2id):
        """
        new_wasDerivedFrom creates an artifact-to-artifact causal dependency
        from a1id to a2id.
        """
        if self.causalDependencies is None:
            self.causalDependencies = self.root.newChild(
                self.ns, "causalDependencies", None)

        wasDerivedFrom = self.causalDependencies.newChild(
            self.ns, "wasDerivedFrom", None)

        wasDerivedFrom.newChild(
            self.ns, "account", None).setProp("ref", self.account)
        wasDerivedFrom.newChild(
            self.ns, "cause", None).setProp("ref", str(a1id))
        wasDerivedFrom.newChild(
            self.ns, "effect", None).setProp("ref", str(a2id))


    # ***SAVE METHODS***
    def save_to(self, filename):
        """save_to saves this OPMGraph to filename in OPM XML format."""
        opmfile = open(filename, 'w')
        self.root.setProp("id", os.path.basename(opmfile.name))
        self.doc.saveTo(opmfile, encoding="UTF-8", format=1)
        opmfile.close()
