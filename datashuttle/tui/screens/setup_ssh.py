from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Static,
)


class SetupSshScreen(ModalScreen):
    def __init__(self, project):
        super(SetupSshScreen, self).__init__()

        self.project = project
        self.stage = 0
        self.failed_password_attempts = 1

    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Static(
                    "Ready to setup setup SSH. " "Press OK to proceed.",
                    id="messagebox_message_label",
                ),
                id="messagebox_message_container",
            ),
            Input("Test", password=True, id="input"),
            Horizontal(
                Button("OK", id="setup_ssh_ok_button"),
                Button("Cancel", id="setup_ssh_cancel_button"),
                id="horizontal_XXX",
            ),
            id="setup_ssh_screen_container",
        )

    def on_mount(self):
        self.query_one("#input").visible = False

    def on_button_pressed(self, event):
        # TODO: retest ssh setup! also why are these skipped?

        if event.button.id == "setup_ssh_cancel_button":
            self.dismiss()

        if event.button.id == "setup_ssh_ok_button":
            from datashuttle.utils import ssh

            central_host_id = self.project.cfg["central_host_id"]

            if self.stage == 0:
                try:
                    self.key = ssh.get_remote_server_key(central_host_id)
                    # TODO: this message is direct copy from datashuttle!
                    # except 'y' goes to 'OK'
                    message = (
                        f"The host key is not cached for this server: "
                        f"{central_host_id}.\nYou have no guarantee "
                        f"that the server is the computer you think it is.\n"
                        f"The server's {self.key.get_name()} key fingerprint is:\n\n "
                        f"{self.key.get_base64()}\n\nIf you trust this host, to connect"
                        f" and cache the host key, press OK: "
                    )
                except BaseException as e:
                    self.query_one("#setup_ssh_ok_button").disabled = True
                    message = (
                        "Could not connect to server. \nCheck the connection "
                        f"and the central host ID : \n\n{central_host_id} \n\n Traceback: {e}"
                    )

                self.query_one("#messagebox_message_label").update(message)
                self.stage = 1

            elif self.stage == 1:
                try:
                    ssh.save_hostkey_locally(
                        self.key,
                        central_host_id,
                        self.project.cfg.hostkeys_path,
                    )
                    message = (
                        "Hostkey accepted. \n\nNext, input your password to the server "
                        "below to setup an SSH key pair. You will not need to enter "
                        "your password again. Press OK to confirm"
                    )
                    self.query_one("#input").visible = True
                except BaseException as e:
                    self.query_one("#setup_ssh_ok_button").disabled = True
                    message = (
                        f"Could not store host key. Check permissions "
                        f"to: \n\n {self.project.cfg.hostkeys_path}.\n\n Traceback: {e}"
                    )

                self.query_one("#messagebox_message_label").update(message)
                self.stage += 1

            elif self.stage == 2:
                try:
                    ssh.generate_and_write_ssh_key(
                        self.project.cfg.ssh_key_path
                    )
                    #  key = paramiko.RSAKey.from_private_key_file(
                    #      cfg.ssh_key_path.as_posix())
                    password = self.query_one("#input").value

                    ssh.add_public_key_to_central_authorized_keys(
                        self.project.cfg, password, self.key
                    )
                    self.project._setup_rclone_central_ssh_config(log=True)

                    message = (
                        f"Connection successful! SSH key "
                        f"saved to {self.project.cfg.ssh_key_path}"
                    )
                    self.query_one("#setup_ssh_ok_button").label = "Finish"
                    self.query_one("#setup_ssh_cancel_button").disabled = True
                    self.stage += 1
                except BaseException as e:
                    message = (
                        f"Password setup failed. Check password is correct and try again."
                        f"\n\n{self.failed_password_attempts} failed password attempts."
                        f"\n\n Traceback: {e}"
                    )
                    self.failed_password_attempts += 1

                self.query_one("#messagebox_message_label").update(message)

            elif self.stage == 3:
                self.dismiss()
