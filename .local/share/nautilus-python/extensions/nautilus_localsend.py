import subprocess

from gi.repository import GObject, Nautilus

# Check Nautilus version compatibility (required)
if not (Nautilus._version.startswith("3.") or Nautilus._version.startswith("4.")):
    msg = f"Nautilus requires 3 or 4, got {Nautilus._version}"
    raise ValueError(msg)


class LocalSendExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self) -> None:
        super().__init__()

    def menu_activate_cb(
        self, menu_item: Nautilus.MenuItem, selected_files: list
    ) -> None:
        self._send_with_localsend(menu_item, selected_files)

    def get_file_items(
        self,
        selected_files: list[Nautilus.FileInfo],
    ) -> list:
        # Don't show the menu item if nothing is selected
        if len(selected_files) == 0:
            return []

        # Check if all selected items have valid file paths
        file_paths = []
        for selected_file in selected_files:
            file_path = selected_file.get_location().get_path()
            if file_path is None:
                continue
            file_paths.append(file_path)

        # Create the Nautilus menu item
        label = "Send with LocalSend"
        if len(selected_files) > 1:
            label = f"Send {len(selected_files)} items with LocalSend"
        menu_item = Nautilus.MenuItem(name="LocalSend::send_files", label=label)
        menu_item.connect("activate", self.menu_activate_cb, file_paths)

        return [menu_item]

    # Even though we're not using background items, Nautilus will generate
    # a warning if the method isn't present
    def get_background_items(
        self,
        current_folder: Nautilus.FileInfo,
    ) -> list:
        return []

    def _send_with_localsend(self, menu_item, file_paths: list):
        """Send files using LocalSend"""
        try:
            command = ["/usr/bin/localsend"] + file_paths
            subprocess.Popen(command)

        except Exception as e:
            print(f"Failed to send files with LocalSend: {e}")
