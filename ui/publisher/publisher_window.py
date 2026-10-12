import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import DARK, SECONDARY, SUCCESS

from service.inkaza_publisher_service import InkazaPublisherService
from service.property_repository_service import PropertyRepositoryService
from service.publisher_credentials_service import PublisherCredentialsService
from ui.widget.scrollable_frame import bring_to_front, center_window
from version import __version__


class PublisherWindow(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.repository = PropertyRepositoryService()
        self.credentials_service = PublisherCredentialsService(
            self.repository.database_path
        )
        self.publisher = InkazaPublisherService()
        self.title(f"INKAZA v{__version__} - Publicar Propriedade")
        self.minsize(900, 700)
        center_window(self, width=900, height=750)
        bring_to_front(self)
        self._build_ui()
        self._load_credentials()
        self._load_properties()

    def _build_ui(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Publicar Propriedade", font=("Helvetica", 22, "bold")).pack(anchor="w")

        credentials = ttk.LabelFrame(
            container, text="Acesso à INKAZA", padding=10
        )
        credentials.pack(fill="x", pady=(0, 14))
        credentials.columnconfigure(0, weight=1)
        credentials.columnconfigure(1, weight=1)
        self.login_var = tk.StringVar()
        self.password_var = tk.StringVar()
        ttk.Label(credentials, text="LOGIN").grid(row=0, column=0, sticky="w")
        ttk.Label(credentials, text="SENHA").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.login_entry = ttk.Entry(credentials, textvariable=self.login_var)
        self.login_entry.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.password_entry = ttk.Entry(
            credentials, textvariable=self.password_var, show="*"
        )
        self.password_entry.grid(
            row=1, column=1, sticky="ew", padx=(10, 0), pady=(6, 0)
        )
        self.show_password_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            credentials,
            text="Mostrar senha",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
        ).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(6, 0))

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(0, 14))
        ttk.Button(actions, text="Voltar", style=DARK, command=self._return_to_launcher).pack(side="left")
        self.publish_button = ttk.Button(
            actions,
            text="Publicar todas não sincronizadas",
            style=SUCCESS,
            command=self._start_publish_all,
        )
        self.publish_button.pack(side="left", padx=(10, 0))
        columns = ("status", "title", "category", "type", "address")
        self.tree = ttk.Treeview(container, columns=columns, show="headings")
        for name, label, width in (("status", "Status", 130), ("title", "Título", 210), ("category", "Categoria", 120), ("type", "Tipo", 90), ("address", "Endereço", 300)):
            self.tree.heading(name, text=label)
            self.tree.column(name, width=width, stretch=name in {"title", "address"})
        self.tree.pack(fill="both", expand=True)

        report_frame = ttk.LabelFrame(container, text="Resultado da publicação", padding=10)
        report_frame.pack(fill="x", pady=(14, 0))
        report_columns = ("status", "property", "stage", "message")
        self.report_tree = ttk.Treeview(
            report_frame, columns=report_columns, show="headings", height=7
        )
        self.report_tree.heading("status", text="Resultado")
        self.report_tree.heading("property", text="Propriedade")
        self.report_tree.heading("stage", text="Etapa")
        self.report_tree.heading("message", text="Mensagem")
        self.report_tree.column("status", width=110, stretch=False)
        self.report_tree.column("property", width=190, stretch=True)
        self.report_tree.column("stage", width=110, stretch=False)
        self.report_tree.column("message", width=370, stretch=True)
        self.report_tree.tag_configure("PUBLICADO", foreground="#198754")
        self.report_tree.tag_configure("ERRO", foreground="#dc3545")
        self.report_tree.pack(fill="x")

        self.status_label = ttk.Label(container, text="Pronto.", style=SECONDARY)
        self.status_label.pack(fill="x", pady=(14, 0))

    def _load_credentials(self):
        try:
            credentials = self.credentials_service.load()
            self.login_var.set(credentials.login)
            self.password_var.set(credentials.password)
        except Exception as error:
            messagebox.showwarning(
                "Credenciais da INKAZA", str(error), parent=self
            )

    def _load_properties(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.repository.list_all():
            status = {
                "NOT_SYNC": "Não sincronizado",
                "SYNC": "Sincronizado",
            }.get(row["status"], row["status"])
            self.tree.insert("", "end", iid=row["id"], values=(status, row["title"], row["category"], row["property_type"], row["address"]))

    def _start_publish_all(self):
        try:
            self.credentials_service.save(
                self.login_var.get(), self.password_var.get()
            )
            pending_rows = self.repository.list_by_status("NOT_SYNC")
            properties = [
                (row["id"], self.repository.load(row["id"]))
                for row in pending_rows
            ]
        except Exception as error:
            messagebox.showerror("Publicar propriedade", str(error), parent=self)
            return
        if not properties:
            messagebox.showinfo(
                "Publicar propriedades",
                "Não há propriedades não sincronizadas.",
                parent=self,
            )
            return
        confirmed = messagebox.askyesno(
            "Confirmar publicação",
            f"Deseja publicar {len(properties)} propriedade(s) não sincronizada(s)?",
            parent=self,
        )
        if not confirmed:
            return
        self.publish_button.configure(state="disabled")
        self._clear_report()
        credentials = (self.login_var.get().strip(), self.password_var.get())
        threading.Thread(
            target=self._run_publish_all,
            args=(properties, *credentials),
            daemon=True,
        ).start()

    def _run_publish_all(self, properties, login, password):
        try:
            results = self.publisher.publish_all(
                properties,
                notify=self._set_status,
                report=self._handle_publication_result,
                login=login,
                password=password,
            )
            published = sum(result.published for _property_id, result in results)
            failed = len(results) - published
            self.after(0, self._load_properties)
            self.after(
                0,
                lambda: messagebox.showinfo(
                    "Publicação concluída",
                    f"Publicadas: {published}\nCom erro: {failed}",
                    parent=self,
                ),
            )
        except Exception as error:
            error_message = str(error)
            self.after(0, lambda: messagebox.showerror("Falha no publicador", error_message, parent=self))
            self._set_status("Não foi possível concluir a publicação.")
        finally:
            self.after(0, lambda: self.publish_button.configure(state="normal"))

    def _toggle_password_visibility(self):
        self.password_entry.configure(
            show="" if self.show_password_var.get() else "*"
        )

    def _clear_report(self):
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)

    def _handle_publication_result(self, property_id, title, result):
        if result.published:
            self.repository.update_status(property_id, "SYNC")
        status = "PUBLICADO" if result.published else "ERRO"
        stage = "Envio" if result.submitted else "Validação/preenchimento"
        message = result.response_message or "Erro não informado."

        def render():
            self.report_tree.insert(
                "",
                "end",
                values=(status.title(), title, stage, message),
                tags=(status,),
            )
            self._load_properties()

        self.after(0, render)

    def _set_status(self, text):
        self.after(0, lambda: self.status_label.configure(text=text))

    def _return_to_launcher(self):
        if "--parent-launcher" in sys.argv:
            self.destroy()
            return
        command = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, str(Path(__file__).resolve().parents[2] / "launcher.pyw")]
        subprocess.Popen(command)
        self.destroy()


def main():
    PublisherWindow().mainloop()
