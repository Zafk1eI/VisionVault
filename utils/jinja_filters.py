from datetime import datetime

import humanize


def time_since_upload(created_at):
    humanize.i18n.activate("ru_RU")
    return humanize.naturaltime(created_at)


def get_correct_word_form(count, singular, genitive, plural):
    if count % 10 == 1 and count % 100 != 11:
        return singular  
    elif count % 10 in [2, 3, 4] and not (count % 100 in [12, 13, 14]):
        return genitive  
    else:
        return plural 


def format_views(views):
    word_form = get_correct_word_form(views, "просмотр", "просмотра", "просмотров")

    if views >= 1_000_000:
        views_formatted = f"{views // 1_000_000}M"
    elif views >= 1_000:
        views_formatted = f"{views // 1_000}K"
    else:
        views_formatted = str(views)

    return f"{views_formatted} {word_form}"


def format_subscribers(subscribers):
    count = len(list(subscribers))
    word_form = get_correct_word_form(count, "подписчик", "подписчика", "подписчиков")
    if count >= 1_000_000:
        return f"{subscribers // 1_000_000}M {word_form}"
    elif count >= 1_000:
        return f"{count // 1_000}K {word_form}"
    return f"{count} {word_form}"
