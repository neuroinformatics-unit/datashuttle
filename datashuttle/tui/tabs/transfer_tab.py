from textual.widgets import Label, TabPane


class TransferTab(TabPane):
    def __init__(self, mainwindow, project):
        super(TransferTab, self).__init__(
            "Transfer", id="tabscreen_transfer_tab"
        )
        self.mainwindow = mainwindow
        self.project = project

    def compose(self):
        yield Label("Transfer; Seems to work!")
