def time_valid(input_time: str) -> bool:
    try:
        hours = int(input_time.split(":")[0])
        minutes = int(input_time.split(":")[1])
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return True
    except ValueError:
        return False
    return False


def count_work_time(start_time: str, end_time: str) -> dict:
    if start_time and end_time:
        # Вычисляем отработанное время
        start_hours, start_minutes = map(int, start_time.split(':'))
        end_hours, end_minutes = map(int, end_time.split(':'))
        total_minutes = (end_hours * 60 + end_minutes) - (start_hours * 60 + start_minutes)
        total_hours = total_minutes // 60
        total_minutes %= 60
        if total_hours <= 4:
            total_hours = total_hours
        else:
            total_hours -= 1
    return {"total_hours": total_hours, "total_minutes": total_minutes}
