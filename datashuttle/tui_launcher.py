import argparse

from datashuttle.tui.app import main as tui_main

# -----------------------------------------------------------------------------
# Entry Point to the CLI
# -----------------------------------------------------------------------------

description = (
    "-----------------------------------------------------------------------\n"
    "Use `datashuttle launch` to start datashuttle.\n"
    "-----------------------------------------------------------------------\n"
)

parser = argparse.ArgumentParser(
    prog="datashuttle",
    usage="%(prog)s launch",
    description=description,
    formatter_class=argparse.RawTextHelpFormatter,
)

parser.add_argument(
    dest="launch",
)

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------


def main() -> None:
    """Launch the datashuttle tui."""
    args = parser.parse_args()

    if args.launch == "launch":
        tui_main()
    else:
        raise ValueError(
            "Command not recognised. Launch datashuttle with "
            "`datashuttle launch`."
        )


if __name__ == "__main__":
    main()
