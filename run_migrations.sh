#!/bin/bash

# Notify about the database connection
echo "Connecting to Railway PostgreSQL database..."

# Run migrations
echo "Running migrations..."
alembic upgrade head

echo "Migrations completed."