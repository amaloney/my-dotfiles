from gi.repository import Gio, GObject, Nautilus

SUPPORTED_FORMATS = "image/jpeg", "image/png"
BACKGROUND_SCHEMA = "org.gnome.desktop.background"
BACKGROUND_KEY = "picture-uri"


class BackgroundImageExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        super().__init__()
        self.bgsettings = Gio.Settings.new(BACKGROUND_SCHEMA)

    def menu_activate_cb(self, menu: Nautilus.MenuItem, file: Nautilus.FileInfo) -> None:
        if file.is_gone():
            return

        self.bgsettings[BACKGROUND_KEY] = file.get_uri()

    def get_file_items(self, files: list[Nautilus.FileInfo]) -> list[Nautilus.MenuItem]:
        if len(files) != 1:
            return []

        file = files[0]
        if not file.get_mime_type() in SUPPORTED_FORMATS:
            return []

        if file.get_uri_scheme() != "file":
            return []

        item = Nautilus.MenuItem(name="Nautilus::set_background_image", label="Use as background image")
        item.connect("activate", self.menu_activate_cb, file)

        return [item]

    def get_background_items(self, current_folder: Nautilus.FileInfo) -> list[Nautilus.MenuItem]:
        return []
