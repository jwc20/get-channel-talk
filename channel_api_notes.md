# Notes

## [Get] /open/v5/user-chats

- limit query [1, 500]

- states: opened, snoozed, closed

- Note: Use the **next** value and **since** parameter to paginate through all user chats:
  - The next value is contained in the root object of the JSON response.
  - Successive queries to this endpoint using the previous next value as the since parameter will ultimately retrieve all user chats.
  - The since parameter can be left empty to start the list.

```json
{
    "next": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MjUwMzQsInNpbmNlIjoiMjAyMS0wOC0xNlQxNzoxNzoxMi4wMDAwMDAwMDAwIn0.1Z
    "user_chats": [
        {
            "id": 25034,
            "state": "opened",
            ...
        },
        {
            "id": 25035,
            "state": "opened",
            ...
        },
        ...
    ]
}
```
