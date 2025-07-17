from datashuttle.utils import utils

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Python API
# -----------------------------------------------------------------------------


def ask_user_for_browser(log: bool = True) -> bool:
    """Ask the user if they have access to an internet browser, for Google Drive set up."""
    message = "Are you running Datashuttle on a machine with access to a web browser? (y/n): "
    input_ = utils.get_user_input(message).lower()

    while input_ not in ["y", "n"]:
        utils.print_message_to_user("Invalid input. Press either 'y' or 'n'.")
        input_ = utils.get_user_input(message).lower()

    answer = input_ == "y"

    if log:
        utils.log(message)
        utils.log(f"User answer: {answer}")

    return answer


def prompt_and_get_service_account_filepath(log: bool = True):
    """Get service account filepath from user."""
    message = "Please enter your service account file path: "
    input_ = utils.get_user_input(message).strip()

    if log:
        utils.log(message)
        utils.log(f"Service account file at: {input_}")

    return input_


def get_client_secret(log: bool = True) -> str:
    """Prompt the user for their Google Drive client secret key."""
    gdrive_client_secret = utils.get_connection_secret_from_user(
        connection_method_name="Google Drive",
        key_name_full="Google Drive client secret",
        key_name_short="secret key",
        log_status=log,
    )

    return gdrive_client_secret.strip()
