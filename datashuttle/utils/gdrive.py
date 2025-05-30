import getpass
import json
import sys

from datashuttle.configs.config_class import Configs
from datashuttle.utils import rclone, utils

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

# These functions are used by both API and TUI for setting up connections to google drive.


def preliminary_for_setup_without_browser(
    cfg: Configs,
    gdrive_client_secret: str | None,
    rclone_config_name: str,
    log: bool = True,
) -> str:
    # TODO: Add docstrings
    client_id_key_value = (
        f"client_id {cfg['gdrive_client_id']} "
        if cfg["gdrive_client_id"]
        else " "
    )
    client_secret_key_value = (
        f"client_secret {gdrive_client_secret} "
        if gdrive_client_secret
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
        utils.log(f"User answer: {answer}")

    return answer


def prompt_and_get_config_token(
    cfg: Configs,
    gdrive_client_secret: str | None,
    rclone_config_name: str,
    log: bool = True,
) -> str:
    # TODO: Add docstrings
    message = preliminary_for_setup_without_browser(
        cfg, gdrive_client_secret, rclone_config_name, log=log
    )
    input_ = utils.get_user_input(message).strip()

    return input_


def get_client_secret(log: bool = True) -> str:
    if not sys.stdin.isatty():
        proceed = input(
            "\nWARNING!\nThe next step is to enter a google drive client secret, but it is not possible\n"
            "to hide your client secret while entering it in the current terminal.\n"
            "This can occur if running the command in an IDE.\n\n"
            "Press 'y' to proceed to client secret entry. "
            "The characters will not be hidden!\n"
            "Alternatively, run ssh setup after starting Python in your "
            "system terminal \nrather than through an IDE: "
        )
        if proceed != "y":
            utils.print_message_to_user(
                "Quitting google drive setup as 'y' not pressed."
            )
            utils.log_and_raise_error(
                "Google Drive setup aborted by user.", ConnectionAbortedError
            )

        gdrive_client_secret = input(
            "Please enter your google drive client secret. Characters will not be hidden: "
        )

    else:
        gdrive_client_secret = getpass.getpass(
            "Please enter your google drive client secret: "
        )

    if log:
        utils.log("Google Drive client secret entered by user.")

    return gdrive_client_secret.strip()
