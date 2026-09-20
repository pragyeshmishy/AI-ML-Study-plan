# Prompt: Build AWS Lambda Data Retention Function

Use this prompt when you're ready to build the monthly data cleanup Lambda.

---

## Prompt

```
Build an AWS Lambda function for automated data retention in the Scheduling Service system.

## What This Lambda Does

It runs once a month (triggered by AWS EventBridge) and deletes schedule records older
than a configurable retention period (default: 90 days) from the PostgreSQL or AWS RDS database.
This prevents the database from growing indefinitely.

## Database Details

- **Database**: Amazon RDS PostgreSQL
- **Schema**: `scheduling`
- **Connection**: The Lambda will need these environment variables:
  - DB_HOST (RDS endpoint)
  - DB_PORT (default: 5432)
  - DB_NAME
  - DB_USER
  - DB_PASSWORD (should come from AWS Secrets Manager, not plaintext env var)
  - RETENTION_DAYS (default: 90)

## Tables Involved

### Table 1: `scheduling.schedule_status_tracker` (PRIMARY TARGET)
This is the main table to delete from. Key columns:
- `schedule_id` VARCHAR(50) — Primary Key
- `current_status` VARCHAR(50) — e.g., COMPLETED, FAILED, PENDING, IN_PROGRESS
- `creation_date` TIMESTAMP WITH TIME ZONE — When the record was created (USE THIS for age check)
- `last_updated_date` TIMESTAMP WITH TIME ZONE — Last update timestamp

### Table 2: `scheduling.schedule_audit_log` (AUTO-DELETED VIA CASCADE)
- `schedule_id` VARCHAR(50) — Foreign Key to schedule_status_tracker with ON DELETE CASCADE
- This means: when you delete a row from schedule_status_tracker, ALL its audit log
  entries are automatically deleted. You do NOT need to delete from this table manually.

## What the Lambda Should Do

1. Connect to RDS PostgreSQL
2. SAFETY CHECK: Only delete records where `current_status` is COMPLETED or FAILED
   (never delete PENDING or IN_PROGRESS jobs — they might still be running)
3. Delete from `scheduling.schedule_status_tracker` where:
   - `creation_date` < NOW() - INTERVAL '{RETENTION_DAYS} days'
   - AND `current_status` IN ('COMPLETED', 'FAILED')
4. The CASCADE foreign key on schedule_audit_log handles audit cleanup automatically
5. Log how many records were deleted
6. Return a summary response

## SQL Query

The core query should be:

DELETE FROM scheduling.schedule_status_tracker
WHERE creation_date < NOW() - INTERVAL '90 days'
  AND current_status IN ('COMPLETED', 'FAILED');

Note: The 90 days should come from the RETENTION_DAYS environment variable.

## Technical Requirements

- **Runtime**: Python 3.11+
- **Database library**: Use `psycopg2` (include `psycopg2-binary` in the Lambda layer or package)
- **Secrets**: Retrieve DB password from AWS Secrets Manager (not environment variable)
  - Secret name should be configurable via environment variable: `DB_SECRET_NAME`
- **Timeout**: Set Lambda timeout to 60 seconds (this query should be fast)
- **Memory**: 128 MB is sufficient
- **VPC**: The Lambda MUST be deployed in the same VPC as the RDS instance,
  with security group access to the RDS port (5432)

## EventBridge Rule

Create an EventBridge rule that triggers the Lambda:
- Schedule expression: `cron(0 2 1 * ? *)` — 1st day of every month at 2:00 AM UTC
- This avoids peak hours

## Error Handling

- If DB connection fails: Log error, return failure response (do NOT retry —
  it'll run again next month)
- If the DELETE query fails: Rollback the transaction, log error, return failure
- If Secrets Manager fails: Log error, return failure

## Logging

Log the following to CloudWatch:
- Start time
- Retention period being used
- Number of records found matching criteria (run a COUNT first)
- Number of records deleted
- End time and duration
- Any errors with full stack trace

## Response Format

The Lambda should return:
{
  "statusCode": 200,
  "body": {
    "message": "Data retention completed successfully",
    "retention_days": 90,
    "records_deleted": 1234,
    "execution_time_ms": 450,
    "timestamp": "2026-03-01T02:00:00Z"
  }
}

## File Structure

Create the Lambda as a standalone directory in the project:

lambda/
  data-retention/
    lambda_function.py    # Main handler
    requirements.txt      # psycopg2-binary, boto3
    template.yaml         # SAM/CloudFormation template (EventBridge + Lambda + IAM role)
    README.md             # How to deploy and test

## Security Considerations

- DB password from Secrets Manager, NEVER hardcoded or in environment variables
- Lambda IAM role needs:
  - secretsmanager:GetSecretValue (for DB credentials)
  - ec2:CreateNetworkInterface, ec2:DescribeNetworkInterfaces,
    ec2:DeleteNetworkInterface (for VPC access)
  - logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents (for CloudWatch)
- NO broad permissions — principle of least privilege
- The Lambda should only have DELETE permission on the scheduling schema
  (use a dedicated DB user with restricted permissions)

## Testing

- Include a test event that can be used for local testing:
  {
    "source": "manual-test",
    "detail": {
      "retention_days_override": 90
    }
  }
- Allow a `retention_days_override` in the event payload for testing with
  different retention periods without changing the environment variable
- Add unit tests that mock the database connection and verify:
  - Correct SQL is generated
  - Only COMPLETED/FAILED records are targeted
  - Secrets Manager is called correctly
  - Error handling works as expected
```

---

## Context Files for Reference

When building this, these existing files provide useful context:

| File | Why It's Relevant |
|------|------------------|
| `scheduling-engine/src/app/models/audit_models.py` | Exact table schema (ScheduleStatusTracker, ScheduleAuditLog) |
| `scheduling-engine/src/app/core/config.py` | Database connection settings pattern |
| `scheduling-engine/src/app/core/database.py` | Existing database connection setup |
| `docs/ARCHITECTURE.md` (lines 149-153) | Architecture requirement for this Lambda |
| `docs/ARCHITECTURE_DIFFERENCES.md` (Difference #9) | Why this is needed |
