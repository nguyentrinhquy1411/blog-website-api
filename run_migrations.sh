#!/bin/bash

# Đợi PostgreSQL khởi động
echo "Waiting for PostgreSQL to start..."
sleep 5

# Chạy migrations
echo "Running migrations..."
alembic upgrade head

echo "Migrations completed." 