# Scheduling pipeline.py with Cron

## Run daily at 7:00 AM

Open your crontab editor:

```bash
crontab -e
```

Add this line (adjust the path to match your project location):

```
0 7 * * * /usr/bin/python3 /path/to/project/pipeline.py >> /path/to/project/logs/cron.log 2>&1
```

## Verify it is registered

```bash
crontab -l
```

## Common schedules

| Schedule         | Cron expression     |
|------------------|---------------------|
| Every day at 7am | `0 7 * * *`         |
| Every 6 hours    | `0 */6 * * *`       |
| Every hour       | `0 * * * *`         |
| Weekdays at 8am  | `0 8 * * 1-5`       |

## Notes

- The pipeline logs its own run details to `logs/pipeline.log`.
- Redirect cron stdout/stderr to `logs/cron.log` to capture system-level errors.
- On macOS, use **launchd** instead of cron for more reliable scheduling.
- On Linux servers, consider **systemd timers** as a modern cron alternative.
