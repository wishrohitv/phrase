# Database Migrations Setup

This guide will help you set up database migrations using Alembic.

## Prerequisites

Make sure you have Python and pip installed on your system.

## Installation

Install the required packages:

```bash
# For PostgreSQL
pip install psycopg2-binary # For psycopg2
pip install psycopg[binary] # For psycopg3

# For MySQL
pip install pymysql
# or
pip install mysqlclient

# For SQLite (included with Python, no additional driver needed)
# No installation required

# Choose the appropriate driver based on your database system
pip install alembic
```

## Initialize Alembic

If this is your first time setting up migrations, initialize Alembic in your project:

```bash
alembic init alembic
```

This will create an `alembic` directory with configuration files and a `versions` folder for your migrations.

## Configure Database Connection

Edit the `alembic.ini` file and set your database connection string:

```ini
sqlalchemy.url = postgresql://username:password@localhost/dbname
```

Alternatively, you can configure the connection in `alembic/env.py` to use environment variables or your application's configuration.

## Create a Migration

Generate a new migration by auto-detecting changes in your models:

```bash
alembic revision --autogenerate -m "Description of your changes"
```

This will create a new migration file in the `alembic/versions` directory.

## Review the Migration

Always review the generated migration file to ensure it captures the intended changes correctly.

## Apply Migrations

Run the migration to update your database schema:

```bash
alembic upgrade head
```

## Additional Commands

- Check current migration version: `alembic current`
- View migration history: `alembic history`
- Downgrade to a previous version: `alembic downgrade -1`
- Downgrade to a specific version: `alembic downgrade <revision_id>`