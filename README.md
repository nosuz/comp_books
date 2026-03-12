## Amazon scraper

## Required folders

- data
- html

```bash
mkdir data html
```

## Build Container

```bash
docker compose build
# build and run in background
# docker compose up -d --build
```

## Start Web container

```bash
docker compose up -d web
```

## Stop Web container

```bash
docker compose down web
```

## Start batch job

```bash
docker compose run --rm batch
```

## Transfer Docker Image

### extract image

```bash
docker save pskreporter-app:latest -o app.tar
tar zcvf ~/pskreporter_image.tgz app.tar Dockerfile compose.yaml README.md
```

### transfer image

```bash
scp pskreporter.tar user@server:/tmp/
```

### install image

```bash
docker load -i pskreporter.tar
```

## start image

```bash
docker compose up -d
```

`-d`が無いとフォアグラウンドで実行される。

## stop image

```bash
docker compose down
```
