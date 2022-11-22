import hal_screen, hal_keypad, hal_buzz, utime, ujson, uos, framebuf
from graphic import framebuf_helper, pbm
from play32sys import app, path
from buildin_resource.font import get_font_8px
from ui.select import select_menu, select_list
from ui.dialog import dialog
from play32hw.cpu import cpu_speed_context, VERY_SLOW, FAST
from machine import lightsleep
FONT_8 = get_font_8px()
WHITE = framebuf_helper.get_white_color(hal_screen.get_format())

drawables = set()
need_remove = set()
muyu = None # type: MuyuImage
gongde_img = None # type: framebuf.FrameBuffer
gongde_offset_x = 0
gongde_offset_y = 0
count_area = (0, 0, 0, 0)
game_data = dict() # type: dict[str, any]
save_path = "/data/muyu/save.json"

class MuyuImage:
    def __init__(self, img_48, img_64, img_64c):
        self.x = 0
        self.y = 0
        self.img = (img_64, img_48, img_64c)
        self.imgsel = 0
        self.last_click = -1
    
    def click(self, crit=False):
        self.imgsel = 2 if crit else 1
        self.last_click = utime.ticks_ms()
        hal_buzz.get_buzz_player().note_on(64 if crit else 48, 9)
    
    def update(self):
        # status
        if self.last_click > 0:
            now = utime.ticks_ms()
            if utime.ticks_diff(now, self.last_click) >= 50: # ms
                hal_buzz.get_buzz_player().stop()
                self.imgsel = 0
                self.last_click = -1
            return True
        return False

    def draw(self, frame):
        # draw
        if self.imgsel == 1:
            frame.blit(self.img[1], self.x + 8, self.y + 8, 0)
        elif self.imgsel == 2:
            frame.blit(self.img[2], self.x, self.y, 0)
        elif self.imgsel == 0:
            frame.blit(self.img[0], self.x, self.y, 0)

class GongDeText:
    def __init__(self):
        self.y = gongde_offset_y
        self.last_update = 0
    
    def update(self):
        # status
        now = utime.ticks_us()
        if self.last_update > 0:
            diff = utime.ticks_diff(now, self.last_update) # us
            offset_y = 128 * diff / 1000000 # 128 pix / s
            self.y -= offset_y
            if self.y + FONT_8.get_font_size()[1] < 0:
                need_remove.add(self)
                return True
        self.last_update = now
        return True

    def draw(self, frame):
        # draw
        frame.blit(gongde_img, gongde_offset_x, int(self.y), 0)

class GongDeCount:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0
        self.last = -1
    
    def update(self):
        # status
        gongde = game_data.get("gongde", 0)
        if gongde != self.last:
            f_w, f_h = FONT_8.get_font_size()
            a_x, a_y, a_w, a_h = count_area
            text = str(gongde)
            self.x = (a_w - (len(text) * f_w)) // 2 + a_x
            self.y = (a_h - f_h) // 2 + a_y
            self.last = gongde
            return True
        return False
    
    def draw(self, frame):
        # draw
        FONT_8.draw_on_frame(str(self.last), frame, self.x, self.y, WHITE)

class AutoClick:
    def __init__(self):
        self.last = utime.ticks_ms()
    
    def auto(self):
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self.last) > game_data.get("muyu_auto", 5000):
            click()
            self.last = now

def load_assert(app_name):
    global muyu, gongde_img, gongde_offset_x, gongde_offset_y, count_area, save_path, game_data
    img_dir = path.join(path.get_app_path(app_name), "images")
    muyu48_path = path.join(img_dir, "muyu48.pbm")
    muyu64_path = path.join(img_dir, "muyu64.pbm")
    muyu64c_path = path.join(img_dir, "muyu64c.pbm")
    with open(muyu48_path, "rb") as f:
        w, h, _f, data, _c = pbm.read_image(f)
        muyu48 = framebuf.FrameBuffer(data, w, h, framebuf.MONO_HLSB)
        muyu48 = framebuf_helper.ensure_same_format(muyu48, framebuf.MONO_HLSB, w, h, hal_screen.get_format(), WHITE)
    with open(muyu64_path, "rb") as f:
        w, h, _f, data, _c = pbm.read_image(f)
        muyu64 = framebuf.FrameBuffer(data, w, h, framebuf.MONO_HLSB)
        muyu64 = framebuf_helper.ensure_same_format(muyu64, framebuf.MONO_HLSB, w, h, hal_screen.get_format(), WHITE)
    with open(muyu64c_path, "rb") as f:
        w, h, _f, data, _c = pbm.read_image(f)
        muyu64c = framebuf.FrameBuffer(data, w, h, framebuf.MONO_HLSB)
        muyu64c = framebuf_helper.ensure_same_format(muyu64c, framebuf.MONO_HLSB, w, h, hal_screen.get_format(), WHITE)
    muyu = MuyuImage(muyu48, muyu64, muyu64c)
    scr_w, scr_h = hal_screen.get_size()
    w, h = FONT_8.get_font_size()
    gongde_offset_x = scr_w - (w*4)
    gongde_offset_y = scr_h - h
    gongde_img = framebuf_helper.new_framebuffer(w*4, h, hal_screen.get_format())
    FONT_8.draw_on_frame("功德++", gongde_img, 0, 0, WHITE)
    drawables.add(muyu)
    count_area = 64, 0, scr_w - 64, scr_h
    drawables.add(GongDeCount())
    save_path = path.join(path.get_data_path(app_name), "save.json")
    try:
        if not path.exist(path.get_data_path(app_name)):
            path.mkdirs(path.get_data_path(app_name))
        with open(save_path, "r") as f:
            game_data = ujson.load(f)
    except: pass

def save():
    with open(save_path, "w") as f:
        ujson.dump(game_data, f)

def muyu_render(force=False):
    frame = hal_screen.get_framebuffer()
    frame.fill(0)
    it = [ d.update() for d in drawables ]
    refresh = any(it)
    for d in need_remove:
        drawables.discard(d)
    if refresh or force:
        with cpu_speed_context(FAST):
            for d in drawables:
                d.draw(frame)
            hal_screen.refresh()
    need_remove.clear()
    return refresh

def crit(chance):
    """ chance in [0, 100] """
    if chance <= 0:
        return False
    if chance >= 100:
        return True
    rand = int.from_bytes(uos.urandom(2), "big") # 0 ~ 0xFFFF
    rand = rand * 100 // 0xFFFF
    return rand <= chance - 1

def click():
    chance = game_data.get("muyu_crit", 0)
    if crit(chance):
        muyu.click(True)
        game_data["gongde"] = game_data.get("gongde", 0) + game_data.get("muyu_level", 1) * 10
    else:
        muyu.click(False)
        game_data["gongde"] = game_data.get("gongde", 0) + game_data.get("muyu_level", 1)
    gongde_float = GongDeText()
    drawables.add(gongde_float)

def text_status():
    return  " 当前功德: {}\n".format(game_data.get("gongde", 0)) + \
            " 总计功德: {}\n".format(game_data.get("gongde", 0) + game_data.get("used_gongde", 0)) + \
            " 木鱼等级: {}\n".format(game_data.get("muyu_level", 1)) + \
            " 自动敲击: {:.2f}秒\n".format(game_data.get("muyu_auto", 5000) / 1000) + \
            " 暴击率: {}%\n".format(game_data.get("muyu_crit", 0)) + \
            ""

def main(app_name, *args, **kws):
    hal_screen.init()
    hal_keypad.init()
    hal_buzz.init()
    # app_name is app`s dir name in fact.
    load_assert(app_name)
    main_loop()

MAIN_MENU = ["积累功德", "升级木鱼", "退出"]
YES = "确定"
NO = "取消"
def main_loop():
    muyu_loop()
    save()
    while True:
        hal_buzz.get_buzz_player().stop()
        sel = select_menu(text_status(), "Cyber木鱼", MAIN_MENU, text_yes=YES, text_no="积累功德")
        if sel < 0:
            muyu_loop()
            save()
        elif sel == 0:
            muyu_loop()
            save()
        elif sel == 1:
            upgrade_menu()
        elif sel == len(MAIN_MENU) - 1:
            app.reset_and_run_app("")

def muyu_loop():
    with cpu_speed_context(VERY_SLOW):
        ac = AutoClick()
        muyu_render(True)
        while True:
            ac.auto()
            for event in hal_keypad.get_key_event():
                event_type, key = hal_keypad.parse_key_event(event)
                if event_type == hal_keypad.EVENT_KEY_PRESS:
                    if key == hal_keypad.KEY_A:
                        click()
                    elif key == hal_keypad.KEY_B:
                        return
            if not muyu_render():
                lightsleep(10)

UPGRADE_MENU = ["升级等级", "减少自动敲击间隔", "提高暴击率"]
def upgrade_menu():
    sel = select_list("升级木鱼", UPGRADE_MENU, text_yes=YES, text_no=NO)
    gongde = game_data.get("gongde", 0)
    spent = 0
    if sel < 0:
        return
    elif sel == 0:
        level = game_data.get("muyu_level", 1)
        if level >= 9:
            dialog("已经达到最高等级", text_yes=YES, text_no=YES)
            return
        price = [100, 400, 1600, 6400, 12800, 51200, 204800, 819200]
        spent = price[level - 1]
        if gongde >= spent:
            game_data["muyu_level"] = level + 1
    elif sel == 1:
        delay = game_data.get("muyu_auto", 5000)
        if delay <= 200:
            dialog("已经达到最高等级", text_yes=YES, text_no=YES)
            return
        price =      [100,  200,  400,  800,  1600, 3200, 6400, 12800, 25600, 51200, 102400, 204800]
        delay_list = [5000, 4500, 4000, 3500, 3000, 2500, 2000, 1500,  1000,  750,   500,    300, 200]
        index = delay_list.index(delay)
        spent = price[index]
        if gongde >= spent:
            game_data["muyu_auto"] = delay_list[index + 1]
    elif sel == 2:
        rate = game_data.get("muyu_crit", 0)
        if rate >= 100:
            dialog("已经达到最高等级", text_yes=YES, text_no=YES)
            return
        spent = 50 * (2 ** (rate // 10 + 1)) * (rate + 1)
        if gongde >= spent:
            game_data["muyu_crit"] = rate + 1
    # 
    if gongde < spent:
        dialog("功德不足，升级失败\n升级需要功德: {}".format(spent), text_yes=YES, text_no=YES)
    else:
        game_data["gongde"] = gongde - spent
        game_data["used_gongde"] = game_data.get("used_gongde", 0) + spent
        save()
