from ttkbootstrap.toast import ToastNotification


def toast_info(message: str, title: str = "Info", duration: int = 3000):
    ToastNotification(
        title=title,
        message=message,
        duration=duration,
        bootstyle="info",
    ).show_toast()


def toast_warning(message: str, title: str = "Atenção", duration: int = 3000):
    ToastNotification(
        title=title,
        message=message,
        duration=duration,
        bootstyle="warning",
    ).show_toast()


def toast_ok(message: str, title: str = "Sucesso", duration: int = 3000):
    ToastNotification(
        title=title,
        message=message,
        duration=duration,
        bootstyle="success",
    ).show_toast()


def toast_error(message: str, title: str = "Erro", duration: int = 3000):
    ToastNotification(
        title=title,
        message=message,
        duration=duration,
        bootstyle="danger",
    ).show_toast()
