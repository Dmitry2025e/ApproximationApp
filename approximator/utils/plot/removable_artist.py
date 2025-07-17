from approximator.utils.log import debug


class RemovableArtist:
    def __init__(self, artist, ax):
        self.artist = artist
        self.ax = ax

    def remove(self):
        try:
            if hasattr(self.ax, "lines") and self.artist in self.ax.lines:
                self.ax.lines.remove(self.artist)
            elif hasattr(self.artist, "set_visible"):
                self.artist.set_visible(False)
            else:
                debug(f"[RemovableArtist] ⚠ Элемент не поддаётся удалению: {type(self.artist)}")


        except Exception as e:
            debug(f"[RemovableArtist] ⚠ Ошибка удаления: {e}")