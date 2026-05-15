#!/bin/bash
set -e

echo "Waiting for MySQL to be ready..."

MAX_RETRIES=30
RETRY_INTERVAL=2
RETRY_COUNT=0

until python -c "
import os, pymysql
conn = pymysql.connect(
    host=os.environ['DB_HOST'],
    port=int(os.environ.get('DB_PORT', '3306')),
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME']
)
conn.close()
print('MySQL is ready!')
" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: MySQL did not become ready in time ($((MAX_RETRIES * RETRY_INTERVAL)) seconds)"
        exit 1
    fi
    echo "MySQL is unavailable - retrying (${RETRY_COUNT}/${MAX_RETRIES})..."
    sleep $RETRY_INTERVAL
done

echo "MySQL is ready! Starting services..."

python schedule.py &
SCHEDULER_PID=$!

python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000)" &
WEB_PID=$!

wait -n $SCHEDULER_PID $WEB_PID

echo "A process exited unexpectedly. Shutting down..."
kill $SCHEDULER_PID $WEB_PID 2>/dev/null
exit 1
