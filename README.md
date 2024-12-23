# my-dotfiles

Personal dotfiles. I'm a fan of having a nice prompt that tells me lots of information.

- present working directory (with truncation)
- git branch
- conda/mamba environment
- workspace name (if on Linux)
- date & time

[Screencast From 2024-09-25 12-03-43.webm](https://github.com/user-attachments/assets/c6bd57a0-8082-44a3-a625-c91c82c82463)

## Ranger

The console file manager [ranger](https://github.com/ranger/ranger) is an excellent tool
with VI key bindings. Sometimes I want it to function outside of my main terminal, which
is easy enough to do by opening a different terminal, using `tmux`, or using a new
terminal tab. I decided to take it a step further and created its own desktop file using
[kitty](https://github.com/kovidgoyal/kitty) as the terminal to run it in. This gave me
the opportunity to have a custom icon and search name for the app. It does mean that a
different terminal needs to run outside my main one, but I end up with features like
shown below. The `.png` file was taken from the ranger GitHub README.

![gnome-search-ranger](https://github.com/user-attachments/assets/cd8a1bf5-4fc5-45de-a1d2-e3ffe5f48e7e)
