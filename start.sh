#!/bin/bash

set -e

NETWORK_NAME="hang-network"

REDIS_CONTAINER="hang-redis-local"
REDIS_IMAGE="hang-redis-image"

DB_CONTAINER="hang-db-local"
DB_IMAGE="hang-db-image"

APP_SCALE=${1:-1}

echo "Scaling api to: $APP_SCALE"

echo "Checking docker network..."

if ! docker network inspect $NETWORK_NAME >/dev/null 2>&1; then
  echo "Creating docker network..."
  docker network create $NETWORK_NAME
fi

echo "Checking Redis container..."

if [ "$(docker ps -q -f name=$REDIS_CONTAINER)" ]; then
  echo "Redis already running."
else
  if [ "$(docker ps -aq -f name=$REDIS_CONTAINER)" ]; then
    echo "Starting existing Redis container..."
    docker start $REDIS_CONTAINER
  else
    if ! docker image inspect $REDIS_IMAGE >/dev/null 2>&1; then
      echo "Redis image missing. Building..."
      docker build -f infra/Dockerfile.redis -t $REDIS_IMAGE infra
    fi

    echo "Creating Redis container..."
    docker run -d --name $REDIS_CONTAINER --network $NETWORK_NAME -p 6379 $REDIS_IMAGE
  fi
fi

echo "Checking Postgres container..."

if [ "$(docker ps -q -f name=$DB_CONTAINER)" ]; then
  echo "Postgres already running."
else
  if [ "$(docker ps -aq -f name=$DB_CONTAINER)" ]; then
    echo "Starting existing Postgres container..."
    docker start $DB_CONTAINER
  else
    if ! docker image inspect $DB_IMAGE >/dev/null 2>&1; then
      echo "DB image missing. Building..."
      docker build -f infra/Dockerfile.db -t $DB_IMAGE infra
    fi

    echo "Creating Postgres container..."
    docker run -d --name $DB_CONTAINER --env-file infra/.db_env --network $NETWORK_NAME -p 5432 $DB_IMAGE
    # -v hang_postgres_data:/var/lib/postgresql/data to keep db vol on kill
  fi
fi

echo "Starting app stack..."

docker compose up --build -d --scale api=$APP_SCALE

echo "Done."