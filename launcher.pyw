import sys

from service.init_service import initialize


initialize()


if __name__ == "__main__":
    if "--admin" in sys.argv:
        from ui.admin.admin_window import main

        main()
    elif "--bot" in sys.argv:
        from ui.bot.bot_window import main

        main()
    else:
        from ui.launcher.launcher_window import main

        main()
