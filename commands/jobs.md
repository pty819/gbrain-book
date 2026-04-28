# Jobs

Manages background jobs and scheduled tasks.

## Synopsis

```bash
gbrain jobs [subcommand] [flags]
```

## Subcommands

### List Jobs

```bash
gbrain jobs list
gbrain jobs list --status running
```

Shows all background jobs:

```
Jobs
====
ID          Type        Status     Started              Progress
----------- ----------- ---------- ------------------- --------
a1b2c3d4    embed       running    2024-03-15 10:30:00  45%
e5f6g7h8    sync        completed  2024-03-15 10:25:00  100%
i9j0k1l2    extract     queued     -                    -
```

### Cancel Job

```bash
gbrain jobs cancel <job-id>
```

### Job Status

```bash
gbrain jobs status <job-id>
gbrain jobs status <job-id> --watch
```

### Purge Completed

```bash
gbrain jobs purge
gbrain jobs purge --older-than 7d
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--status <status>` | Filter by status | `none` |
| `--watch` | Continuously watch status | `false` |

## Job Types

| Type | Description |
|------|-------------|
| `embed` | Vector embedding generation |
| `sync` | Content synchronization |
| `extract` | Data extraction |
| `maintain` | Maintenance tasks |
| `publish` | Publishing operations |

## See Also

- {doc}`cron-scheduler` - Cron scheduling
- {doc}`daily-task-manager` - Task management
