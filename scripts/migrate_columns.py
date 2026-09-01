# -*- coding: utf-8 -*-
import sqlite3

def run_migration():
    conn = sqlite3.connect("data/damga_ops.db")
    cursor = conn.cursor()

    tables_to_check = [
        ("daily_operations", "verification_status", "TEXT NOT NULL DEFAULT 'UNVERIFIED'"),
        ("daily_facts", "verification_status", "TEXT NOT NULL DEFAULT 'UNVERIFIED'"),
        ("alerts", "verification_status", "TEXT NOT NULL DEFAULT 'UNVERIFIED'"),
        ("period_alerts", "verification_status", "TEXT NOT NULL DEFAULT 'UNVERIFIED'"),
        ("ingestion_runs", "verification_status", "TEXT NOT NULL DEFAULT 'UNVERIFIED'"),
        ("analyst_briefs", "verification_status", "TEXT DEFAULT 'UNVERIFIED'")
    ]

    for table, col, col_type in tables_to_check:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if col not in columns:
            print(f"Adding {col} to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            print(f"Added {col} to {table}.")
        else:
            print(f"{table}.{col} already exists.")

    conn.commit()
    conn.close()
    print("Migration check complete.")

if __name__ == "__main__":
    run_migration()

