#include <QGraphicsItem>
#include "signalhandler.h"
#include "mphandler.h"
#include "mpsurface.h"
#include "mptile.h"

SignalHandler::SignalHandler(QGraphicsScene* scene, int z_value) {
    this->scene = scene;
    this->z_value = z_value;
    if (z_value < 0) {
        this->z_value = 0;
        for (const QGraphicsItem* item : scene->items()) {
            int itemZ = item->zValue();
            if ((itemZ + 1) > this->z_value) {
                this->z_value = (itemZ + 1);
            }
        }
    }

    MPHandler* mypaint = MPHandler::handler();
    connect(mypaint, SIGNAL(newTile(MPSurface*, MPTile*)), this, SLOT(onNewTile(MPSurface*, MPTile*)));
    connect(mypaint, SIGNAL(updateTile(MPSurface*, MPTile*)), this, SLOT(onUpdateTile(MPSurface*, MPTile*)));
    connect(mypaint, SIGNAL(clearedSurface(MPSurface*)), this, SLOT(onClearedSurface(MPSurface*)));
}

SignalHandler::~SignalHandler() {
}

void SignalHandler::onNewTile(MPSurface *surface, MPTile *tile)
{
    Q_UNUSED(surface);
    tile->setZValue(z_value);
    scene->addItem(tile);
}

void SignalHandler::onUpdateTile(MPSurface *surface, MPTile *tile)
{
    Q_UNUSED(surface);
    tile->update();
}
