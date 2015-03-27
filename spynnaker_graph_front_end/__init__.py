from spinn_front_end_common.interface.executable_finder import ExecutableFinder

_spinnaker = None


def setup(hostname=None, graph_label=None, model_binary_folder=None):
    """ for builders with pynn attitude, allows end users to define wherever
    their binaries are

    :param hostname:
    :param graph_label:
    :param model_binary_folder:
    :return:
    """
    from spynnaker_graph_front_end.spinnaker_graph_front_end import \
        SpiNNakerGraphFrontEnd
    import os
    global _spinnaker
    executable_finder = ExecutableFinder()
    executable_finder.add_path(os.path.dirname(model_binary_folder.__file__))
    # set up the spinnaker object
    _spinnaker = SpiNNakerGraphFrontEnd(hostname, graph_label,
                                        executable_finder)


def run(duration=None):
    """
    method to support running an application for a number of microseconds
    :param duration: the number of microseconds the application should run for
    :type duration: int
    """
    import sys
    global _spinnaker

    if duration is None:
        duration = sys.maxint
    _spinnaker.run(duration)


def stop(stop_on_board=True):
    """
    Do any necessary cleaning up before exiting.

    Unregisters the controller
    :param stop_on_board: decides if the routing tbales and tag should be
    removed from the machine at stop
    """
    global _spinnaker
    global _executable_finder

    _spinnaker.stop(stop_on_board)
    _spinnaker = None
    _executable_finder = None


def read_xml_file(file_path):
    """
    helper method for people who use this as an import.
    reads a xml file and translates it into a graph and partitioned graph
    (if required)
    :param file_path: the file path in absulete form
    :return: None
    """
    global _spinnaker
    _spinnaker.read_xml_file(file_path)


# noinspection PyPep8Naming
def Vertex(cellclass, cellparams, label=None, constraints=None):
    """

    :param cellclass:
    :param cellparams:
    :param constraints:
    :param label:
    :return:
    """
    global _spinnaker
    return _spinnaker.add_partitionable_vertex(cellclass, cellparams, label,
                                               constraints)


# noinspection PyPep8Naming
def Edge(cell_type, cellparams, label=None, constraints=None):
    """

    :param cell_type:
    :param cellparams:
    :param constraints:
    :param label:
    :return:
    """
    global _spinnaker
    return _spinnaker.add_partitionable_edge(cell_type, cellparams, label,
                                             constraints)


# noinspection PyPep8Naming
def PartitionedVertex(cellclass, cellparams, label=None, constraints=None):
    """

    :param cellclass:
    :param cellparams:
    :param label:
    :param constraints:
    :return:
    """
    global _spinnaker
    return _spinnaker.add_partitioned_vertex(cellclass, cellparams, label,
                                             constraints)


# noinspection PyPep8Naming
def PartitionedEdge(cellclass, cellparams, label=None, constraints=None):
    """

    :param cellclass:
    :param cellparams:
    :param constraints:
    :param label:
    :return:
    """
    global _spinnaker
    return _spinnaker.add_partitioned_edge(cellclass, cellparams, label,
                                           constraints)


def get_machine_dimensions():
    """

    :return:
    """
    global _spinnaker
    return _spinnaker.get_machine_dimensions()