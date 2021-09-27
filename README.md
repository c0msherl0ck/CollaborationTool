# The Message Carving Tool for Slack and Microsoft Teams

Developed as a part of Journal of The Korea Institute of Information Security & Cryptology<br>
"A Study on Message Acquisition from Electron-based Collaboration Tool: Focused on Jandi, Slack, and Microsoft Teams"


# Usage

message.py -i {IndexedDB_FilePath} -m {slack, teams}<br>
```
message.py -i "~AppData\Roaming\Slack\IndexedDB\https_app.slack.com_0.indexeddb.blob\1\00\3c" -m slack
message.py -i "~AppData\Roaming\Microsoft\Teams\IndexedDB\https_teams.live.com_0.indexeddb.leveldb\000004.log" -m teams
message.py -i "~AppData\Roaming\Microsoft\Teams\IndexedDB\https_teams.live.com_0.indexeddb.leveldb\000005.ldb" -m teams
```

# License

Copyright © 2021. c0msherl0ck. All Rights Reserved.
