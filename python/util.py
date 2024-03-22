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

def mbo_to_human(result):
    solved = str(99 - int(str(result)[0:2]))
    attempted = str(result)[2:4]
    t_in_sec = int(str(result[-5:]))
    
    m, s = divmod(t_in_sec, 60)
    h, m = divmod(m, 60)
    if s < 10 and m > 0:
        s = f"0{str(s)}"
    if m < 10 and h > 0:
        m = f"0{str(m)}"
    if t_in_sec < 60:
        return f"{solved}/{attempted} {s}"
    else:
        if t_in_sec < 3600:
            return f"{solved}/{attempted} {m}:{s}"
        else:
            return f"{solved}/{attempted} {h}:{m}:{s}"
        
    
def mbf_to_human(result):
    diff = 99 - int(str(result)[0:2])
    t_in_sec = int(str(result)[2:7])
    mis = int(str(result)[-2:])
    solved = diff + mis
    attempted = solved + mis
    
    m, s = divmod(t_in_sec, 60)
    h, m = divmod(m, 60)
    if s < 10 and m > 0:
        s = f"0{str(s)}"
    if m < 10 and h > 0:
        m = f"0{str(m)}"
    if t_in_sec < 60:
        return f"{solved}/{attempted} {s}"
    else:
        if t_in_sec < 3600:
            return f"{solved}/{attempted} {m}:{s}"
        else:
            return f"{solved}/{attempted} {h}:{m}:{s}"
