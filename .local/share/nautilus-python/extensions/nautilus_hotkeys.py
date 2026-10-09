# """In-Nautilus hotkeys: folder jumps, tab reorder accels, and type-ahead.
#
# Install: ~/.local/share/nautilus-python/extensions/
# Reload:  nautilus -q && nautilus
# Debug:   NAUTILUS_PYTHON_DEBUG=misc nautilus
#
# Nautilus >= 43 (extension API 4.x) exposes no window to extensions, so:
# - accelerators go through GtkApplication on Nautilus' own GActions
#   (the active tab's action group is inserted on the window as "slot.*")
# - type-ahead is a CAPTURE-phase key controller on each NautilusWindow
#   that runs before Nautilus' BUBBLE-phase search-on-type handler
# """
# import gi
#
# gi.require_version("Gdk", "4.0")
# gi.require_version("Gtk", "4.0")
# from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Nautilus
#
# # --------------------------------------------------------------------- config
#
# # accel -> GLib special dir or absolute path (current tab navigates in place)
# FOLDER_BINDINGS = {
#     "<Control><Alt>d": GLib.UserDirectory.DIRECTORY_DOCUMENTS,
# }
#
# # Nautilus action -> extra accels (appended, defaults kept)
# ACTION_BINDINGS = {
#     "win.tab-move-left": ["<Shift><Super>bracketleft"],
#     "win.tab-move-right": ["<Shift><Super>bracketright"],
# }
#
# # Typing in the file list selects the first matching file instead of
# # opening the search box. Buffer resets after this many ms of inactivity.
# TYPEAHEAD = True
# TYPEAHEAD_TIMEOUT_MS = 1000
#
# _BLOCKING_MODS = (
#     Gdk.ModifierType.CONTROL_MASK
#     | Gdk.ModifierType.ALT_MASK
#     | Gdk.ModifierType.SUPER_MASK
#     | Gdk.ModifierType.META_MASK
# )
#
# _installed = False
#
# # ---------------------------------------------------------------- accelerators
#
#
# def _target_uri(target):
#     if isinstance(target, GLib.UserDirectory):
#         path = GLib.get_user_special_dir(target)
#     else:
#         path = target
#     return Gio.File.new_for_path(path).get_uri()
#
#
# def _add_accels(app, detailed_action, accels):
#     current = list(app.get_accels_for_action(detailed_action))
#     new = [a for a in accels if a not in current]
#     app.set_accels_for_action(detailed_action, current + new)
#
#
# def _install_accels(app):
#     for action, accels in ACTION_BINDINGS.items():
#         _add_accels(app, action, accels)
#     for accel, target in FOLDER_BINDINGS.items():
#         detailed = Gio.Action.print_detailed_name(
#             "slot.open-location", GLib.Variant("s", _target_uri(target))
#         )
#         _add_accels(app, detailed, [accel])
#     return GLib.SOURCE_REMOVE  # usable as an idle callback
#
#
# # ------------------------------------------------------------------ type-ahead
#
#
# def _find_view(widget):
#     """Nearest GtkColumnView/GtkGridView ancestor of widget, or None."""
#     while widget is not None:
#         if isinstance(widget, (Gtk.ColumnView, Gtk.GridView)):
#             return widget
#         widget = widget.get_parent()
#     return None
#
#
# def _item_name(item):
#     if isinstance(item, Gtk.TreeListRow):
#         item = item.get_item()
#     file = item.get_property("file")  # NautilusViewItem:file -> NautilusFile
#     return Nautilus.FileInfo.get_name(file)
#
#
# def _selected_index(model):
#     sel = model.get_selection()
#     if sel.is_empty():
#         return -1
#     return sel.get_minimum()
#
#
# def _select(view, index):
#     flags = Gtk.ListScrollFlags.SELECT | Gtk.ListScrollFlags.FOCUS
#     if isinstance(view, Gtk.ColumnView):
#         view.scroll_to(index, None, flags, None)
#     else:
#         view.scroll_to(index, flags, None)
#
#
# class _TypeAhead:
#     def __init__(self):
#         self.buffer = ""
#         self.timeout_id = 0
#
#     def _reset(self):
#         self.buffer = ""
#         self.timeout_id = 0
#         return GLib.SOURCE_REMOVE
#
#     def _touch(self):
#         if self.timeout_id:
#             GLib.source_remove(self.timeout_id)
#         self.timeout_id = GLib.timeout_add(TYPEAHEAD_TIMEOUT_MS, self._reset)
#
#     def _search(self, view):
#         model = view.get_model()
#         n = model.get_n_items()
#         if n == 0:
#             return
#         needle = self.buffer.lower()
#         start = 0
#         # same key repeated -> cycle through matches from current selection
#         if len(needle) > 1 and needle == needle[0] * len(needle):
#             needle = needle[0]
#             start = _selected_index(model) + 1
#         for offset in range(n):
#             i = (start + offset) % n
#             try:
#                 name = _item_name(model.get_item(i))
#             except Exception:
#                 continue
#             if name.lower().startswith(needle):
#                 _select(view, i)
#                 return
#
#     def on_key_pressed(self, controller, keyval, _keycode, state):
#         window = controller.get_widget()
#         view = _find_view(window.get_focus())
#         if view is None or state & _BLOCKING_MODS:
#             return Gdk.EVENT_PROPAGATE
#
#         if keyval == Gdk.KEY_BackSpace and self.buffer:
#             self.buffer = self.buffer[:-1]
#             self._touch()
#             return Gdk.EVENT_STOP
#
#         ch = chr(Gdk.keyval_to_unicode(keyval) or 0)
#         if not ch.isprintable() or ch.isspace():
#             return Gdk.EVENT_PROPAGATE
#
#         self.buffer += ch
#         self._touch()
#         self._search(view)
#         return Gdk.EVENT_STOP
#
#
# def _install_typeahead(window):
#     if getattr(window, "_typeahead_installed", False):
#         return
#     if GObject.type_name(window) != "NautilusWindow":
#         return
#     window._typeahead_installed = True
#
#     ctl = Gtk.EventControllerKey()
#     ctl.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
#     ctl.connect("key-pressed", _TypeAhead().on_key_pressed)
#     window.add_controller(ctl)
#
#
# # --------------------------------------------------------------------- wiring
#
#
# def _install():
#     global _installed
#     if _installed:
#         return
#     app = Gio.Application.get_default()
#     if not isinstance(app, Gtk.Application):
#         return
#     _installed = True
#
#     def on_window(app, window):
#         # NautilusWindow's constructor emits window-added *before* it
#         # resets the app accels (nautilus_window_initialize_actions), so
#         # re-merge from idle, after the constructor returns. Idempotent.
#         GLib.idle_add(_install_accels, app)
#         if TYPEAHEAD:
#             _install_typeahead(window)
#
#     _install_accels(app)
#     for w in app.get_windows():
#         on_window(app, w)
#     app.connect("window-added", on_window)
#
#
# class HotkeyFolders(GObject.GObject, Nautilus.MenuProvider):
#     """No-op provider: keeps the module registered and retries _install
#     if the app wasn't available at import time."""
#
#     def get_background_items(self, current_folder):
#         _install()
#         return []
#
#     def get_file_items(self, files):
#         _install()
#         return []
#
#
# _install()
