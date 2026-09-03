def center_window(win, width=800, height=500):
    win.update_idletasks()

    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()

    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)

    win.geometry(f"{width}x{height}+{x}+{y}")


def bring_to_front(win, delay_ms=300):
    win.lift()
    win.attributes("-topmost", True)
    win.after(delay_ms, lambda: win.attributes("-topmost", False))
    win.focus_force()


def bind_mousewheel(canvas, root):
    def _on_mousewheel(event):
        # Windows / macOS
        if event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # Linux
        elif event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

    # Windows / macOS
    root.bind_all("<MouseWheel>", _on_mousewheel)
    # Linux
    root.bind_all("<Button-4>", _on_mousewheel)
    root.bind_all("<Button-5>", _on_mousewheel)
