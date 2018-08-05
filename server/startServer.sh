#!/bin/sh

cat /home/administrator/workspace/minecraft_server/server/startServer.sh | at now + 5 minutes

cd /home/administrator/workspace/minecraft_server/server

export MC_SVR_SHOULD_RUN=1

/usr/bin/python /home/administrator/workspace/minecraft_server/server/serverRoutine.py >> debug_log.txt
