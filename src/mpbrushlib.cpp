#include <QFile>
#include "mpbrushlib.h"
#include "mphandler.h"
#include "signalhandler.h"

SignalHandler* MPBrushLib::signalHandler = nullptr;
QString MPBrushLib::brushpath("");

void MPBrushLib::add_to_scene(QGraphicsScene* scene, int z_value) {
    if (MPBrushLib::signalHandler == nullptr) {
        MPBrushLib::signalHandler = new SignalHandler(scene, z_value);
    }
}

void MPBrushLib::set_surface_size(QSize size) {
    MPHandler::handler()->setSurfaceSize(size);
}

QSize MPBrushLib::surface_size() {
    return MPHandler::handler()->surfaceSize();
}

void MPBrushLib::clear_surface() {
    MPHandler::handler()->clearSurface();
}

void MPBrushLib::load_brush(QString brush_path, bool preserveSize) {
    QFile file(brush_path);
    float brushSize = 0;
    if (preserveSize) {
        brushSize = MPHandler::handler()->getBrushValue((MyPaintBrushSetting) MYPAINT_BRUSH_SETTING_RADIUS_LOGARITHMIC);
    }
    if (file.open( QIODevice::ReadOnly ))
    {
        QByteArray content = file.readAll();
        content.append( (char)0 );
        MPBrushLib::brushpath = brush_path;
        MPHandler::handler()->loadBrush(content);
        if (preserveSize) {
            MPHandler::handler()->setBrushValue((MyPaintBrushSetting) MYPAINT_BRUSH_SETTING_RADIUS_LOGARITHMIC, brushSize);
        }
    }
}

QString MPBrushLib::get_active_brush() {
    return MPBrushLib::brushpath;
}

void MPBrushLib::set_brush_color(QColor color) {
    MPHandler::handler()->setBrushColor(color);
}

void MPBrushLib::load_image(const QImage& image) {
    MPHandler::handler()->loadImage(image);
}

QImage MPBrushLib::render_image() {
    return MPHandler::handler()->renderImage();
}

void MPBrushLib::start_stroke() {
    MPHandler::handler()->startStroke();
}

void MPBrushLib::end_stroke() {
    MPHandler::handler()->endStroke();
}

void MPBrushLib::basic_stroke_to(float x, float y) {
    MPHandler::handler()->strokeTo(x, y);
}

void MPBrushLib::stroke_to(float x, float y, float pressure, float xtilt, float ytilt) {
    MPHandler::handler()->strokeTo(x, y, pressure, xtilt, ytilt);
}

float MPBrushLib::get_brush_value(MPBrushLib::BrushSetting valueType) {
    return MPHandler::handler()->getBrushValue((MyPaintBrushSetting) valueType);
}

void MPBrushLib::set_brush_value(MPBrushLib::BrushSetting valueType, float value) {
    MPHandler::handler()->setBrushValue((MyPaintBrushSetting) valueType, value);
}
