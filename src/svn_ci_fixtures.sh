#!/bin/sh

FIXTURE="fixtures/initial_data.json"
APPS="akademic auth"

python manage.py dumpdata $APPS --indent 2 > $FIXTURE

echo -n "Buscando cambios en $FILE (salida por stdout)..."
svn diff $FIXTURE
echo "Done."

MENSAJE="Nuevas fixtures recogidas en `hostname` el dia `date -R`"
echo -n "Subiendo cambios: '$MENSAJE' (salida por stdout)..."
svn ci $FIXTURE -m "$MENSAJE" 
echo "Done."
