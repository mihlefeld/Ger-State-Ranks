def centiseconds_to_human(result):
    as_integer = int(result)
    centi = int(str(result)[-2:])
    if centi < 10:
        centi = f"0{str(centi)}"
    if as_integer < 100:
        return f"0.{as_integer}"
    else:
        seconds_or_more = int(str(result)[:-2])
        m, s = divmod(seconds_or_more, 60)
        h, m = divmod(m, 60)
        if s < 10 and m > 0:
            s = f"0{str(s)}"
        if m < 10 and h > 0:
            m = f"0{str(m)}"
        if seconds_or_more < 60:
            return f"{s}.{centi}"
        else:
            if seconds_or_more < 3600:
                return f"{m}:{s}.{centi}"
            else:
                return f"{h}:{m}:{s}.{centi}"
