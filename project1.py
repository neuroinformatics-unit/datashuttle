from textual.app import App
from textual.containers import Container
from textual.widgets import Button, Label, Select, Log, ProgressBar
import asyncio

# Define required folders for validation
REQUIRED_FOLDERS = ["data", "scripts", "docs"]

class SimpleTUI(App):
    def compose(self):
        """Create the UI components."""
        yield Container(
            Label("Select Project Directory:"),
            Select(
                options=[("Project A", "A"), ("Project B", "B"), ("Project C", "C")],
                id="folder_select",
            ),
            Button("Validate Structure", id="validate_button"),
            Button("Start File Transfer", id="transfer_button"),
            ProgressBar(id="progress", total=100),
            Log(id="log_window"),
        )

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button clicks."""
        if event.button.id == "validate_button":
            await self.validate_structure()
        elif event.button.id == "transfer_button":
            await self.simulate_transfer()

    async def validate_structure(self):
        """Check if required folders exist and log the result."""
        log_window = self.query_one("#log_window", Log)
        log_window.clear()
        log_window.write("Checking project structure...")
        await asyncio.sleep(1)  # Simulate checking process
        missing_folders = [folder for folder in REQUIRED_FOLDERS]
        if missing_folders:
            log_window.write(f"Missing folders: {', '.join(missing_folders)}")
        else:
            log_window.write("Project structure is valid!")

    async def simulate_transfer(self):
        """Simulate file transfer progress."""
        progress = self.query_one("#progress", ProgressBar)
        log_window = self.query_one("#log_window", Log)
        log_window.clear()
        log_window.write("Starting file transfer...")
        for i in range(0, 101, 20):
            progress.progress = i
            log_window.write(f"Transferred {i}%")
            await asyncio.sleep(0.5)
        log_window.write("File transfer complete!")

if __name__ == "__main__":
    app = SimpleTUI()
    app.run()
