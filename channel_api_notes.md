# Notes

### [Get] /open/v5/user-chats

-   limit query [1, 500]

-   states: opened, snoozed, closed

-   Note: Use the **next** value and **since** parameter to paginate through all user chats:
    -   The next value is contained in the root object of the JSON response.
    -   Successive queries to this endpoint using the previous next value as the since parameter will ultimately retrieve all user chats.
    -   The since parameter can be left empty to start the list.


```


 

            
        
```
