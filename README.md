# play32app_template

## Required 
install [mpypack](https://github.com/Dreagonmon/mpypack)
- change app name and icon in ``` apps/play32app_template/manifest.json ```
- rename ``` apps/play32app_template ``` to your app name(id)
- change "port", "local", "source", "remote" and "output" in ``` .mpypack.conf ```

## Optional Setup
download [play32 dev library](https://github.com/Icy-Rime/play32-dev).

- change "PLAY32DEV_PATH" and "APP_NAME_ID" in ``` main.py ```
- change python autoComplete and analysis path in ``` .vscode/settings.json ```

## Test Run
using ``` mpypack sync ``` to sync this app to the PLAY32 board. then run it from the app selector. using ``` mpypack repl ``` to use repl.

or, run it on desktop, execute ``` python main.py ```. note whether you can run it on desktop, you should finally test it on real devices. the [play32 dev library](https://github.com/Icy-Rime/play32-dev) could only provide some of the "micropython" library that the game apps required. most of the libraries that operate hardware, will not work.
