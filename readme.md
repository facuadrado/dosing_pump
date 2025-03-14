# fastapi-doser

Automatic doser for reef tank.

## Getting Started

These instructions will cover usage information and for the docker container 

### Prerequisities


In order to run this container you'll need docker installed.


### Usage
#### Container Parame

Build the docker image

```shell
docker build -t fastapi-doser .
```

Run the Docker Container

```shell
docker run --privileged --mount type=volume,src=doser-mnt,dst=/mnt -p 8000:8000 fastapi-doser
```
Persistent 24/7 run

```shell
docker run --privileged -d --restart unless-stopped --mount type=volume,src=doser-mnt,dst=/mnt -p 8000:8000 fastapi-doser
```

Bash into container
```shell
docker exec -it <container-id> /bin/Bash
```

Alternatively run container using docker compose
```shell
docker compose up -d
```

to force a build run
```shell
docker compose up --build -d
```


Access API at:
* `http://<raspberry-pi-ip>:8000/docs`
