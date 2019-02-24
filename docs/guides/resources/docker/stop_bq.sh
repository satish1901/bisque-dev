docker stop $(docker ps -a -q --filter ancestor=cbiucsb/bisque05:stable --format="{{.ID}}")
