class AdHelper:

    @staticmethod
    def to_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def collect_checked(state_map: dict) -> list[str]:
        return [label for label, var in state_map.items() if var.get()]

    @staticmethod
    def apply_checklist(state_map: dict, selected_items: list[str]):
        selected = set(selected_items or [])
        for label, var in state_map.items():
            var.set(label in selected)
