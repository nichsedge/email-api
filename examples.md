# Email API Examples

## Mark Multiple Emails as Read (Batch)

To mark multiple emails as read in a single request, use the batch endpoint:

### cURL Example

```bash
curl -X POST "http://localhost:8000/emails/mark-read-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "email_ids": [
      "3",
      "4"
    ]
  }'
```

### Response Example

```json
{
  "status": "completed",
  "total_processed": 3,
  "success_count": 3,
  "failure_count": 0,
  "details": [
    {
      "email_id": "123",
      "status": "success",
      "message": "Email 123 marked as read"
    },
    {
      "email_id": "124", 
      "status": "success",
      "message": "Email 124 marked as read"
    },
    {
      "email_id": "125",
      "status": "success", 
      "message": "Email 125 marked as read"
    }
  ]
}
```

### Error Response Example

```json
{
  "status": "completed",
  "total_processed": 3,
  "success_count": 2,
  "failure_count": 1,
  "details": [
    {
      "email_id": "123",
      "status": "success",
      "message": "Email 123 marked as read"
    },
    {
      "email_id": "124",
      "status": "success",
      "message": "Email 124 marked as read"
    },
    {
      "email_id": "999",
      "status": "error",
      "message": "No message with that UID"
    }
  ]
}
```

## Other API Examples

### Get Unread Emails

```bash
curl "http://localhost:8000/emails?filter_by=today&mark_as_read=false"
```

### Mark Single Email as Read

```bash
curl -X POST "http://localhost:8000/emails/123/mark-read"
```
### Mark Multiple Emails as Unread (Batch)

To mark multiple emails as unread in a single request, use the batch endpoint:

```bash
curl -X POST "http://localhost:8000/emails/mark-unread-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "email_ids": [
      "3",
      "4"
    ]
  }'
```


### Send Email

```bash
curl -X POST "http://localhost:8000/send" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_email": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email"
  }'