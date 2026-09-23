from gi.repository import GObject, Nautilus

if not (Nautilus._version.startswith("3.") or Nautilus._version.startswith("4.")):
    msg = f"Nautilus requires 3 or 4, got {Nautilus._version}"
    raise ValueError(msg)


class LocalSendExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self) -> None:
        super().__init__()

    def menu_activate_cb(self, menu_item: Nautilus.MenuItem, selected_file_paths: list) -> None:
        try:
            command = ["/usr/bin/localsend"] + file_paths
            subprocess.Popen(command)

        except Exception as e:
            print(f"Failed to send files with LocalSend: {e}")

    def get_file_items(self, selected_files: list[Nautilus.FileInfo]) -> list:
        # Don't show the menu item if nothing is selected
        if len(selected_files) == 0:
            return []

        # Check if all selected items have valid file paths
        selected_file_paths = []
        for selected_file in selected_files:
            selected_file_path = selected_file.get_location().get_path()
            if selected_file_path is None:
                continue
            selected_file_paths.append(selected_file_path)

        # Create the Nautilus menu item
        label = "Send with LocalSend"
        if len(selected_files) > 1:
            label = f"Send {len(selected_files)} items with LocalSend"
        menu_item = Nautilus.MenuItem(name="LocalSend::send_files", label=label)
        menu_item.connect("activate", self.menu_activate_cb, selected_file_paths)

        return [menu_item]

    def get_background_items(self, current_folder: Nautilus.FileInfo) -> list:
        return []
