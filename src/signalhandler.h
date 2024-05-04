#ifndef SIGNALHANDLER_H
#define SIGNALHANDLER_H

#include <QObject>
#include <QGraphicsScene>
#include "mpsurface.h"
#include "mptile.h"

class SignalHandler : public QObject {
    Q_OBJECT
public:
    SignalHandler(QGraphicsScene* scene, int z_value=-1);
    ~SignalHandler();

public slots:
    void onNewTile(MPSurface *surface, MPTile *tile);
    void onUpdateTile(MPSurface *surface, MPTile *tile);

private:
    int z_value;
    QGraphicsScene* scene;

};

#endif //SIGNALHANDLER_H
