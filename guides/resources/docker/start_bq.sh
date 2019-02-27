#xterm -e docker run --name bisque --rm -p 9898:8080 -v ~/bisque-docker/container-modules:/source/modules -v ~/bisque-docker/container-data:/source/data cbiucsb/bisque05:stable &

xterm -e \
docker run --name bisque --rm -p 8085:8080 \
-v $(pwd)/container-modules:/source/modules \
-v $(pwd)/container-data:/source/data \
-v $(pwd)/container-config:/source/config \
-v $(pwd)/container-backup:/source/backup \
'cbiucsb/bisque05:stable'
