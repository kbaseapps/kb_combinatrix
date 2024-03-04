"""Fetches, combines, masticates, and spits out the appropriate data structure."""

from typing import Any

from combinatrix.constants import DL, FIELD, JOIN_LIST, REF, REQD_FIELDS, T1, T2
from pandas import DataFrame


def suffix(original_str: str, ref: str) -> str:
    """Add a suffix to a string.

    :param original_str: the string to add the suffix to
    :type ref: str
    :param ref: the suffix to add (e.g. a KBase ref)
    :type ref: str
    :return: the suffixed string
    :rtype: str
    """
    return f"{ref}__{original_str}"


def generate_combination_string(join: dict[str, Any]) -> str:
    """Generate a string from a set of join parameters.

    :param join: dictionary with keys T1 and T2, each of which has fields REF and FIELD
    :type join: dict[str, Any]
    :return: string of the combined values
    :rtype: str
    """
    return (
        f"{join[T1][REF]} '{join[T1][FIELD]}' and {join[T2][REF]} '{join[T2][FIELD]}'"
    )


def combine_data(
    join_params: dict[str, Any],
    combined_data: dict[str, Any],
) -> dict[str, Any]:
    """Combine datasets from the different sources together and check for intersections.

    :param join_params: join parameters
    :type join_params: dict[str, Any]
    :param combined_data: dict containing standardised data for each dataset, indexed by KBase ref
    :type combined_data: dict[str, Any]
    :raises RuntimeError: if required fields are missing
    :raises RuntimeError: if there are no intersections between datasets
    """
    ## Matrix: list of {"row_id": x, "col_id": y, "value": z}
    ## Sampleset: list of {"sample_id": x, "field_2": y, "field_3": z, ...}
    ##

    dataframes: dict[str, DataFrame] = {}
    reqd_fields_by_ref = join_params[REQD_FIELDS]
    all_err_list = []
    for ref in reqd_fields_by_ref:
        if ref not in dataframes:
            dataframes[ref] = DataFrame(combined_data[ref][DL])
        # make sure all fields are present
        missing_fields = [
            f for f in reqd_fields_by_ref[ref] if f not in dataframes[ref].columns
        ]
        if missing_fields:
            all_err_list.append(
                f"{ref}: fields not found: " + ", ".join(sorted(missing_fields))
            )

    if all_err_list:
        err_msg = "Errors in dataset field specifications:\n" + "\n".join(all_err_list)
        raise RuntimeError(err_msg)

    # add a suffix to all the columns so we can track their origins
    for ref in dataframes:
        renamed_cols = dataframes[ref].rename(columns=lambda x: suffix(x, ref))
        dataframes[ref] = renamed_cols

    # initialise the megamerged dataframe with the first dataset on the join list
    df_merged = dataframes[join_params[JOIN_LIST][0][T1][REF]]
    # join each pair of datasets to ensure there is an overlap,
    # and keep a cumulative joined dataset
    for join in join_params[JOIN_LIST]:
        try:
            temp_df = dataframes[join[T1][REF]].merge(
                dataframes[join[T2][REF]],
                left_on=suffix(join[T1][FIELD], join[T1][REF]),
                right_on=suffix(join[T2][FIELD], join[T2][REF]),
                how="inner",
                validate="many_to_many",
            )
            if not len(temp_df):
                all_err_list.append(generate_combination_string(join))

            # merge dataframes into the megamerged version
            df_merged = df_merged.merge(
                dataframes[join[T2][REF]],
                left_on=suffix(join[T1][FIELD], join[T1][REF]),
                right_on=suffix(join[T2][FIELD], join[T2][REF]),
                how="inner",
                validate="m:m",
            )

        except ValueError as e:
            all_err_list.append(generate_combination_string(join) + ": " + e.args[0])

    if all_err_list:
        err_msg = (
            "No matching values found between the following datasets:\n"
            + "\n".join(all_err_list)
        )
        raise RuntimeError(err_msg)

    matched_ids = {}
    for ref in dataframes:
        # extract the matched IDs from each dataframe
        matched_ids[ref] = set(df_merged[suffix("id", ref)].dropna())

    return matched_ids
