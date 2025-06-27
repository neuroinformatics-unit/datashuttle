from pathlib import Path

from datashuttle import DataShuttle

project = DataShuttle("example_project")

this_file_path = Path(__file__)

if not project.cfg:  # TODO: make a convenience func for this
    project.make_config_file(
        this_file_path.parent / "example_project",
    )

project.convert(Path(this_file_path))
