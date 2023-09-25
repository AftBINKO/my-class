from app import scheduler, CONFIG_PATH, app
from app.data.functions import clear_times


@scheduler.task("cron", id="everyday", hour="00", minute="00")
def everyday():
    clear_times(CONFIG_PATH, echo=app.debug)


@scheduler.task("cron", id="everyyear", month="09", day="01")
def everyyear():
    clear_times(CONFIG_PATH, echo=app.debug, all_times=True)
