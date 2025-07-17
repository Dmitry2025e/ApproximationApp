
from approximator.data_models.segment import Segment
from approximator.data_models.channel_state import ChannelState
from approximator.utils.log import debug


class SegmentEditor:
    """Инкапсулирует операции редактирования сегментов канала."""

    def __init__(self, channel: ChannelState):
        self.channel = channel

    def split_segment_at(self, x: float) -> bool:
        """Делит сегмент, содержащий x, на два новых."""

        debug(f"[SegmentEditor] split_segment_at({x:.3f})")
        if not self.channel or not self.channel.segments:
            debug("[SegmentEditor] channel is None or has no segments")
            return False


        for i, seg in enumerate(self.channel.segments):
            debug(f"  → Segment {i}: {seg.x_start:.3f} → {seg.x_end:.3f}")

            if seg.x_start < x < seg.x_end:
                if abs(x - seg.x_start) < 1e-6 or abs(x - seg.x_end) < 1e-6:
                    return False
                left = Segment(x_start=seg.x_start, x_end=x, label=seg.label, color=seg.color)
                right = Segment(x_start=x, x_end=seg.x_end, label="", color=seg.color)
                self.channel.segments[i] = left
                self.channel.segments.insert(i + 1, right)
                self.channel.selected_segment_index = i + 1

                debug(f"[SegmentEditor] Split success → "
                      f"{left.x_start:.3f}–{left.x_end:.3f}, "
                      f"{right.x_start:.3f}–{right.x_end:.3f}")
                return True

        debug("[SegmentEditor] No segment found to split at given x")
        return False


    def merge_segments(self, index_a: int, index_b: int) -> bool:
        """Объединяет два соседних сегмента, если они смежные."""
        if index_a < 0 or index_b < 0:
            return False
        if index_a >= len(self.channel.segments) or index_b >= len(self.channel.segments):
            return False
        if abs(self.channel.segments[index_a].x_end - self.channel.segments[index_b].x_start) > 1e-6:
            return False  # не смежные

        seg_a = self.channel.segments[index_a]
        seg_b = self.channel.segments[index_b]
        new_seg = Segment(
            x_start=seg_a.x_start,
            x_end=seg_b.x_end,
            label=seg_a.label or seg_b.label,
            color=seg_a.color
        )
        self.channel.segments[index_a] = new_seg
        del self.channel.segments[index_b]
        self.channel.selected_segment_index = index_a
        return True

    def move_boundary(self, index: int, side: str, new_x: float) -> bool:
        """Перемещает границу сегмента ('start' или 'end') на new_x."""
        if index < 0 or index >= len(self.channel.segments):
            return False
        seg = self.channel.segments[index]
        if side == 'start':
            if new_x >= seg.x_end:
                return False
            seg.x_start = new_x
        elif side == 'end':
            if new_x <= seg.x_start:
                return False
            seg.x_end = new_x
        else:
            return False
        return True

    def delete_segment(self, index: int) -> bool:
        """Удаляет сегмент по индексу."""
        if index < 0 or index >= len(self.channel.segments):
            return False
        del self.channel.segments[index]
        self.channel.selected_segment_index = -1
        return True

    def recolor_segment(self, index: int, new_color: str) -> bool:
        """Изменяет цвет сегмента."""
        if index < 0 or index >= len(self.channel.segments):
            return False
        self.channel.segments[index].color = new_color
        return True

    def relabel_segment(self, index: int, new_label: str) -> bool:
        """Присваивает сегменту метку."""
        if index < 0 or index >= len(self.channel.segments):
            return False
        self.channel.segments[index].label = new_label
        return True

    def insert_segment(self, x_start: float, x_end: float, label: str = "", color: str = "#8888ff") -> bool:
        """Добавляет новый сегмент."""
        if x_start >= x_end:
            return False
        new_seg = Segment(x_start=x_start, x_end=x_end, label=label, color=color)
        self.channel.segments.append(new_seg)
        self.channel.selected_segment_index = len(self.channel.segments) - 1
        return True

    def lock_segment(self, index: int) -> bool:
        """Блокирует сегмент от редактирования (если поле lock доступно)."""
        if index < 0 or index >= len(self.channel.segments):
            return False
        setattr(self.channel.segments[index], "locked", True)
        return True

    def unlock_segment(self, index: int) -> bool:
        """Разблокирует сегмент."""
        if index < 0 or index >= len(self.channel.segments):
            return False
        setattr(self.channel.segments[index], "locked", False)
        return True