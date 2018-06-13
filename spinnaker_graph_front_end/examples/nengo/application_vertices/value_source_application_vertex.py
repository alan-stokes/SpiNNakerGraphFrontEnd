from spinn_utilities.overrides import overrides
from spinnaker_graph_front_end.examples.nengo.abstracts.\
    abstract_nengo_application_vertex import \
    AbstractNengoApplicationVertex


class ValueSourceApplicationVertex(AbstractNengoApplicationVertex):

    __slots__ = [
        #
        '_nengo_node_output',
        #
        '_nengo_node_size_out',
        #
        '_period'
    ]

    def __init__(self, label, rng, nengo_node_output, nengo_node_size_out,
                 period):
        AbstractNengoApplicationVertex.__init__(self, label=label, rng=rng)
        self._nengo_node_output = nengo_node_output
        self._nengo_node_size_out = nengo_node_size_out
        self._period = period

    @overrides(AbstractNengoApplicationVertex.create_machine_vertices)
    def create_machine_vertices(self):
        pass
