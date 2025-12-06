# Implementation Plan - Fix Database Connection

## Goal
Install and configure PostgreSQL locally to resolve "Connection refused" error.

## Proposed Changes
1. Install `postgresql` and `postgresql-contrib` packages.
2. Start PostgreSQL service.
3. Create PostgreSQL user `hirakata` with password `hirakata`.
4. Create database `hirakata_bot` owned by `hirakata`.

## Verification Plan
1. Run `start_prod.sh` (or the db init part) to verify connection.
2. Check logs for successful startup.
