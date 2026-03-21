## Amazon scraper

## Required folders

- data
- html

```bash
mkdir data html
```

## Container

### Build Container

```bash
docker compose build
# build and run in background
# docker compose up -d --build
```

### Start Web container

```bash
docker compose up -d web
```

### Stop Web container

```bash
docker compose down web
```

### Start scraping

```bash
docker compose run --rm update
```

## Transfer Docker Image

### extract image

```bash
docker save amazon_scrape:latest -o amazon_scrape.tar
tar cvf amazon_scrape_image.tar amazon_scrape.tar compose.yaml README.md
```

### transfer image

```bash
scp amazon_scrape_image.tar user@server:/tmp/
```

### install image

```bash
mkdir amazon_scrape
cd amazon_scrape
mkdir data html

tar xf /tmp/amazon_scrape_image.tar
docker load -i amazon_scrape.tar
```

## start image

```bash
docker compose up -d web
```

`-d`が無いとフォアグラウンドで実行される。

## stop image

```bash
docker compose down
```
