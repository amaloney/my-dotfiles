// Adds vim navigation to the Super+Tab app switcher (AppSwitcherPopup).
//
//   h / l  previous / next app (or previous / next window when windows are shown)
//   j      show the selected app's windows (only when it has more than one)
//   k      go back from the window list to the app list
//
// The keys are mapped to the arrow keys the switcher already handles.
import Clutter from 'gi://Clutter';

import * as AltTab from 'resource:///org/gnome/shell/ui/altTab.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const VIM_TO_ARROW = new Map([
    [Clutter.KEY_h, Clutter.KEY_Left],
    [Clutter.KEY_H, Clutter.KEY_Left],
    [Clutter.KEY_j, Clutter.KEY_Down],
    [Clutter.KEY_J, Clutter.KEY_Down],
    [Clutter.KEY_k, Clutter.KEY_Up],
    [Clutter.KEY_K, Clutter.KEY_Up],
    [Clutter.KEY_l, Clutter.KEY_Right],
    [Clutter.KEY_L, Clutter.KEY_Right],
]);

export default class VimAppSwitcherExtension extends Extension {
    enable() {
        const proto = AltTab.AppSwitcherPopup.prototype;
        const original = proto._keyPressHandler;
        this._original = original;

        proto._keyPressHandler = function (keysym, action) {
            const arrow = VIM_TO_ARROW.get(keysym);
            if (arrow === undefined)
                return original.call(this, keysym, action);

            if (arrow === Clutter.KEY_Down && !this._thumbnailsFocused) {
                const windows = this._items[this._selectedIndex]?.cachedWindows ?? [];
                if (windows.length < 2)
                    return Clutter.EVENT_STOP;
            }
            // Pass no action so a binding such as Super+H (minimize) cannot
            // override the navigation key.
            return original.call(this, arrow, null);
        };
    }

    disable() {
        AltTab.AppSwitcherPopup.prototype._keyPressHandler = this._original;
        this._original = null;
    }
}
