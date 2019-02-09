Reference: https://severalnines.com/blog/using-kubernetes-deploy-postgresql

#### Create a Volume: pgdev-vol
- Path on the host node: /tmp/postgres

#### Setup a Postgresql 10 database 

Image: postgres:10.4
Environment
```
    POSTGRES_DB=postgres
    POSTGRES_PASSWORD=postgres
    POSTGRES_USER=postgres
```

Spec for a Rancher 2 workload
```
spec:
  containers:
  - env:
    - name: POSTGRES_DB
      value: postgres
    - name: POSTGRES_PASSWORD
      value: postgres
    - name: POSTGRES_USER
      value: postgres
    image: postgres:10.4
    imagePullPolicy: Always
    name: postgres
    ports:
    - containerPort: 5432
      hostPort: 5432
      name: 5432tcp54320
      protocol: TCP
    resources: {}
    volumeMounts:
    - mountPath: /var/lib/postgresql/data
      name: pgdev-vol
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-7hhqq
      readOnly: true
  dnsPolicy: ClusterFirst
  nodeName: loup
  volumes:
  - name: pgdev-vol
    persistentVolumeClaim:
      claimName: pgdev-vol
  - name: default-token-7hhqq
    secret:
      defaultMode: 420
      secretName: default-token-7hhqq
```

##### Test database using the nodes IP
```
psql -h 10.42.0.15 -U postgres --password -p 5432 postgres
psql -h loup.ece.ucsb.edu -U postgres --password -p 5432 postgres
```