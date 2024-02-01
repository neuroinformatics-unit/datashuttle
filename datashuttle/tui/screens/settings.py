from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    RadioButton,
    RadioSet,
)


class SettingsScreen(ModalScreen):
    def __init__(self, mainwindow):
        super(SettingsScreen, self).__init__()

        self.mainwindow = mainwindow
        self.global_settings = self.mainwindow.load_global_settings()

    def compose(self):
        dark_mode = self.global_settings["dark_mode"]
        yield Container(
            RadioSet(
                RadioButton(
                    "Dark Mode",
                    value=dark_mode,
                ),
                RadioButton(
                    "Light Mode",
                    value=not dark_mode,
                ),
                id="settings_color_scheme_radioset",
            ),
            Checkbox(
                "Show transfer status on directory tree",
                value=self.global_settings["show_transfer_tree_status"],
            ),
            Button("Close", id="settings_screen_close_button"),
            id="settings_screen_top_container",
        )

    def on_radio_set_changed(self, event):
        label = str(event.pressed.label)
        assert label in ["Light Mode", "Dark Mode"]
        dark_mode = label == "Dark Mode"
        self.mainwindow.dark = dark_mode
        self.global_settings["dark_mode"] = dark_mode
        self.mainwindow.save_global_settings(self.global_settings)

    def on_checkbox_changed(self, event):
        self.global_settings["show_transfer_tree_status"] = event.value
        self.mainwindow.save_global_settings(self.global_settings)

    def on_button_pressed(self, event):
        if event.button.id == "settings_screen_close_button":
            self.dismiss()
