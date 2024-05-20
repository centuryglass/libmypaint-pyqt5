"""
Combines various data_model/canvas modules to represent and control an edited image section.
"""
from typing import Optional
from PyQt5.QtGui import QColor, QPixmap, QImage, QTabletEvent, QMouseEvent
from PyQt5.QtCore import Qt, QPoint, QLine, QSize, QEvent, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget
from pydemo.util.fixed_aspect_graphics_view import FixedAspectGraphicsView
from pydemo.util.canvas import Canvas

class CanvasWidget(FixedAspectGraphicsView):
    """QWidget providing a mypaint drawing surface."""
    color_selected = pyqtSignal(QColor)


    def __init__(self, parent: Optional[QWidget], canvas: Canvas) -> None:
        super().__init__(parent)
        self._canvas = canvas
        self._drawing = False
        self._last_point = QPoint()
        self._line_mode=False
        self._brush_color = QColor(0, 0, 0)
        self._pen_pressure = None
        self._tablet_eraser = False
        self._image_section = None
        self._image_pixmap = None
        self.content_size = self._canvas.size()
        canvas.add_to_scene(self.scene(), 0)
        self.resizeEvent(None)


    def get_brush_color(self) -> QColor:
        """Returns the current sketch canvas brush color."""
        return self._brush_color


    def set_brush_color(self, color: QColor):
        """Sets the current sketch canvas brush color."""
        self._brush_color = color


    def clear(self) -> None:
        """Clears image content in the active canvas."""
        self._canvas.clear()
        self.update()


    def undo(self) -> None:
        """Reverses the last drawing operation done in the active canvas."""
        self._canvas.undo()
        self.update()


    def redo(self) -> None:
        """Restores the last drawing operation in the active canvas removed by undo."""
        self._canvas.redo()
        self.update()


    def fill(self) -> None:
        """Fills the active canvas."""
        self._canvas.fill(self._brush_color)
        self.update()


    def load_image(self, image : Optional[QPixmap | QImage]) -> None:
        """Loads a new image section behind the canvas."""
        self.background = image


    def get_color_at_point(self, point: QPoint) -> QColor:
        """Returns the color of the image and sketch canvas at a given point.

        If the point is outside of the widget bounds, QColor(0, 0, 0) is returned instead.
        """
        sketch_color = QColor(0, 0, 0, 0)
        image_color = QColor(0, 0, 0, 0)
        if self._canvas.has_sketch():
            sketch_color = self._canvas.get_color_at_point(point)
        image_color = self._image_section.pixelColor(point)
        def get_component(sketch_component, image_component):
            return int((sketch_component * sketch_color.alphaF()) + (image_component * image_color.alphaF()
                        * (1.0 - sketch_color.alphaF())))
        red = get_component(sketch_color.red(), image_color.red())
        green = get_component(sketch_color.green(), image_color.green())
        blue = get_component(sketch_color.blue(), image_color.blue())
        combined = QColor(red, green, blue)
        return combined


    def mousePressEvent(self, event: Optional[QMouseEvent]) -> None:
        """Start drawing, erasing, or color sampling when clicking if an image is loaded."""
        if event is None:
            return
        key_modifiers = QApplication.keyboardModifiers()
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            size_override = 1 if event.button() == Qt.RightButton else None
            if key_modifiers == Qt.ControlModifier:
                point = self._widget_to_image_coords(event.pos())
                color = self.get_color_at_point(point)
                if color is not None:
                    self.color_selected.emit(color)
            else:
                size_multiplier = self._pen_pressure if self._pen_pressure is not None else None
                if self._line_mode:
                    new_point = self.widget_to_scene_coords(event.pos()).toPoint()
                    line = QLine(self._last_point, new_point)
                    self._last_point = new_point
                    # Prevent issues with lines not drawing by setting a minimum multiplier for lineMode only:
                    if size_multiplier is not None:
                        size_multiplier = max(size_multiplier, 0.5)
                    self._canvas.draw_line(line, self._brush_color, size_multiplier, size_override)
                    canvas.end_stroke()
                else:
                    self._canvas.start_stroke()
                    self._drawing = True

                    self._last_point = self.widget_to_scene_coords(event.pos()).toPoint()
                    self._canvas.draw_point(self._last_point, self._brush_color, size_multiplier, size_override)
                self.update()


    def mouseMoveEvent(self, event: Optional[QMouseEvent]) -> None:
        """Continue any active drawing when the mouse is moved with a button held down."""
        if event is None:
            return
        if (Qt.LeftButton == event.buttons() or Qt.RightButton == event.buttons()) and self._drawing:
            size_override = 1 if Qt.RightButton == event.buttons() else None
            canvas = self._canvas
            color = QColor(self._brush_color)
            size_multiplier = self._pen_pressure if (self._pen_pressure is not None) else 1.0
            new_last_point = self.widget_to_scene_coords(event.pos()).toPoint()
            line = QLine(self._last_point, new_last_point)
            self._last_point = new_last_point
            canvas.draw_line(line, color, size_multiplier, size_override)
            self.update()


    def tabletEvent(self, tabletEvent: Optional[QTabletEvent]) -> None:
        """Update pen pressure and eraser status when a drawing tablet event is triggered."""
        if tabletEvent is None:
            return
        if tabletEvent.type() == QEvent.TabletRelease:
            self._pen_pressure = None
            self._tablet_eraser = False
        elif tabletEvent.type() == QEvent.TabletPress:
            self._tablet_eraser = tabletEvent.pointerType() == QTabletEvent.PointerType.Eraser
            self._pen_pressure = tabletEvent.pressure()
        else:
            self._pen_pressure = tabletEvent.pressure()

    def mouseReleaseEvent(self, event: Optional[QMouseEvent]) -> None:
        """Finishes any drawing operations when the mouse button is released."""
        if (event.button() == Qt.LeftButton or event.button() == Qt.RightButton) and self._drawing:
            self._drawing = False
            self._pen_pressure = None
            self._tablet_eraser = False
            self._canvas.end_stroke()
        self.update()


    def get_image_display_size(self) -> QSize:
        """Get the QSize in pixels of the area where the edited image section is drawn."""
        return QSize(self.displayed_content_size.width(), self.displayed_content_size.height())
