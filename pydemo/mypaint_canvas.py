"""
Provides a Canvas implementation using the libmypaint/brushlib library, used for directly drawing within edited image
sections. Allows painting in full color with drawing tablet support, using .myb brush files.
"""
from typing import Optional
import atexit
import math
from PyQt5.QtGui import QPainter, QImage, QPixmap, QColor
from PyQt5.QtCore import Qt, QLine, QSize, QPoint, QRect
from PyQt5.QtWidgets import QGraphicsScene
from PIL import Image
from pydemo.util.canvas import Canvas
from pydemo.util.image_utils import pil_image_to_qimage
from libmypaint_pyqt5 import MPBrushLib as brushlib


class MypaintCanvas(Canvas):
    """MypaintCanvas provides an image editing layer that uses the MyPaint brush engine."""

    RADIUS_LOG = brushlib.BrushSetting.MYPAINT_BRUSH_SETTING_RADIUS_LOGARITHMIC

    def __init__(self, size: QSize) -> None:
        """Initialize with config values and optional arbitrary initial image data.

        Parameters
        ----------
        config: data_model.Config
            Used for setting initial size if no initial image data is provided.
        image: QImage or PIL Image or QPixmap or QSize or str, optional
        """
        super().__init__(size)
        self._visible = True
        self._size = size
        brushlib.set_surface_size(size)
        self._drawing = False
        self._scene: Optional[QGraphicsScene] = None
        self._scale = 1.0
        self._has_sketch = False
        self._saved_brush_size: Optional[int] = None
        self._saved_image: Optional[QImage] = None
        self.set_image(size)
        #atexit.register(lambda: self.clear())


    def has_sketch(self) -> bool:
        """Returns whether the canvas contains non-empty image data."""
        return self._has_sketch


    def set_brush(self, brush_path: str) -> None:
        """Loads a MyPaint brush file.

        Parameters
        ----------
        brush_path : str
            Path to a valid MyPaint brush file. These files contain JSON data in the format specified by MyPaint and
            usually have the .myb extension.
        """
        brushlib.load_brush(brush_path, True)
        self.set_brush_size(self.brush_size())


    def set_brush_size(self, size: int) -> None:
        """Sets the base brush size.

        Parameters
        ----------
        size : int
            Base brush blot diameter in pixels.
        """
        super().set_brush_size(size)
        size_log_radius = math.log(size / 2)
        brushlib.set_brush_value(MypaintCanvas.RADIUS_LOG, size_log_radius)


    def add_to_scene(self, scene: QGraphicsScene, z_value: Optional[int] = None):
        """Adds the canvas to a QGraphicsScene. This must only ever be called once.

        Parameters
        ----------
        scene : QGraphicsScene
            Scene that will display the canvas content.
        z_value : int
            Level within the scene where canvas content is drawn, higher levels appear above lower ones.
        """
        self._scene = scene
        brushlib.add_to_scene(scene, z_value)


    def set_image(self, image_data: QImage | QSize | Image.Image | str) -> None:
        """Loads an image into the canvas, overwriting existing canvas content.

        Parameters
        ----------
        image_data : QImage or QSize or PIL Image or str
            An image, image size, or image path. If necessary, the canvas will be resized to match the image size.
            If image_data is a QSize, the canvas will be cleared.
        """
        brushlib.clear_surface()
        image = None
        if isinstance(image_data, QSize):
            if self.size() != image_data:
                brushlib.set_surface_size(image_data)
        elif isinstance(image_data, str):
            image = QImage(image_data)
        elif isinstance(image_data, Image.Image):
            image = pil_image_to_qimage(image_data)
        elif isinstance(image_data, QImage):
            image = image_data
        else:
            raise TypeError(f'Invalid image param {image_data}')
        if image is not None:
            if self.size() != image_data.size():
                brushlib.set_surface_size(image_data.size())
            if image.format() != QImage.Format_ARGB32:
                image.convertTo(QImage.Format_ARGB32)
            brushlib.load_image(image)


    def size(self) -> QSize:
        """Returns the canvas size in pixels as a QSize."""
        return brushlib.surface_size()


    def width(self) -> int:
        """Returns the canvas width in pixels as an int."""
        return self._size.width()


    def height(self) -> int:
        """Returns the canvas height in pixels as an int."""
        return self._size.height()


    def get_qimage(self) -> QImage:
        """Returns all canvas image content as a QImage."""
        image = brushlib.render_image()
        if image.size() != self.size():
            image = image.scaled(self.size())
        return image


    def resize(self, size: QSize) -> None:
        """Updates the canvas size, scaling any image content to match.

        Parameters
        ----------
        size : QSize
            New canvas size in pixels.
        """
        self._size = size
        size = QSize(int(size.width() * self._scale), int(size.height() * self._scale))
        if size != brushlib.surface_size():
            image = self.get_qimage().scaled(size)
            self.set_image(image)


    def start_stroke(self) -> None:
        """Signals the start of a brush stroke, to be called once whenever user input starts or resumes."""
        if not self._visible:
            return
        super().start_stroke()
        brushlib.start_stroke()
        self._drawing = True


    def end_stroke(self) -> None:
        """Signals the end of a brush stroke, to be called once whenever user input stops or pauses."""
        if not self._visible:
            return
        brushlib.end_stroke()
        self._drawing = False
        if self._saved_brush_size is not None:
            self.set_brush_size(self._saved_brush_size)
            self._saved_brush_size = None


    def draw_point(self,
            point: QPoint,
            color: QColor,
            size_multiplier: Optional[float],
            size_override: Optional[int] = None) -> None:
        """Draws a single point on the canvas.

        Parameters
        ----------
        point : QPoint
            Position where the point should be drawn.
        color : QColor
            Current color selected for drawing.
        size_multiplier : float, optional
            Tablet pen pressure value. This may or may not actually affect size, it depends on the brush.
        size_override : int, optional
            Optional value that should override brush_size for this operation only.
        """
        if not self._visible:
            return
        self._draw(point, color, size_multiplier, size_override)


    def draw_line(self,
            line: QLine,
            color: QColor,
            size_multiplier: Optional[float],
            size_override: Optional[int] = None) -> None:
        """Draws a line on the canvas.

        Parameters
        ----------
        line : QLine
            Position where the line should be drawn.
        color : QColor
            Current color selected for drawing.
        size_multiplier : float, optional
            Tablet pen pressure value. This may or may not actually affect size, it depends on the brush.
        size_override : int, optional
            Optional value that should override brush_size for this operation only.
        """
        if not self._visible:
            return
        self._draw(line, color, size_multiplier, size_override)


    def fill(self, color: QColor) -> None:
        """Fills the canvas with a single QColor."""
        if not self._visible:
            return
        super().fill(color)
        self._has_sketch = True
        size = self.size()
        image = QImage(size, QImage.Format_ARGB32)
        painter = QPainter(image)
        painter.fillRect(0, 0, size.width(), size.height(), color)
        painter.end()
        self.set_image(image)


    def clear(self) -> None:
        """Replaces all canvas image contents with transparency.  Does nothing if connected to an image layer."""
        super().clear()
        self._has_sketch = False
        brushlib.clear_surface()


    def setVisible(self, visible: bool) -> None:
        """Shows or hides the canvas."""
        if visible == self._visible:
            return
        self._visible = visible
        if self._visible:
            if self._saved_image is not None:
                self.set_image(self._saved_image)
                self._saved_image = None
        else:
            self._saved_image = self.get_qimage()
            self.clear()


    def _draw(self,
            pos: QPoint | QLine,
            color: QColor,
            size_multiplier: Optional[float],
            size_override: Optional[int] = None) -> None:
        if not self._visible:
            return
        if size_override is not None:
            if self._saved_brush_size is None:
                self._saved_brush_size = self.brush_size()
            self.set_brush_size(size_override)
        self._has_sketch = True
        brushlib.set_brush_color(color)
        if not self._drawing:
            self.start_stroke()
            if isinstance(pos, QLine):
                if size_multiplier is None:
                    brushlib.basic_stroke_to(float(pos.x1()), float(pos.y1()))
                else:
                    brushlib.stroke_to(float(pos.x1()), float(pos.y1()), size_multiplier, 0.0, 0.0)
        if isinstance(pos, QLine):
            if size_multiplier is None:
                brushlib.basic_stroke_to(float(pos.x2()), float(pos.y2()))
            else:
                brushlib.stroke_to(float(pos.x2()), float(pos.y2()), size_multiplier, 0.0, 0.0)
        else: #QPoint
            if size_multiplier is None:
                brushlib.basic_stroke_to(float(pos.x()), float(pos.y()))
            else:
                brushlib.stroke_to(float(pos.x()), float(pos.y()), size_multiplier, 0.0, 0.0)
