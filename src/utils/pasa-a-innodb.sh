#!/bin/sh

USER=dbusername
DB=dbpassword
PASSWD=ex3Quiegin
BACKUPFILE=/root/backups/backup_$(date +%Y%m%d_%H%M%S)_$DB.sql

mysqldump --defaults-file=/etc/mysql/debian.cnf \
  --complete-insert --skip-add-drop-table \
  --no-create-info --ignore-table=$DB.auth_permission \
  --ignore-table=$DB.django_admin_log \
  --ignore-table=$DB.django_content_type \
  --ignore-table=$DB.django_session \
  --ignore-table=$DB.django_site $DB > $BACKUPFILE

python manage.py reset_db --noinput

rm -f addressbook/fixtures/initial_data.json
rm -f fixtures/initial_data.json
python manage.py syncdb --noinput

mysql --verbose --user=$USER \
        --password=$PASSWD $DB < $BACKUPFILE > /dev/null

