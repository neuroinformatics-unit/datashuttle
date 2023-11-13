from textual.widgets import Label, TabPane


class TransferTab(TabPane):
    def __init__(self):
        super(TransferTab, self).__init__(
            "Transfer", id="tabscreen_transfer_tab"
        )

    def compose(self):
        yield Label("Transfer; Seems to work!")
