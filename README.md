# hyper-channel 🚀

A simple application to view chat messages between managers and participants using the [channel.io open API](https://api-doc.channel.io/).

![Capture](capture.png)

## Endpoints

### GET /api/managers/{manager_id}/chats/{state}/{limit}/{sort_order}/{date}

```json
{
    "chats": [
        {
            "chat_message": "Hello, world!",
            "created_at": "2024-06-11 08:29:01",
            "participant_id": "69420",
            "participant_name": "John Doe",
        }, ...
    ],
    "count": 69,
    "date": "2024-06-11",
    "manager_id": "42069"
}
```
