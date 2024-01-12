import copy


def get_textual_compatible_project_configs(project_cfg):
    """
    This uses a datashuttle function to convert any pathlib to
    strings. Textualize inputs cannot take Path type. This
    conversion is in-place so configs must be copied.
    """

    cfg_to_load = copy.deepcopy(project_cfg)
    project_cfg.convert_str_and_pathlib_paths(cfg_to_load, "path_to_str")
    return cfg_to_load
