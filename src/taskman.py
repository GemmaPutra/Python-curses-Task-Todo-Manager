import string
from typing import Any, NewType
from enum import Enum, auto
import os
import time

try:
    import curses
    from curses import wrapper
    from curses.textpad import Textbox, rectangle
except ModuleNotFoundError as _:
    print("'curses' module not found")
    quit()

from account import Account, create_account, get_account, delete_account, verify_account
from maid import shortened_content, poslog, divide_list, convert_todo_check

limit_char = 20
debug = False
esc_info = "'esc' to exit"
enter_info = "'enter' to continue"
warn_no_input = "no input get caught"
Warning_Color = None
commands = [
    "task",
    "todo",
    "check",
    "uncheck",
    "edit",
    "logout",
    "delete",
    "exit",
    "quit",
]

_stdscr = NewType("_stdscr", Any)
# _stdscr = NewType("_stdscr", curses._CursesWindow)


class GetType(Enum):
    Normal = auto()
    Password = auto()


def centerize(_size_width: int, _object_width: int) -> tuple[int, int]:
    return (_size_width // 2) - (_object_width // 2)


def write_info(stdscr: _stdscr, _info: str, /) -> None:
    stdscr.addstr(curses.LINES - 1, (curses.COLS - 1) - len(_info), _info)


def write_info_on_command_box(stdscr: _stdscr, _info: str, /) -> None:
    stdscr.addstr(curses.LINES - 4, 1, _info)


def write_warning(stdscr: _stdscr, _warning: str, /) -> None:
    stdscr.addstr(
        curses.LINES - 4,
        (curses.COLS - 1) - len(_warning),
        _warning,
        curses.color_pair(Warning_Color),
    )


def curse_input(
    stdscr: _stdscr,
    _fy: int,
    _fx: int,
    _limit: int,
    /,
    *,
    type: GetType = GetType.Normal,
) -> str | None:
    word = []
    cpos = 0

    if type is GetType.Normal:
        curses.echo()
    if type is GetType.Password:
        curses.noecho()

    while True:
        if type is GetType.Normal:
            stdscr.move(_fy, _fx + cpos)
        if type is GetType.Password:
            stdscr.move(_fy, _fx)
            curses.curs_set(False)
        ch = stdscr.getch()

        if ch == curses.KEY_ENTER or ch == ord("\n"):
            break
        elif ch == curses.KEY_BACKSPACE or ch == ord("\b"):
            if cpos > 0:
                cpos -= 1
                word.pop()
                stdscr.delch(_fy, _fx + cpos)
                stdscr.move(_fy, _fx + cpos)
            if cpos == 0:
                if word != []:
                    word.pop()
                stdscr.addstr(_fy, _fx, " ")
        elif ch == 27 or ch == ord("\x1b"):
            stdscr.delch(_fy, _fx + cpos)
            stdscr.move(_fy, _fx + cpos)
            stdscr.addstr(_fy, _fx + cpos, " ")
            return None
        else:
            if chr(ch) in string.ascii_letters or chr(ch) in string.digits:
                word.append(chr(ch))
                cpos += 1

        if cpos >= _limit:
            cpos = _limit

    curses.echo()
    curses.curs_set(True)
    output = "".join(word).strip()
    if output == "":
        return None
    else:
        return output


def curse_yesno(stdscr: _stdscr, _fy: int, _fx: int, /) -> str | None:
    word = "n"
    cpos = 0
    limit_ask = 1

    curses.echo()

    while True:
        stdscr.move(_fy, _fx + cpos)
        ch = stdscr.getch()

        if ch == curses.KEY_ENTER or ch == ord("\n"):
            curses.echo()
            if word == "n":
                return False
            if word == "y":
                return True
        if ch == curses.KEY_BACKSPACE or ch == ord("\b"):
            if cpos > 0:
                cpos -= 1
                word = ""
                stdscr.delch(_fy, _fx + cpos)
                stdscr.move(_fy, _fx + cpos)
            if cpos == 0:
                word = ""
                stdscr.addstr(_fy, _fx, " ")
        if ch == 27 or ch == ord("\x1b"):
            stdscr.delch(_fy, _fx + cpos)
            stdscr.move(_fy, _fx + cpos)
            stdscr.addstr(_fy, _fx + cpos, " ")
        if chr(ch) in "yn":
            cpos += 1
            word = chr(ch)
        else:
            if cpos > 0:
                cpos -= 1
                stdscr.delch(_fy, _fx + cpos)
                stdscr.move(_fy, _fx + cpos)
            if cpos == 0:
                stdscr.addstr(_fy, _fx, " ")

        if cpos >= limit_ask:
            cpos = limit_ask


# unused
def curse_num(
    stdscr: _stdscr, _fy: int, _fx: int, /, num_required: list[int]
) -> str | None:
    num = None
    cpos = 0
    limit_ask = 1

    curses.echo()

    while True:
        stdscr.move(_fy, _fx + cpos)
        ch = stdscr.getch()

        if ch == curses.KEY_ENTER or ch == ord("\n"):
            curses.echo()
            if any(num == n for n in num_required):
                return int(chr(ch))
        if ch == curses.KEY_BACKSPACE or ch == ord("\b"):
            if cpos > 0:
                cpos -= 1
                num = None
                stdscr.delch(_fy, _fx + cpos)
                stdscr.move(_fy, _fx + cpos)
            if cpos == 0:
                num = None
                stdscr.addstr(_fy, _fx, " ")
        if ch == 27 or ch == ord("\x1b"):
            stdscr.delch(_fy, _fx + cpos)
            stdscr.move(_fy, _fx + cpos)
            stdscr.addstr(_fy, _fx + cpos, " ")
        if chr(ch) in num_required:
            cpos += 1
            num = chr(ch)
        else:
            if cpos > 0:
                cpos -= 1
                stdscr.delch(_fy, _fx + cpos)
                stdscr.move(_fy, _fx + cpos)
            if cpos == 0:
                stdscr.addstr(_fy, _fx, " ")

        if cpos >= limit_ask:
            cpos = limit_ask


def curse_gen_list(stdscr: _stdscr, _fx: int, _fy: int, _items: list[Any], /) -> None:
    for idx_, itm_ in enumerate(_items):
        stdscr.addstr(_fy + idx_, _fx, itm_)


def curse_interactive(stdscr: _stdscr, limit: str = None) -> str:
    curses.noecho()
    curses.napms(50)
    curses.curs_set(True)
    stdscr.keypad(True)
    rectangle(stdscr, curses.LINES - 3, 1, curses.LINES - 1, curses.COLS - 2)
    stdscr.refresh()
    win = curses.newwin(1, curses.COLS - 2, curses.LINES - 1, 1)
    win.refresh()
    box = Textbox(win, insert_mode=True)
    text = ""

    while True:
        char = win.getch()

        if char == ord("\n"):  # enter
            text = box.gather()
            break
        elif char == 27:  # esc
            return -1
        elif char == 17:  # ctrl + q
            return -1
        elif char == 8:  # backspace
            box.do_command(char)
        elif char == 3:
            continue
        else:
            if limit is not None:
                if chr(char) in limit:
                    # poslog(chr(char))
                    box.do_command(char)
            else:
                # poslog(char)
                box.do_command(char)
    return text


def curse_editable(stdscr: _stdscr, past_text: str = None) -> str | None:
    curses.noecho()
    stdscr.keypad(True)
    stdscr.clear()
    stdscr.refresh()
    # win = curses.newwin(
    #     curses.LINES - ((curses.LINES // 2) - 10) - 4,
    #     curses.COLS - 1,
    #     (curses.LINES // 2) - 10,
    #     1,
    # )
    hgh, wdh = stdscr.getmaxyx()
    rectangle(stdscr, 3, 1, hgh - 10, wdh - 10)
    win = curses.newwin(
        curses.LINES - 8,
        curses.COLS - 1,
        4,
        1,
    )
    win.scrollok(True)
    win.idlok(True)

    if past_text is not None:
        win.addstr(past_text)

    text = None
    box = Textbox(win, insert_mode=True)
    per_text = []

    if past_text is not None:
        per_text.append([l_ for l_ in past_text.strip()])

    per_lines = []
    cur_pos = 0

    while True:
        char = win.getch()

        if char == 27:  # esc
            break
        elif char == 17:  # ctrl + q
            per_text.append(per_lines)
            text = "".join(["".join(lines_) for lines_ in per_text])
            if text == "":
                text = past_text
            break
        elif char == 8:  # backspace
            if cur_pos > 0 and len(per_lines) > 0:
                cur_pos -= 1
                per_lines.pop()
            if cur_pos == 0 and len(per_lines) == 0:
                if len(per_text) != 0:
                    per_lines = per_text.pop()
                    cur_pos = len(per_lines) - 1
            box.do_command(char)
        elif char == ord("\n"):  # enter
            per_lines.append("\n")
            per_text.append(per_lines)
            per_lines = []
            box.do_command(char)
        elif char == 3:
            continue
        elif char == 1:
            char2 = win.getch()

            if char2 == 127 or char2 == 8:
                per_lines = []
                per_text = []
                cur_pos = 0
                win.clear()
        else:
            cur_pos += 1
            per_lines.append(chr(char))
            box.do_command(char)
    curses.echo()
    stdscr.keypad(False)
    win.scrollok(False)
    win.idlok(False)
    return text


def command_parser(_command: str, /, commands: list[str]) -> dict[str, Any] | None:
    parser = {}
    _command = _command.split()
    command_name = None
    if _command[0] not in commands:
        return None
    for com_ in _command:
        if com_ not in parser:
            if com_ in commands:
                parser[com_] = []
                command_name = com_
            else:
                if command_name is not None:
                    parser[command_name].append(com_)
    return parser if parser != {} else None


def process_command(
    stdscr: _stdscr, _commands: dict[str, str], _on_acc: Account, /
) -> int | None:
    acc_todo = [td_["todo-name"] for td_ in _on_acc.todo]
    acc_task = [ts_["task-name"] for ts_ in _on_acc.task]
    for com_, targ_ in _commands.items():
        with _on_acc as _acc:
            match com_:
                case "exit" | "quit":
                    return -1
                case "logout":
                    return None
                case "check":
                    if len(targ_) < 1:
                        return 2
                    for td_ in targ_:
                        if td_ in acc_todo:
                            _acc.check_todo(td_, True)
                        if td_.replace("-", " ") in acc_todo:
                            # poslog("has been checked")
                            # poslog(_on_acc.todo)
                            _acc.check_todo(td_.replace("-", " "), True)
                            # poslog(_on_acc.todo)
                case "uncheck":
                    if len(targ_) < 1:
                        return 2
                    for td_ in targ_:
                        if td_ in acc_todo:
                            _acc.check_todo(td_.replace("-", " "), False)
                        if td_.replace("-", " ") in acc_todo:
                            _acc.check_todo(td_.replace("-", " "), False)
                case "task":
                    if len(targ_) < 1:
                        return 2
                    for ts_ in targ_:
                        if ts_ in acc_task:
                            _acc.add_task(ts_, "")
                        if ts_.replace("-", " ") in acc_task:
                            _acc.add_task(ts_.replace("-", " "), "")
                case "todo":
                    if len(targ_) < 1:
                        return 2
                    for td_ in targ_:
                        if td_ in acc_task:
                            _acc.add_todo(td_, False)
                        if td_.replace("-", " ") in acc_task:
                            _acc.add_todo(td_.replace("-", " "), False)
                case "delete":
                    if len(targ_) < 1:
                        return 2
                    for itm_ in targ_:
                        if itm_ in acc_task:
                            _acc.delete_task(itm_)
                        if itm_.replace("-", " ") in acc_task:
                            _acc.delete_task(itm_.replace("-", " "))
                        if itm_ in acc_todo:
                            _acc.delete_todo(itm_)
                        if itm_.replace("-", " ") in acc_todo:
                            _acc.delete_todo(itm_.replace("-", " "))
                case "edit":
                    if len(targ_) < 1:
                        return 2
                    subwin_height, subwin_width = stdscr.getmaxyx()
                    subwin = curses.newwin(subwin_height, subwin_width, 0, 0)
                    for tsk_ in targ_:
                        if tsk_ in acc_task:
                            # poslog("not space")
                            subwin.touchwin()
                            stdscr.clear()
                            subwin.clear()
                            new_content = curse_editable(
                                stdscr, _acc.get_task_content(tsk_)
                            )
                            _acc.edit_task(tsk_, new_content)
                        if tsk_.replace("-", " ") in acc_task:
                            # poslog("spacing")
                            # poslog(tsk_)
                            subwin.touchwin()
                            stdscr.clear()
                            subwin.clear()
                            new_content = curse_editable(
                                stdscr,
                                _acc.get_task_content(tsk_.replace("-", " ")),
                            )
                            _acc.edit_task(tsk_.replace("-", " "), new_content)
                    del subwin
                case _:
                    return -2
    return 1
    # TODO: just implement the rest of the command


def interface_dict_item(
    stdscr: _stdscr, desc: str, items: list[dict[str, str]] = None
) -> None:
    title = "Task/ToDo Terminal"
    column_spacing = 4
    max_len_title = 10
    left_margin = 4
    coll_desc = []
    right_margin = curses.COLS - left_margin
    desc_left_margin = len(title) + left_margin + 5
    desc_field_len = right_margin - desc_left_margin
    copy_desc = desc[::]
    title_lines = 2
    # screen_lim = 10 # this variable is unused
    items_in_screen_lim = 2
    desc_len_limit = 3
    last_lines = title_lines + desc_len_limit

    if len(desc) > desc_field_len:
        stt = 0
        for idx_ in range(len(copy_desc)):
            if idx_ % desc_field_len == 0:
                coll_desc.append(desc[stt:idx_])
                stt = idx_
            elif idx_ == len(copy_desc) - 1:
                coll_desc.append(desc[stt : idx_ + 1])
    else:
        coll_desc.append(desc)
    del copy_desc

    coll_desc = [dsc_ for dsc_ in coll_desc if not dsc_.isspace()]
    coll_desc = [dsc_ for dsc_ in coll_desc if dsc_ != ""]

    if len(coll_desc) > desc_len_limit:
        raise ValueError("description is too long")

    stdscr.clear()
    stdscr.scrollok(True)
    stdscr.idlok(True)
    curses.echo()

    stdscr.addstr(title_lines, left_margin, title)

    # this is broken when you want to poslog more than one sentence the first sentence will poslog
    # ~ on 3rd line instead beside the title 2nd (fixed)
    for idx_, dp_ in enumerate(coll_desc):
        stdscr.addstr(title_lines + idx_, desc_left_margin, dp_)
    # divided into `n` parts
    if items is not None:
        items = divide_list(items, items_in_screen_lim)
        for idx_, itm_ in enumerate(items):
            for idx__, itm__ in enumerate(itm_):
                if idx_ % items_in_screen_lim == 0:
                    shortened_title = shortened_content(itm__["title"], max_len_title)
                    spaces = " " * (max_len_title - len(shortened_title) + 1)
                    max_len_content = (
                        (curses.COLS // 2 - column_spacing)
                        - (left_margin + max_len_title + 3)
                        - 2
                    )
                    stdscr.addstr(
                        last_lines + idx__,
                        left_margin,
                        f"{shortened_title}{spaces}: {shortened_content(itm__['content'], max_len_content)}",
                    )
                else:
                    shortened_title = shortened_content(itm__["title"], max_len_title)
                    spaces = " " * (max_len_title - len(shortened_title) + 1)
                    max_len_content = (
                        (curses.COLS // 2 - column_spacing)
                        - (left_margin + max_len_title + 3)
                        - 2
                    )
                    stdscr.addstr(
                        last_lines + idx__,
                        (curses.COLS // 2) - column_spacing,
                        f"{shortened_title}{spaces}: {shortened_content(itm__['content'], max_len_content)}",
                    )
    else:
        stdscr.addstr(last_lines, left_margin, "...")

    stdscr.idlok(False)
    stdscr.scrollok(False)
    stdscr.refresh()


def interface_greet(stdscr: _stdscr, /) -> int:
    title = "Task/ToDo Terminal"
    menu_list = [
        "1. Log In",
        "2. Register",
    ]
    title_x_pos = centerize(curses.COLS, len(title))
    textbx_input = None

    # stdscr.clear()
    stdscr.addstr(2, title_x_pos, title)
    curse_gen_list(stdscr, title_x_pos, 4, menu_list)
    stdscr.refresh()
    write_info_on_command_box(stdscr, f"{esc_info}, {enter_info}")
    textbx_input = curse_interactive(stdscr, limit="123")
    stdscr.refresh()
    curses.echo()
    if textbx_input == "":
        return None
    return int(textbx_input)


def interface_login(stdscr: _stdscr, /) -> Account | None:
    menu = {
        "title": "Task/ToDo Terminal",
        "cre_name": "username : ",
        "cre_pass": "password : ",
    }
    usr_name = usr_pass = ""
    user_name_pos = 4, centerize(curses.COLS, len(menu["cre_name"]) + limit_char)
    user_pass_pos = 5, centerize(curses.COLS, len(menu["cre_pass"]) + limit_char)

    stdscr.clear()
    curses.echo()
    stdscr.addstr(2, centerize(curses.COLS, len(menu["title"])), menu["title"])
    stdscr.addstr(*user_name_pos, menu["cre_name"])
    stdscr.addstr(*user_pass_pos, menu["cre_pass"])
    write_info(stdscr, "press 'esc' to quit")
    stdscr.refresh()
    usr_name = curse_input(
        stdscr,
        user_name_pos[0],
        user_name_pos[-1] + len(menu["cre_name"]),
        limit_char,
        type=GetType.Normal,
    )
    if usr_name is None:
        return None
    usr_pass = curse_input(
        stdscr,
        user_pass_pos[0],
        user_pass_pos[-1] + len(menu["cre_pass"]),
        limit_char,
        type=GetType.Password,
    )
    if usr_pass is None:
        return None

    result = Account(usr_name, usr_pass)
    if not result.is_exist():
        return None
    return result


def interface_yesno(stdscr: _stdscr, _question: str, _detail: str = None, /) -> bool:
    menu = {
        "title": "Task/ToDo Terminal",
        "question": _question + " (Y/n) : ",
    }
    _detail = _detail if _detail is not None else ""
    question_line = 4

    stdscr.clear()
    curses.echo()
    stdscr.addstr(2, centerize(curses.COLS, len(menu["title"])), menu["title"])
    if _detail is not None:
        question_line = 5
        stdscr.addstr(4, centerize(curses.COLS, len(_detail)), _detail)
    stdscr.addstr(
        question_line,
        centerize(curses.COLS, len(menu["question"]) + (limit_char // 2)),
        menu["question"],
    )  # I still don't know what is this mean I forgor
    write_info(stdscr, "press 'esc' to quit")
    stdscr.refresh()
    # code below is broken please fix it, the cursor is not in the center (fixed)
    yesno = curse_yesno(
        stdscr,
        question_line,
        centerize(curses.COLS, len(menu["question"]) + (limit_char // 2))
        + len(menu["question"]),
    )

    return yesno


def interface_register(stdscr: _stdscr, /, debug: bool = False) -> Account | None:
    menu = {
        "title": "Task/ToDo Terminal",
        "desc": "create new account",
        "cre_name": "username : ",
        "cre_pass": "password : ",
    }

    usr_name = usr_pass = ""
    user_name_pos = 6, centerize(curses.COLS, len(menu["cre_name"]) + limit_char)
    user_pass_pos = 7, centerize(curses.COLS, len(menu["cre_pass"]) + limit_char)
    result = None

    stdscr.clear()
    curses.echo()
    stdscr.addstr(2, centerize(curses.COLS, len(menu["title"])), menu["title"])
    stdscr.addstr(
        3, centerize(curses.COLS, len(menu["desc"])), menu["desc"], curses.A_UNDERLINE
    )
    stdscr.addstr(*user_name_pos, menu["cre_name"])
    stdscr.addstr(*user_pass_pos, menu["cre_pass"])
    write_info(stdscr, "press 'esc' to quit")
    stdscr.refresh()
    usr_name = curse_input(
        stdscr,
        user_name_pos[0],
        user_name_pos[-1] + len(menu["cre_name"]),
        limit_char,
        type=GetType.Normal,
    )
    if usr_name is None:
        return None
    usr_pass = curse_input(
        stdscr,
        user_pass_pos[0],
        user_pass_pos[-1] + len(menu["cre_pass"]),
        limit_char,
        type=GetType.Password,
    )
    if usr_pass is None:
        return None

    if not debug:
        with create_account(usr_name, usr_pass) as _acc:
            result = _acc
    return result


def interface_tasktodo(stdscr: _stdscr, _account: Account, /) -> None:
    commands = [
        "task",
        "todo",
        "check",
        "uncheck",
        "edit",
        "logout",
        "delete",
        "exit",
        "quit",
    ]
    command = None
    acc_itms = []
    acc_task = []
    acc_todo = []

    def recalc_itm():
        nonlocal acc_itms, acc_task, acc_todo
        acc_itms = []
        acc_task = [
            {
                "title" if nn == "task-name" else "content": nnn
                for nn, nnn in tsk.items()
            }
            for tsk in _account.task
        ]
        acc_todo = [
            {
                "title"
                if nn == "todo-name"
                else "content": nnn
                if not isinstance(nnn, bool)
                else convert_todo_check(nnn)
                for nn, nnn in tdo.items()
            }
            for tdo in _account.todo
        ]
        acc_itms.extend(acc_task)
        acc_itms.extend(acc_todo)

    desc = f"| Task: {len(_account.task)} - Todo: {len(_account.todo)}"

    while True:
        recalc_itm()
        stdscr.clear()
        stdscr.refresh()
        if 0 < len(acc_itms):
            interface_dict_item(stdscr, desc, acc_itms)
        else:
            interface_dict_item(stdscr, desc, None)

        stdscr.refresh()
        command = curse_interactive(stdscr)
        stdscr.refresh()
        # poslog(f"commands : '{command}'")
        if command == -1:
            return -1
        if command != "":
            command = command_parser(command, commands)
            # poslog(command)
            result = process_command(stdscr, command, _account)

            if result == -2:
                write_warning(stdscr, warn_no_input)
                continue
            elif result == -1:
                return -1
            elif result == 1:
                continue
            elif result == 2:
                write_warning(stdscr, "no target applied at command")
                continue
            elif result is None:
                return None
        else:
            write_warning(stdscr, warn_no_input)
            continue
    # poslog(command)


def motherterminal(stdscr: _stdscr, /) -> None:
    global Warning_Color
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    Warning_Color = curses.color_pair(1)

    terminal_run = True
    _usr = False
    cred = None
    chooser = None

    while terminal_run:
        stdscr.clear()
        curses.curs_set(False)
        stdscr.refresh()
        chooser = interface_greet(stdscr)

        curses.curs_set(True)
        match chooser:
            case 1:
                cred = interface_login(stdscr)
                if cred is None:
                    return None
                if isinstance(cred, Account):
                    if chooser == 1 and not verify_account(cred):
                        _usr = interface_yesno(
                            stdscr, "create new account ?", "you have no account"
                        )
                        if _usr:
                            chooser = 2
                else:
                    if chooser == 1 and not verify_account(**cred):
                        _usr = interface_yesno(
                            stdscr, "create new account ?", "you have no account"
                        )
                        if _usr:
                            chooser = 2
            case 2:
                cred = interface_register(stdscr, debug=debug)
                if cred is None:
                    return None
                if isinstance(cred, Account):
                    if chooser == 1 and not verify_account(cred):
                        _usr = interface_yesno(
                            stdscr, "create new account ?", "you have no account"
                        )
                        if _usr:
                            chooser = 2
                else:
                    if chooser == 1 and not verify_account(**cred):
                        _usr = interface_yesno(
                            stdscr, "create new account ?", "you have no account"
                        )
                        if _usr:
                            chooser = 2
            case -1:
                quit()
            case _:
                stdscr.clear()
                write_warning(stdscr, warn_no_input)
                continue
        edit_inter_command = interface_tasktodo(stdscr, cred)
        if edit_inter_command == -1:
            terminal_run = False
        elif edit_inter_command is None:
            continue


def run() -> None:
    os.system("cls")
    time.sleep(1)
    wrapper(motherterminal)


if __name__ == "__main__":
    wrapper(motherterminal)
