import csv
import io
import json
import re
import sys
import tomllib
from datetime import datetime
from pathlib import Path

import pytz
from jsonschema import exceptions as jsonschema_exceptions
from jsonschema import validate
from rich.pretty import pprint

from .json_schema_str import JSON_SCHEMA_STR

CONFIG_FILE = Path.home() / ".config/csv_term_tagger/csv_term_tagger.toml"


def get_toml_data(*, config_path) -> dict:
    if not Path.exists(config_path):
        pprint(f"Whoops, no config file exists at {config_path}")
        pprint(
            "Please see the repo directions and make sure you have the config file in this location.",
        )
        sys.exit(1)

    try:
        with Path.open(config_path, "rb") as f:
            toml_data = tomllib.load(f)
    except OSError as e:
        msg = "Problem with loading toml data from the config file. Please check the settings in your toml file to ensure they match the example toml file in the repo."
        raise OSError(msg) from e

    return toml_data


def validate_toml_data(*, toml_data, json_schema):
    try:
        validate(instance=toml_data, schema=json_schema)
        # print("TOML file is valid against the schema.")
    except jsonschema_exceptions.ValidationError as e:
        print(f"TOML file Validation error: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        pprint("Whoops, no input file path passed in.")
        pprint("Usage: csv_term_tagger <input-file-path>")
        pprint("Example: csv_term_tagger Z:/term_tag_me.csv")
        sys.exit(1)

    # grab the bu number passed in and clean it up
    file_path = sys.argv[1]
    file_path = file_path.strip()
    run(csv_file_path=file_path)


def get_dated_output_file_path(*, filename_prefix: str) -> Path:
    home_dir = Path.home()

    # Assuming us central
    timezone_name = "US/Central"
    # Create a tzinfo object from the timezone name
    tz = pytz.timezone(timezone_name)

    dt_str = datetime.now(tz=tz).strftime("%Y%m%d_%H%M%S")
    consolidated_file_path = home_dir / f"Documents/{filename_prefix}_{dt_str}.csv"

    return consolidated_file_path


def gen_tags_terms_dict_from_toml(*, toml_tag_terms):
    """Generate a tag:list[terms] dict from toml dict."""
    # make a dict with cleaned up tags as keys and terms as values
    tag_terms = {}
    for one_dict in toml_tag_terms:
        # re.sub replaces all whitespace with underscore
        # lower changes to lowercase
        clean_tag = re.sub(r"\s+", "_", one_dict["tag"]).lower()
        tag_terms[clean_tag] = one_dict["terms"]
    return tag_terms


def run(*, csv_file_path):
    """Accepts CSV file to process and generates new CSV file with tags column based upon found terms."""
    toml_data = get_toml_data(config_path=CONFIG_FILE)

    json_schema = json.load(io.StringIO(JSON_SCHEMA_STR))

    validate_toml_data(toml_data=toml_data, json_schema=json_schema)

    out_records = []  # store the row info and dump to file at the end only if no errors

    # Open the CSV file in read mode ('r') with universal newline support
    with Path.open(csv_file_path) as reader_file:
        overwriting = False
        reader = csv.DictReader(reader_file)
        headers = reader.fieldnames
        search_column = toml_data["processing_info"]["search_column"]

        if search_column not in headers:
            pprint(
                f"Whoops, the input file doesn't have have a search_column named '{search_column}' (from toml).",
            )
            pprint(
                "Looks like you need to fix your config toml file or CSV file headers.",
            )
            pprint("Found these headers in your CSV:")
            pprint(headers)
            sys.exit(1)

        tags_column = toml_data["processing_info"]["tags_column"]
        overwrite_tags_column = toml_data["processing_info"]["overwrite_tags_column"]

        if tags_column in headers and overwrite_tags_column != "Y":
            pprint(
                f"Whoops, your config toml has 'overwrite_tags_column' set to '{overwrite_tags_column}' and your CSV already has a column named '{tags_column}'.",
            )
            pprint(
                f"You need to allow overwritting, change the tags_column, or remove/rename the '{tags_column}' column in your CSV file.",
            )
            sys.exit(1)

        if tags_column in headers and overwrite_tags_column == "Y":
            overwriting = True

        tag_terms = gen_tags_terms_dict_from_toml(toml_tag_terms=toml_data["tag_terms"])
        tags = tag_terms.keys()

        for row in reader:
            found_tags = set()

            for one_tag in tags:
                search_terms = tag_terms[one_tag]

                for one_term in search_terms:
                    # \\b matches a word boundary (space, punctuation, start/end of string)
                    # re.IGNORECASE makes the search case-insensitive
                    pattern = r"\b" + re.escape(one_term) + r"\b"
                    if re.search(pattern, row[search_column], re.IGNORECASE):
                        found_tags.add(one_tag)

            if found_tags:
                escaped_tag_string = "|".join(sorted(found_tags))
                row[tags_column] = escaped_tag_string
            else:
                row[tags_column] = ""

            out_records.append(row)

        # for item in out_records:
        #    print(item)

        out_file = get_dated_output_file_path(filename_prefix="term_tagger_results")

        with Path.open(out_file, "w", newline="") as csvfile:
            if not overwriting:
                # the tags column header doesn't exist, so we need to add it
                headers = [*headers, tags_column]
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(out_records)

        pprint(f"Wrote output to {out_file}")


if __name__ == "__main__":
    main()
