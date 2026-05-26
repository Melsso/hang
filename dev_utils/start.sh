#!/bin/bash

set -e

NETWORK_NAME="hang_network"

REDIS_CONTAINER="local_redis"
REDIS_IMAGE="local_redis_image"

DB_CONTAINER="local_db"
DB_IMAGE="local_db_image"

APP_SCALE=${1:-1}

echo "Scaling hang_app to: $APP_SCALE"

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
      docker build -f ../Dockerfile.redis -t $REDIS_IMAGE ..
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
      docker build -f ../Dockerfile.db -t $DB_IMAGE .. 
    fi

    echo "Creating Postgres container..."
    docker run -d --name $DB_CONTAINER --env-file .db_env --network $NETWORK_NAME -p 5432 $DB_IMAGE
  fi
fi

echo "Starting app stack..."

docker compose up --build -d --scale hang_app=$APP_SCALE

echo "Done."