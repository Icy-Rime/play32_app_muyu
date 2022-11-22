import os, sys
PLAY32DEV_PATH = "/run/media/dreagonmon/Data/Code/Python/play32-dev" # replace to your path
APP_NAME_ID = "play32app_template"
sys.path.append(PLAY32DEV_PATH)
import play32env
if __name__ == "__main__":
    app_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(app_dir, "apps")
    # >>>> init <<<<
    play32env.setup(app_dir)
    # >>>> test <<<<
    play32env.start_app(APP_NAME_ID)
