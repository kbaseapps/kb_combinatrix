"""Check and coerce the parameter list for the combinatrix."""

import re
from typing import Any

import networkx as nx
from combinatrix.constants import (
    FIELD,
    JOIN_LIST,
    MAX_CONNECTIONS_PER_NODE,
    MAX_REFS,
    PARAM_ERROR_MESSAGE,
    REF,
    REFS,
    REQD_FIELDS,
    T1,
    T2,
)
from combinatrix.util import MULTISPACE_REGEX
from networkx import Graph


def validate_params(params: dict[str, Any], max_refs: int = MAX_REFS) -> dict[str, Any]:
    """Parse the params and clean up the join-related params.

    :param params: input parameters for the combinatrix
    :type params: dict[str, Any]
    :param max_refs: maximum number of datasets per combinatrix run
    :type max_refs: int
    :raises RuntimeError: if errors are found in the join params
    :return: cleaned-up and parsed join params
    :rtype: dict[str, Any]
    """
    errors = []
    joins = []
    refs = set()
    reqd_fields_by_ref = {}

    if not params or JOIN_LIST not in params:
        err_msg = f"{PARAM_ERROR_MESSAGE}no '{JOIN_LIST}' parameter found"
        raise RuntimeError(err_msg)

    # trim fields / remove spaces
    for paramset in params[JOIN_LIST]:
        # should be in the form {"t1_ref": UPA, "t1_field": str, "t2_ref": UPA, "t2_field": str}
        has_errors = False
        join_data = {}
        for tx in [T1, T2]:
            join_data[tx] = {}
            for f_name in [REF, FIELD]:
                val = paramset.get(f"{tx}_{f_name}", "")
                if not val or not val.strip():
                    errors.append(
                        f"Invalid value for {tx}_{f_name}: '{paramset.get(tx + '_' + f_name)}'"
                    )
                    has_errors = True
                    continue
                # normalise the name - convert to lowercase, convert spaces to _
                join_data[tx][f_name] = re.sub(
                    MULTISPACE_REGEX, "_", val.strip().lower()
                )
                if f_name == REF:
                    refs.update([join_data[tx][REF]])

        if (
            REF in join_data[T1]
            and REF in join_data[T2]
            and join_data[T2][REF] == join_data[T1][REF]
        ):
            errors.append(f"{join_data[T1][REF]} cannot be joined to itself")
            has_errors = True

        if not has_errors:
            # make sure this combination has not been seen before
            inverse_join_data = {T1: join_data[T2], T2: join_data[T1]}
            if join_data not in joins and inverse_join_data not in joins:
                joins.append(join_data)

            # collate the field data required from each ref
            for tx in [T1, T2]:
                if join_data[tx][REF] not in reqd_fields_by_ref:
                    reqd_fields_by_ref[join_data[tx][REF]] = {join_data[tx][FIELD]}
                else:
                    reqd_fields_by_ref[join_data[tx][REF]].update(
                        [join_data[tx][FIELD]]
                    )

    if not joins:
        errors.append("no valid join data found")

    if errors:
        err_msg = PARAM_ERROR_MESSAGE + "\n".join(errors)
        raise RuntimeError(err_msg)

    if len(refs) > max_refs:
        err_msg = (
            PARAM_ERROR_MESSAGE
            + f"The Combinatrix is currently limited to combining {max_refs} datasets."
        )
        raise RuntimeError(err_msg)

    return {
        REFS: refs,
        JOIN_LIST: joins,
        REQD_FIELDS: reqd_fields_by_ref,
    }


def construct_graph(
    join_list: list[dict[str, Any]], max_connections: int = MAX_CONNECTIONS_PER_NODE
) -> Graph:
    """Generate a graph from the list of joins.

    :param join_list: list of dictionaries specifying the join information
    :type join_list: list[dict[str, Any]]
    :param max_connections: maximum number of connections between one dataset and another
    :type max_connections: int
    :raises RuntimeError: if any aspect of the join list is invalid
    :return: graph of the joins in the join_list
    :rtype: Graph
    """
    join_graph = nx.Graph()
    # keep a tally of how many refs each ref is connected to
    ref_counts = {}

    for join in join_list:
        for ref in [join[T1][REF], join[T2][REF]]:
            # update the counts
            if ref in ref_counts:
                ref_counts[ref] += 1
            else:
                ref_counts[ref] = 1

        join_graph.add_edge(join[T1][REF], join[T2][REF])

    too_many_connections = [
        ref for ref in ref_counts if ref_counts[ref] > max_connections
    ]
    if too_many_connections:
        too_many_connections.sort()
        err_msg = (
            "The following refs are connected to too many other refs:\n"
            + ", ".join(too_many_connections)
        )
        raise RuntimeError(err_msg)

    return join_graph


def find_longest_path_in_graph(
    join_list: list[dict[str, Any]], max_connections: int = MAX_CONNECTIONS_PER_NODE
) -> list[str]:
    """Find the longest path in a graph and return it as a list of nodes.

    :param join_list: list of dictionaries specifying the join information
    :type join_list: list[dict[str, Any]]
    :param max_connections: maximum number of connections between one dataset and another
    :type max_connections: int
    :raises RuntimeError: if the graph is cyclic or does not produce a tree
    :return: node sequence in the longest path
    :rtype: list[str]
    """
    join_graph = construct_graph(join_list, max_connections)

    # check that all edges are connected to at least one other edge
    # and that the graph forms a tree without cycles
    if not nx.is_connected(join_graph) or not nx.is_tree(join_graph):
        err_msg = "Error: the joins specified do not create a single dataset"
        raise RuntimeError(err_msg)

    # The graph is a tree; proceed with finding the longest path
    leaves = [node for node, degree in join_graph.degree() if degree == 1]
    farthest_leaf, _ = max(
        nx.single_source_shortest_path_length(join_graph, leaves[0]).items(),
        key=lambda x: x[1],
    )
    longest_path = max(
        nx.single_source_shortest_path(join_graph, farthest_leaf).values(), key=len
    )

    # the longest path can go in either direction, so order it according to which
    # of the end nodes appear first in discovered_refs
    # Check if last item of longest_path appears before the first item
    discovered_refs = [
        ref for item in join_list for key in [T1, T2] for ref in [item[key][REF]]
    ]
    if discovered_refs.index(longest_path[-1]) < discovered_refs.index(longest_path[0]):
        # Reverse longest_path
        longest_path.reverse()

    return longest_path


def sort_params(
    join_list: list[dict[str, Any]],
    max_connections: int = MAX_CONNECTIONS_PER_NODE,
) -> list[dict[str, Any]]:
    """Sort the join parameters into an appropriate order.

    :param join_list: list of dictionaries specifying the join information
    :type join_list: list[dict[str, Any]]
    :param max_connections: maximum number of connections between one dataset and another
    :type max_connections: int
    :return: sorted list of input params
    :rtype: list[dict[str, Any]]
    """
    longest_path = find_longest_path_in_graph(join_list, max_connections)

    # Create a mapping from node to its position in the path for easy lookup
    node_positions = {node: i for i, node in enumerate(longest_path)}

    # Sort and order join_list based on the node positions in the path
    sorted_and_ordered_params = []
    for join in join_list:
        t1, t2 = join[T1], join[T2]
        # Order refs within each join pair according to their position in the path
        if node_positions[join[T1][REF]] > node_positions[join[T2][REF]]:
            t1, t2 = t2, t1  # Swap to correct order
        sorted_and_ordered_params.append({T1: t1, T2: t2})

    # Sort the pairs themselves based on the position of the first ref in each pair
    sorted_and_ordered_params.sort(key=lambda join: node_positions[join[T1][REF]])

    return sorted_and_ordered_params


def check_params(
    params: dict[str, Any],
    max_refs: int = MAX_REFS,
    max_connections: int = MAX_CONNECTIONS_PER_NODE,
) -> dict[str, Any]:
    """Check the input parameters and order them sensibly.

    :param params: input parameters from the combinatrix app; we are interested in the 'join_list' value.
    :type params: dict[str, Any]
    :return: input parameters categorised, sorted, ordered, and generally coerced into an appropriate state for further processing
    :rtype: dict[str, Any]
    """
    validated_params = validate_params(params, max_refs)
    sorted_params = sort_params(
        validated_params[JOIN_LIST],
        max_connections,
    )
    validated_params[JOIN_LIST] = sorted_params

    return validated_params
