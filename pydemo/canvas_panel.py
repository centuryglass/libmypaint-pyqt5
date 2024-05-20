"""
Panel used to edit the selected area of the edited image.
"""
from PyQt5.QtWidgets import QWidget, QPushButton, QColorDialog, QGridLayout, QHBoxLayout, QSlider, QSpinBox, QLabel
from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QPainter, QPen, QCursor, QPixmap, QIcon, QColor

from pydemo.canvas_widget import CanvasWidget
from pydemo.util.equal_margins import get_equal_margins
from pydemo.util.contrast_color import contrast_color
from pydemo.brush_picker import BrushPicker
from pydemo.mypaint_canvas import MypaintCanvas
from pydemo.util.canvas import Canvas


class CanvasPanel(QWidget):
    """CanvasPanel is used to edit the selected area of the edited image."""

    def __init__(self, canvas: Canvas) -> None:
        """Initialize the panel with the edited image."""
        super().__init__()
        self._cursor_pixmap = QPixmap('./pydemo/resources/cursor.png')
        small_cursor_pixmap = QPixmap('./pydemo/resources/minCursor.png')
        self._small_cursor = QCursor(small_cursor_pixmap)
        eyedropper_icon = QPixmap('./pydemo/resources/eyedropper.png')
        self._eyedropper_cursor = QCursor(eyedropper_icon, hotX=0, hotY=eyedropper_icon.height())
        self._last_cursor_size = None
        self._brush_picker_button = None
        self._canvas = canvas

        self._canvas_widget = CanvasWidget(self, canvas)
        self._canvas_widget.setMinimumSize(QSize(256, 256))

        def set_brush_color(color: QColor):
            self._canvas_widget.set_brush_color(color)
            if self._color_picker_button is not None:
                icon = QPixmap(QSize(64, 64))
                icon.fill(color)
                self._color_picker_button.setIcon(QIcon(icon))
            self.update()
        self._canvas_widget.color_selected.connect(set_brush_color)

        self._color_picker_button = QPushButton()
        self._color_picker_button.setText('Color')
        self._color_picker_button.setToolTip('Select brush color')
        set_brush_color(self._canvas_widget.get_brush_color())
        self._color_picker_button.clicked.connect(lambda: set_brush_color(QColorDialog.getColor()))

        self._brush_size = canvas.brush_size()


        self._slider_widget = QWidget(self)
        self._slider_layout = QHBoxLayout(self._slider_widget)
        self._slider_label = QLabel('Brush size', self._slider_widget)
        self._slider = QSlider(Qt.Orientation.Horizontal, self._slider_widget)
        self._slider_spinbox = QSpinBox(self._slider_widget)
        self._slider.setRange(0, 300)
        self._slider_spinbox.setRange(0, 300)
        def slider_change(value):
            self._slider_spinbox.setValue(value)
            self._canvas.set_brush_size(value)
        self._slider.valueChanged.connect(slider_change)
        def spinbox_change(value):
            self._slider.setValue(value)
            self._canvas.set_brush_size(value)
        self._slider_spinbox.valueChanged.connect(spinbox_change)
        self._slider_layout.addWidget(self._slider_label, stretch = 2)
        self._slider_layout.addWidget(self._slider, stretch = 10)
        self._slider_layout.addWidget(self._slider_spinbox, stretch = 1)

        self._clear_button = QPushButton()
        self._clear_button.setText('clear')
        self._clear_button.setIcon(QIcon(QPixmap('./pydemo/resources/clear.png')))
        def clear():
            self._canvas_widget.clear()
        self._clear_button.clicked.connect(clear)

        self._fill_button = QPushButton()
        self._fill_button.setText('fill')
        self._fill_button.setIcon(QIcon(QPixmap('./pydemo/resources/fill.png')))
        def fill():
            self._canvas_widget.fill()
        self._fill_button.clicked.connect(fill)

        self._brush_picker_button = QPushButton()
        self._brush_picker = None
        self._brush_picker_button.setText('Brush')
        self._brush_picker_button.setToolTip('Select sketch brush type')
        self._brush_picker_button.setIcon(QIcon(QPixmap('./resources/brush.png')))
        def open_brush_picker():
            if self._brush_picker is None:
                self._brush_picker = BrushPicker()
            self._brush_picker.show()
            self._brush_picker.raise_()
        self.open_brush_picker = open_brush_picker
        self._brush_picker_button.clicked.connect(open_brush_picker)


        self._layout = QGridLayout(self)
        self._border_size = 2
        self._canvas_widget.setContentsMargins(get_equal_margins(0))

        # Setup layout:
        self._layout.addWidget(self._canvas_widget, 0, 0, 1, 2)
        self._layout.addWidget(self._color_picker_button, 2, 0)
        self._layout.addWidget(self._brush_picker_button, 2, 1)
        self._layout.addWidget(self._slider_widget, 3, 0, 1, 2)
        self._layout.addWidget(self._clear_button, 4, 0)
        self._layout.addWidget(self._fill_button, 4, 1)
        self._layout.setRowStretch(0, 255)
        border_size = self._slider_widget.sizeHint().height() // 3
        self._layout.setVerticalSpacing(border_size)
        self._layout.setHorizontalSpacing(border_size)
        self._layout.setContentsMargins(get_equal_margins(self._border_size))


    def paintEvent(self, event: QEvent):
        """Draws a border around the panel."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(contrast_color(self), self._border_size//2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
        if not self._color_picker_button.isHidden():
            painter.setPen(QPen(self._canvas_widget.get_brush_color(), self._border_size//2, Qt.SolidLine, Qt.RoundCap,
                        Qt.RoundJoin))
            painter.drawRect(self._color_picker_button.geometry())


    def resizeEvent(self, unused_event: QEvent):
        """Update brush cursor sizing when the widget size changes."""
        self._update_brush_cursor()


    def eventFilter(self, unused_source, event: QEvent) -> bool:
        """Draw straight lines when shift is held, use the eyedropper tool when control is held in sketch mode."""
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Control and not self._canvas_widget.get_draw_mode() == MaskCreator.DrawMode.MASK:
                self._canvas_widget.set_line_mode(False)
                self._canvas_widget.setCursor(self._eyedropper_cursor)
            elif event.key() == Qt.Key_Shift:
                self._canvas_widget.set_line_mode(True)
        elif event.type() == QEvent.KeyRelease:
            if event.key() == Qt.Key_Control:
                self._last_cursor_size = None
                self._update_brush_cursor()
            elif event.key() == Qt.Key_Shift:
                self._canvas_widget.set_line_mode(False)
        return False


    def undo(self):
        """Reverses the last drawing operation in the active canvas."""
        self._canvas_widget.undo()


    def redo(self):
        """Restores an undone drawing operation in the active canvas."""
        self._canvas_widget.redo()


    def _update_brush_cursor(self):
        """Recalculate brush cursor based on panel and brush sizes."""
        if not hasattr(self, '_mask_creator'):
            return
        brush_size = self.get_brush_size()
        scale =  max(self._canvas_widget.get_image_display_size().width(), 1) / max(self._canvas.width(), 1)
        scaled_size = max(int(brush_size * scale), 9)
        if scaled_size == self._last_cursor_size:
            return
        if scaled_size <= 10:
            self._canvas_widget.setCursor(self._small_cursor)
        else:
            new_cursor = QCursor(self._cursor_pixmap.scaled(QSize(scaled_size, scaled_size)))
            self._canvas_widget.setCursor(new_cursor)
        self._last_cursor_size = scaled_size
