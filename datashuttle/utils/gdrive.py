import json

from datashuttle.configs.config_class import Configs
from datashuttle.utils import rclone, utils


def preliminary_for_setup_without_browser(
    cfg: Configs, rclone_config_name: str, log: bool = True
):
    client_id_key_value = (
        f"client_id {cfg['gdrive_client_id']} "
        if cfg.get("gdrive_client_id", None)
        else " "
    )
    client_secret_key_value = (
        f"client_secret {cfg['gdrive_client_secret']} "
        if cfg.get("gdrive_client_secret", None)
        else ""
    )
    output = rclone.call_rclone(
        f"config create "
        f"{rclone_config_name} "
        f"drive "
        f"{client_id_key_value}"
        f"{client_secret_key_value}"
        f"scope drive "
        f"config_is_local=false "
        f"--non-interactive",
        pipe_std=True,
    )

    # TODO: make this more robust
    output_json = json.loads(output.stdout)
    message = output_json["Option"]["Help"]

    if log:
        utils.log(message)

    return message


# -----------------------------------------------------------------------------
# Python API
# -----------------------------------------------------------------------------


def ask_user_for_browser(log: bool = True) -> bool:
    message = "Are you running Datashuttle on a machine with access to a web browser? (y/n): "
    input_ = utils.get_user_input(message).lower()

    while input_ not in ["y", "n"]:
        utils.print_message_to_user("Invalid input. Press either 'y' or 'n'.")
        input_ = utils.get_user_input(message).lower()

    if input_ == "y":
        answer = True
    else:
        answer = False

    if log:
        utils.log(message)

    return answer


def prompt_and_get_config_token(
    cfg: Configs, rclone_config_name: str, log: bool = True
) -> str:
    message = preliminary_for_setup_without_browser(
        cfg, rclone_config_name, log=log
    )
    input_ = utils.get_user_input(message).strip()

    return input_
