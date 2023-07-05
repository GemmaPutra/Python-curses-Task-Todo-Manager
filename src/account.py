import pathlib
import json
import traceback
from typing import Final, Self, Any
from maid import poslog

SRC: Final[pathlib.Path] = pathlib.Path(__file__).parent


class Account:
    db_path = SRC / "account_db"

    def __init__(self, _acc_name: str | pathlib.Path, _password: Any = None, /) -> Self:
        if isinstance(_acc_name, str):
            if _acc_name.strip() == "":
                raise ValueError("error: file name cannot be empty")
            self.path = self.db_path / pathlib.Path(
                str("acc_" + _acc_name)
            ).with_suffix(".json")
        else:
            self.path = _acc_name
        self.name = self.path.with_suffix("").name
        self.data = {
            "acc-name": self.name,
            "acc-pass": str(_password) if _password is not None else None,
            "acc-data": {
                "task": [],
                "todo": [],
            },
        }

        if self.path.exists():
            with self.path.open() as _acf:
                self.data = json.load(_acf)
        else:
            try:
                self.path.touch(exist_ok=False)
            except FileExistsError:
                pass

        self.task_link = self.data["acc-data"]["task"]
        self.todo_link = self.data["acc-data"]["todo"]

    def __delete_account(self) -> None:
        self.path.unlink(missing_ok=False)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, _exc_type, _exc_val, _trace) -> bool:
        self.approve()
        if _exc_type is not None:
            poslog(
                f"an exception occurred :\nexception : {_exc_type}\nvalue : {_exc_val}\ntraceback : {_trace}\n"
            )

            traceback.print_tb(_trace)
            # raise _exc_type(_exc_val)
            raise _exc_type from _exc_val
        return True

    @property
    def account_name(self) -> str:
        return self.data["acc-name"]

    @property
    def password(self) -> str | None:
        return self.data["acc-pass"]

    @property
    def content(self) -> dict[str, list[dict[str, str]]]:
        return self.data["acc-data"]

    @property
    def task(self) -> list[dict[str, str]]:
        return self.task_link

    @property
    def todo(self) -> list[dict[str, str]]:
        return self.todo_link

    @property
    def items(self) -> list[dict[str, str]]:
        itms = []
        itms.extend(self.task_link)
        itms.extend(self.todo_link)
        return itms

    def is_account(self) -> bool:
        return self.path.name.startswith("acc_")

    def is_exist(self) -> bool:
        dat = None
        with self.path.open() as _file:
            dat = _file.read()
        return dat != ""

    def approve(self) -> None:
        with self.path.open("w") as _acc:
            json.dump(self.data, _acc)

    def set_password(self, _old_password: str | None, _new_password: Any) -> None:
        if self.data["acc-pass"] is None or self.data["acc-pass"] == _old_password:
            self.data["acc-pass"] = str(_new_password)

    def add_task(self, _task_name: str, _task_content: str, /) -> None:
        task_temp = {
            "task-name": _task_name,
            "item-type": "task",
            "task-content": _task_content,
        }
        self.task.append(task_temp)

    def add_todo(self, _todo_name: str, _finished: bool, /) -> None:
        todo_temp = {
            "todo-name": _todo_name,
            "item-type": "todo",
            "finished?": _finished,
        }
        self.todo.append(todo_temp)

    def delete_task(self, _task_name: str, /) -> bool:
        for idx_, itm_ in enumerate(self.task):
            if (
                itm_.get("item-type", None) == "task"
                and itm_["task-name"] == _task_name
            ):
                self.task.pop(idx_)

    def delete_todo(self, _todo_name: str, /) -> bool:
        for idx_, itm_ in enumerate(self.todo):
            if (
                itm_.get("item-type", None) == "task"
                and itm_["task-name"] == _todo_name
            ):
                self.todo.pop(idx_)

    def rename_task(self, _old_task_name: str, _new_task_name: str, /) -> None:
        for idx_, itm_ in enumerate(self.task):
            if (
                itm_.get("item-type", None) == "task"
                and itm_["task-name"] == _old_task_name
            ):
                self.task[idx_][_new_task_name] = itm_
                del self.task[idx_][_old_task_name]

    def rename_todo(self, _old_todo_name: str, _new_todo_name: str, /) -> None:
        for idx_, itm_ in enumerate(self.todo):
            if (
                itm_.get("item-type", None) == "todo"
                and itm_["task-name"] == _old_todo_name
            ):
                self.todo[idx_][_new_todo_name] = itm_
                del self.todo[idx_][_old_todo_name]

    def get_task_content(self, _which_task: str, /) -> str:
        for idx_, itm_ in enumerate(self.task):
            if (
                itm_.get("item-type", None) == "task"
                and itm_["task-name"] == _which_task
            ):
                with self.path.open() as _f_c:
                    # return json.load(_f_c)["acc-data"]["task"]["task-content"]
                    return self.task[idx_]["task-content"]

    def edit_task(self, _which_task: str, _content: str, /) -> None:
        for idx_, itm_ in enumerate(self.task):
            if (
                itm_.get("item-type", None) == "task"
                and itm_["task-name"] == _which_task
            ):
                self.task[idx_]["task-content"] = _content

    def check_todo(self, _which_todo: str, _finished: bool, /) -> None:
        for idx_, itm_ in enumerate(self.todo):
            if (
                itm_.get("item-type", None) == "todo"
                and itm_["todo-name"] == _which_todo
            ):
                self.todo[idx_]["finished?"] = _finished

    def list_item(
        self,
    ) -> tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...],]:
        return tuple([tuple(self.task_link), tuple(self.todo_link)])

    def list_task(self) -> tuple[dict[str, str], ...]:
        return tuple(self.task_link)

    def list_todo(self) -> tuple[dict[str, str], ...]:
        return tuple(self.todo_link)


def create_account(_username: str, _password: Any = None, /) -> Account:
    acc = Account(_username, _password)
    if acc.is_exist():
        raise ValueError("error: use get_account() to get existing account")
    return acc


def get_account(_name: str) -> Account:
    acc = Account(_name)
    if not acc.is_exist():
        raise ValueError("error: use create_account() to create new account")
    return acc


def delete_account(_name: Account) -> None:
    _name._Account__delete_account()


def list_account() -> tuple[str, ...]:
    return tuple(
        file_.with_suffix("").name.replace("acc_", "")
        for file_ in Account.db_path.glob("*.json")
        if Account(file_).is_account()
    )


def list_account_path() -> tuple[pathlib.Path, ...]:
    return tuple(
        file_ for file_ in Account.db_path.glob("*.json") if Account(file_).is_account()
    )


def verify_account(_username: str | Account, _password: str = None) -> bool:
    if isinstance(_username, Account):
        return _username.is_exist()
    else:
        if _password is None:
            raise ValueError()
    if _username in list_account():
        with get_account(_username) as _acc:
            if _acc.password == _password:
                return True
    return False


if __name__ == "__main__":
    # delete_account(Account("user"))
    # print(verify_account("admin", "admin456"))
    with get_account("admin") as acc:
        acc.edit_task("task 1", "task one/1")
