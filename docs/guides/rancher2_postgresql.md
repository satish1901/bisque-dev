## Setup Postgresql for Bisque Database Persistence
- Idea is, to not use the default Sqlite DB in a cluster environment
- The data directory is still being used for images/cache etc, and mounted as NFS across this cluster
- Reference: https://severalnines.com/blog/using-kubernetes-deploy-postgresql

#### Create a Volume: pgdev-vol
- Path on the host node: /opt/bisque/pg
![Persistent Storage postgres volume](img/bqranch/rancher_volume_pg.png?raw=true)

#### Setup a Postgresql 10 database 

- Image: postgres:10.4
- Environment:
```
    POSTGRES_DB=postgres
    POSTGRES_PASSWORD=postgres
    POSTGRES_USER=postgres
```
- Ports: 5432/TCP -> ClusterIP -> Same as container port
- Volume: Mount pgdev-vol created above to mount point "/var/lib/postgresql/data"


> Here is the complete Postgres workload configuration screen shot for reference

![Workload postgres](img/bqranch/workload_postgres.png?raw=true)

> Make sure to claim this volume in the Postgres workload deploy configuration

![Workload postgres volume](img/bqranch/workload_postgres_volume.png?raw=true)


##### Test database using the nodes IP

- Test using psql, depending on what IP the postgres server is available at

```
psql -h 10.42.0.15 -U postgres --password -p 5432 postgres
psql -h postgres.prod -U postgres --password -p 5432 postgres
```

- Create database for a particular instance

```
CREATE DATABASE connoisseur;
GRANT ALL PRIVILEGES ON DATABASE "connoisseur" to postgres;
```