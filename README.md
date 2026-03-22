## Amazon Comp Books

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
docker compose up -d
```

### Stop Web container

```bash
docker compose down
```

## Transfer Docker Image

### extract image

```bash
docker save comp_books:latest -o comp_books.tar
tar cvf comp_books_image.tar comp_books.tar compose.yaml README.md
```

### transfer image

```bash
scp comp_books_image.tar user@server:/tmp/
```

### install image

```bash
mkdir comp_books
cd comp_books
mkdir data html

tar xf /tmp/comp_books_image.tar
docker load -i comp_books.tar
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
