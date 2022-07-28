# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
The API for running SpiNNaker simulations based on a basic (non-neural) graph.

The general usage pattern for this API something like is::

    import spinnaker_graph_front_end as gfe

    # Uses information from your configuration file
    # You might need to specify how many SpiNNaker boards to allocate
    gfe.setup()

    # Make the bits that do the computation
    for each vertex to add:
        gfe.add_vertex_instance(vertex)

    # Connect them together so computations are coordinated
    for each edge to add:
        gfe.add_edge_instance(edge)

    # Actually plan and run the simulation
    gfe.run(number_of_steps)

    # Get the results back; what this means can be complex
    for each vertex:
        results += vertex.retrieve_relevant_results()

    # Shut everything down
    # Only your retrieved results really exist after this
    gfe.stop()

    # Analyse/render the results; totally application-specific!

It is possible to use GFE-style vertices in a neural graph (e.g., to simulate
the external world). Talk to the SpiNNaker team for more details.
"""

import os
import logging
import sys
from spinn_utilities.log import FormatAdapter
from spinn_utilities.socket_address import SocketAddress
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from pacman.model.graphs.application.application_edge import ApplicationEdge
from spinn_front_end_common.data import FecDataView
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utility_models import (
    ReverseIpTagMultiCastSource as _RIPTMCS)
from spinnaker_graph_front_end._version import (
    __version__, __version_name__, __version_month__, __version_year__)
from spinnaker_graph_front_end.spinnaker import SpiNNaker
from spinnaker_graph_front_end import spinnaker as gfe_file

logger = FormatAdapter(logging.getLogger(__name__))


__all__ = ['add_edge_instance', 'add_socket_address', 'add_vertex_instance',
           'buffer_manager', 'get_number_of_available_cores_on_machine',
           'has_ran', 'is_allocated_machine', 'machine', 'placements',
           'ReverseIpTagMultiCastSource', 'routing_infos', 'run', 'setup',
           'stop']


def setup(model_binary_module=None,
          model_binary_folder=None, database_socket_addresses=(),
          n_chips_required=None, n_boards_required=None,
          time_scale_factor=None, machine_time_step=None):
    """ Set up a graph, ready to have vertices and edges added to it, and the\
        simulator engine that will execute the graph.

    .. note::
        This must be called *before* the other functions in this API.

    :param ~types.ModuleType model_binary_module:
        the Python module where the binary files (``.aplx``) can be found for
        the compiled C code that is being used in this application; mutually
        exclusive with the ``model_binary_folder``.
    :param str model_binary_folder:
        the folder where the binary files can be found for the c code that is
        being used in this application; mutually exclusive with the
        ``model_binary_module``.
    :param database_socket_addresses:
        set of SocketAddresses to be added for the database notification
        system. These are over and above the ones used by the
        :py:class:`~spinn_front_end_common.utilities.connections.LiveEventConnection`
    :type database_socket_addresses:
        ~collections.abc.Iterable(~spinn_utilities.socket_address.SocketAddress)
    :param n_chips_required:
        Deprecated! Use ``n_boards_required`` instead.
        Must be ``None`` if ``n_boards_required`` specified.
    :type n_chips_required: int or None
    :param n_boards_required:
        if you need to be allocated a machine (for spalloc) before building
        your graph, then fill this in with a general idea of the number of
        boards you need so that the spalloc system can allocate you a machine
        big enough for your needs.
    :type n_boards_required: int or None
    :raise ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
        if mutually exclusive options are given.
    """
    # pylint: disable=redefined-outer-name
    logger.info(
        "SpiNNaker graph front end (c) {}, University of Manchester",
        __version_year__)
    parent_dir = os.path.split(os.path.split(gfe_file.__file__)[0])[0]
    logger.info(
        "Release version {}({}) - {} {}. Installed in folder {}",
        __version__, __version_name__, __version_month__, __version_year__,
        parent_dir)

    # add the directories where the binaries are located
    if model_binary_module is not None:
        FecDataView.register_binary_search_path(
            os.path.dirname(model_binary_module.__file__))
    elif model_binary_folder is not None:
        FecDataView.register_binary_search_path(model_binary_folder)
    else:
        file_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        FecDataView.register_binary_search_path(file_dir)

    # set up the spinnaker object; after this, _sim() returns this object
    SpiNNaker(
        n_chips_required=n_chips_required,
        n_boards_required=n_boards_required,
        machine_time_step=machine_time_step,
        time_scale_factor=time_scale_factor)
    FecDataView.add_database_socket_addresses(database_socket_addresses)


def _sim():
    """ Get the current SpiNNaker simulator object.

    :rtype: ~spinn_front_end_common.utilities.SimulatorInterface
    """
    return globals_variables.get_simulator()


def run(duration=None):
    """ Run a simulation for a number of microseconds.

    :param int duration:
        the number of microseconds the application code should run for
    """
    _sim().run(duration)


def run_until_complete(n_steps=None):
    """ Run until the simulation is complete.

    :param int n_steps:
        If not ``None``, this specifies that the simulation should be
        requested to run for the given number of steps.  The host will
        still wait until the simulation itself says it has completed
    """
    _sim().run_until_complete(n_steps)


def stop():
    """ Do any necessary cleaning up before exiting. Unregisters the controller
    """
    # pylint: disable=global-variable-undefined
    global _executable_finder

    _sim().stop()
    _executable_finder = None


def stop_run():
    """ Stop a request to run forever
    """
    _sim().stop_run()


def add_vertex_instance(vertex_to_add):
    """ Add an existing application vertex to the unpartitioned graph.

    :param ~pacman.model.graphs.application.ApplicationVertex vertex_to_add:
        vertex instance to add to the graph
    """
    FecDataView.add_vertex(vertex_to_add)


def _new_edge_label():
    label = f"Edge {FecDataView.get_next_none_labelled_edge_number()}"
    return label


def add_edge_instance(edge, partition_id):
    """ Add an edge to the unpartitioned graph.

    :param ~pacman.model.graphs.application.ApplicationEdge edge:
        The edge to add.
    :param str partition_id:
        The ID of the partition that the edge belongs to.
    """
    FecDataView.add_edge(edge, partition_id)


def add_machine_vertex_instance(machine_vertex):
    """ Add a machine vertex instance to the graph.

    :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
        The vertex to add
    """
    app_vertex = AbstractOneAppOneMachineVertex(
        machine_vertex, machine_vertex.label, constraints=())
    FecDataView.add_vertex(app_vertex)
    machine_vertex._app_vertex = app_vertex


def add_machine_edge_instance(edge, partition_id):
    """ Add a machine edge instance to the graph.

    :param ~pacman.model.graphs.machine.MachineEdge edge:
        The edge to add
    :param str partition_id:
        The ID of the partition that the edge belongs to.
    """
    FecDataView.add_edge(
        ApplicationEdge(
            edge.pre_vertex.app_vertex, edge.post_vertex.app_vertex),
        partition_id)


def add_socket_address(
        database_ack_port_num, database_notify_host, database_notify_port_num):
    """ Add a socket address for the notification protocol.

    :param int database_ack_port_num:
        port number to send acknowledgement to
    :param str database_notify_host:
        host IP to send notification to
    :param int database_notify_port_num:
        port that the external device will be notified on.
    """
    database_socket = SocketAddress(
        listen_port=database_ack_port_num,
        notify_host_name=database_notify_host,
        notify_port_no=database_notify_port_num)

    FecDataView.add_database_socket_address(database_socket)


def get_number_of_available_cores_on_machine():
    """ Get the number of cores on this machine that are available to the\
        simulation.

    :rtype: int
    """
    return _sim().get_number_of_available_cores_on_machine


def has_ran():
    """ Get whether the simulation has already run.

    :rtype: bool
    """
    return FecDataView.is_ran_ever()


def routing_infos():
    """ Get information about how messages are routed on the machine.

    :rtype: ~pacman.model.routing_info.RoutingInfo
    """
    return FecDataView.get_routing_infos()


def placements():
    """ Get the planned locations of machine vertices on the machine.

    :rtype: ~pacman.model.placements.Placements
    """
    return FecDataView.get_placements()


def tags():
    """ Get the IPTAGs allocated on the machine.

    :rtype: ~pacman.model.tags.Tags
    """
    return FecDataView.get_tags()


def buffer_manager():
    """ Get the buffer manager being used for loading/extracting buffers

    :rtype: ~spinn_front_end_common.interface.buffer_management.BufferManager
    """
    return FecDataView.get_buffer_manager()


def machine():
    """ Get the model of the attached/allocated machine.

    :rtype: ~spinn_machine.Machine
    """
    logger.warning(
        "If you are getting the machine object to locate how many cores you "
        "can use,\n"
        "please use the following function call, as it is more reliable and "
        "takes into account software resources as well:\n\n"
        "get_number_of_available_cores_on_machine()")
    return FecDataView.get_machine()


def is_allocated_machine():
    """ Get whether a machine is allocated.

    :rtype: bool
    """
    return FecDataView.has_machine()


class ReverseIpTagMultiCastSource(_RIPTMCS):
    """
    For full documentation see
    :py:class:`~spinn_front_end_common.utility_models.ReverseIpTagMultiCastSource`.
    """
    __slots__ = ()
