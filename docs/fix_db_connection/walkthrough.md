# Walkthrough - Database Connection Fix

## Problem
The user encountered a `psycopg2.OperationalError: Connection refused` when running `./start_prod.sh`. This was caused by the PostgreSQL database server not being installed/running on the local machine.

## Solution
1. Installed PostgreSQL (`postgresql`, `postgresql-contrib`).
2. Started the PostgreSQL service.
3. Created the database user `hirakata` and database `hirakata_bot` to match the application configuration.

## Verification
- Verified that the PostgreSQL service is running.
- Successfully connected to the database using the application's initialization script.
- Confirmed that tables can be created/accessed.

## Next Steps
The user can now run `./start_prod.sh` successfully.
