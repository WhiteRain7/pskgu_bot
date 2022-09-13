from calendar import month
from pskgu_bot.bots import messages
from pskgu_bot.bots.base.shedule.find_group import try_guess_user_group

from pskgu_bot.db.services import (find_vk_user_by_id, find_group_by_name)
from pskgu_bot.utils import (get_week_days, get_name_of_day, str_to_int,
                             logger, double_list_to_str)
from pskgu_bot.config import Config
from typing import Optional, BinaryIO
from .to_image import week_to_image
from io import BytesIO

MONTHS = {'01': 'янв',
          '02': 'фев',
          '03': 'мар',
          '04': 'апр',
          '05': 'май',
          '06': 'июн',
          '07': 'июл',
          '08': 'авг',
          '09': 'сен',
          '10': 'окт',
          '11': 'ноя',
          '12': 'дек'}

def key_to_normal_format(key: str) -> str:
    y, m, d = key.split('-')
    return MONTHS[m] + ' ' + d


async def show_schedule(user_id: Optional[str] = None,
                        group_name: Optional[str] = None,
                        week_shift: Optional[str] = None,
                        image: bool = False,
                        type_sys: str = "vk") -> (str, BinaryIO):
    """
        Возвращает расписание недели.
    """
    def make_readable_text(group, keys):
        """
            Преобразуем словарь group.days в читаемое сообщение.
        """
        mess = ""
        for key in keys:
            day = group.days.get(key)
            if day:
                day_name = get_name_of_day(key)
                mess += day_name + ", " + key + "\n"
                for x, lesson in day.items():
                    mess += x + ") " + double_list_to_str(lesson) + "\n"
                mess += "\n"
        if mess == "":
            first_date = key_to_normal_format(min(keys))
            last_date = key_to_normal_format(max(keys))
            mess = f"\nНа этой неделе ({first_date} - {last_date}) нет никаких занятий.\nВозможно, их и не должно быть.\n"
        return mess

    def add_name(group):
        """
            Вставка имени преподавателя или названия группы.
        """
        if group.prefix[0] == "преподаватель":
            return "Преподаватель"
        else:
            return "Группа"

    if (group_name is None or group_name == ""):
        group_name = None

    user_id = str_to_int(user_id)

    week_shift = str_to_int(week_shift)
    if week_shift is None:
        week_shift = 0

    if (user_id is not None and group_name is None and type_sys == "vk"):
        user = await find_vk_user_by_id(user_id)
        if user:
            group_name = user.group

    if (group_name is None or group_name == ""):
        return messages.MSG_NO_NAME_AND_USER_GROUP, None

    group = await find_group_by_name(group_name)
    if not group: return await try_guess_user_group(group_name), None

    if image:
        try:
            img = await week_to_image(group.days, group_name, add_name(group),
                                      week_shift)
            return "Расписание.", img
        except Exception as e:
            logger.error(e)
            return "Произошла ошибка при создании изображения.", None

    mess = ""
    days = get_week_days(week_shift)
    mess += add_name(group) + ": " + group.name + "\n"
    web_bot = "{0}?find_group_name={1}&from=vk.com".format(
        Config.WEB_URL, group.name)
    mess += "Оригинал: {0}\nWeb-версия бота: {1}\n".format(
        group.page_url, web_bot)
    mess += make_readable_text(group, days)

    return mess, None
