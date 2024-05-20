"""
Selects between the default mypaint brushes found in resources/brushes. This widget can only be used if a compatible
brushlib/libmypaint QT library is available, currently only true for x86_64 Linux.
"""
from typing import Optional, Any
import os
import re
from PyQt5.QtWidgets import QWidget, QTabWidget, QGridLayout, QScrollArea, QSizePolicy, QMenu
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPaintEvent, QMouseEvent, QResizeEvent
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QEvent, pyqtSignal
from pydemo.util.get_scaled_placement import get_scaled_placement
from libmypaint_pyqt5 import MPBrushLib as brushlib

class BrushPicker(QTabWidget):
    """BrushPicker elects between the default mypaint brushes found in resources/brushes."""

    BRUSH_DIR = './demo/brushes'
    BRUSH_CONF_FILE = 'brushes.conf'
    BRUSH_ORDER_FILE = 'order.conf'
    BRUSH_EXTENSION = '.myb'
    BRUSH_ICON_EXTENSION = '_prev.png'

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Loads brushes and optionally adds the widget to a parent.

        Parameters
        ----------
        parent : QWidget, optional
            Optional parent widget.
        """
        super().__init__(parent)
        self._groups: list[str] = []
        self._group_orders: dict[str, list[str]] = {}
        self._layouts: dict[str, QGridLayout] = {}
        self._pages: dict[str, QWidget]  = {}
        self._read_order_file(os.path.join(BrushPicker.BRUSH_DIR, BrushPicker.BRUSH_CONF_FILE))
        # scan for added groups:
        for group in os.listdir(BrushPicker.BRUSH_DIR):
            group_dir = os.path.join(BrushPicker.BRUSH_DIR, group)
            if group in self._group_orders or not os.path.isdir(group_dir):
                continue
            if self._read_order_file(os.path.join(group_dir, BrushPicker.BRUSH_ORDER_FILE)):
                continue
            # No order.conf: just read in file order
            self._groups.append(group)
            self._group_orders[group] = []
            for file in os.listdir(group_dir):
                if not file.endswith(BrushPicker.BRUSH_EXTENSION):
                    continue
                brush_name = file[:-4]
                self._group_orders[group].append(brush_name)
        for group in self._groups:
            group_dir = os.path.join(BrushPicker.BRUSH_DIR, group)
            if not os.path.isdir(group_dir):
                continue
            self._create_tab(group)
            group_layout = self._layouts[group]
            for x, y, brush in _GridIter(self._group_orders[group]):
                brush_path = os.path.join(group_dir, brush + BrushPicker.BRUSH_EXTENSION)
                image_path = os.path.join(group_dir, brush + BrushPicker.BRUSH_ICON_EXTENSION)
                brush_icon = _IconButton(image_path, brush_path)
                group_layout.addWidget(brush_icon, y, x)


    def _create_tab(self, tab_name: str, index: Optional[int] = None) -> None:
        """Adds a new brush category tab."""
        if tab_name in self._layouts:
            return
        tab = QScrollArea(self)
        tab.setWidgetResizable(True)
        content = QWidget(tab)
        tab.setWidget(content)
        layout = QGridLayout()
        content.setLayout(layout)
        self._pages[tab_name] = content
        self._layouts[tab_name] = layout
        if index is None:
            self.addTab(tab, tab_name)
        else:
            self.insertTab(index, tab, tab_name)


    def _read_order_file(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = [ln.strip() for ln in file.readlines()]
        for line in lines:
            group_match = re.search(r'^Group: ([^#]+)', line)
            if group_match:
                group = group_match.group(1)
                self._groups.append(group)
                self._group_orders[group] = []
                continue
            if '/' not in line:
                continue
            group, brush = line.split('/')
            if group not in self._group_orders:
                self._groups.append(group)
                self._group_orders[group] = []
            self._group_orders[group].append(brush)
        return True


class _IconButton(QWidget):
    """Button widget used to select a single brush."""

    def __init__(self, imagepath: str, brushpath: str) -> None:
        """Initialize using paths to the brush file and icon."""
        super().__init__()
        self._brushname = os.path.basename(brushpath)[:-4]
        self._brushpath = brushpath
        self._imagepath = imagepath
        self._image_rect: Optional[QRect] = None
        self._image = QPixmap(imagepath)
        inverted = QImage(imagepath)
        inverted.invertPixels(QImage.InvertRgba)
        self._image_inverted = QPixmap.fromImage(inverted)
        size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        size_policy.setWidthForHeight(True)
        self.setSizePolicy(size_policy)
        self.resizeEvent(None)

    def saved_name(self) -> str:
        """Returns the name used to save this brush to favorites."""
        group_name = os.path.basename(os.path.dirname(self._brushpath))
        return f'{group_name}/{self._brushname}'

    def copy(self, favorite: bool = False) -> QWidget:
        """Creates a new IconButton with the same brush file and icon."""
        return _IconButton(self._imagepath, self._brushpath)

    def sizeHint(self) -> QSize:
        """Set ideal size based on the brush icon size."""
        return self._image.size()

    def is_selected(self) -> bool:
        """Checks whether this brush is the selected brush."""
        active_brush = brushlib.get_active_brush()
        return active_brush is not None and active_brush == self._brushpath

    def resizeEvent(self, unused_event: Optional[QResizeEvent]) -> None:
        """Recalculates icon bounds when the widget size changes."""
        self._image_rect = get_scaled_placement(QRect(0, 0, self.width(), self.height()), self._image.size())

    def paintEvent(self, unused_event: Optional[QPaintEvent]) -> None:
        """Paints the icon image in the widget bounds, preserving aspect ratio."""
        if self._image_rect is None:
            return
        painter = QPainter(self)
        painter.fillRect(self._image_rect, Qt.GlobalColor.red)
        if self.is_selected():
            painter.drawPixmap(self._image_rect, self._image_inverted)
        else:
            painter.drawPixmap(self._image_rect, self._image)

    def mousePressEvent(self, event: Optional[QMouseEvent]) -> None:
        """Load the associated brush when left-clicked."""
        if event is not None and event.button() == Qt.MouseButton.LeftButton and not self.is_selected() \
                and self._image_rect is not None and self._image_rect.contains(event.pos()):
            brushlib.load_brush(self._brushpath)
            parent = self.parent()
            if isinstance(parent, QWidget):
                parent.update()

class _GridIter():
    """Iterates through brush grid positions and list items."""
    WIDTH = 5

    def __init__(self, item_list: list[Any], i: int = 0):
        """Sets the iterated list and initial list index."""
        self._list = item_list
        self._i = i
        self._x = 0
        self._y = 0

    def __iter__(self):
        self._x = self._i % _GridIter.WIDTH
        self._y = self._i // _GridIter.WIDTH
        return self

    def __next__(self) -> tuple[int, int, Any]:
        """returns the next column, row, list item."""
        x = self._x
        y = self._y
        i = x + y * _GridIter.WIDTH
        if i >= len(self._list):
            raise StopIteration
        self._x += 1
        if self._x >= _GridIter.WIDTH:
            self._y += 1
            self._x = 0
        return x, y, self._list[i]
