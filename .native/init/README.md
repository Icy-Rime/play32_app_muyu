# debug init script

change "APP_NAME_ID" in the ``` main.py ``` to your app name(id)

mpypack sync this dir, and during boot, play32 will always load your app. system app selector will not be loaded.

to restore, in the repl:

```python
import uos
uos.remove("/main.py")
uos.remove("/boot.py")
uos.remove("/framework_debug")
```