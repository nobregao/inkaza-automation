from version import __version__
from pathlib import Path
import mimetypes
import re
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import unicodedata
import ttkbootstrap as ttk
from PIL import Image, ImageOps, ImageTk, UnidentifiedImageError
from ttkbootstrap.constants import DANGER, INFO, SECONDARY, SUCCESS, DARK
from service.property_repository_service import PropertyRepositoryService
from helper.ad_form_mapper import AdFormMapper
from ui.widget.scrollable_frame import (
    center_window,
    bring_to_front,
    bind_mousewheel,
)
from ui.widget.toast import toast_ok, toast_error
from ui.admin.form_state import FormState
from domain.catalog_admin import (
    CATEGORIAS_DETALHES,
    DURACOES_PRECO,
    LUGARES_PROXIMOS,
)


class AdminWindow(ttk.Window):

    ad_mapper = AdFormMapper()

    def __init__(self):
        super().__init__(themename="flatly")
        self.property_repository = PropertyRepositoryService()
        self.current_property_id = None
        self._configure_window()
        self.container = None
        self.show_property_list()

    def _configure_window(self):
        self.title(f"INKAZA v{__version__} - Propriedades")
        self.minsize(900, 750)
        center_window(self, width=900, height=750)
        bring_to_front(self)

    def _clear_screen(self):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        if self.container is not None and self.container.winfo_exists():
            self.container.destroy()

    def show_property_list(self):
        self._clear_screen()
        self.current_property_id = None
        self.container = ttk.Frame(self, padding=20)
        self.container.pack(fill="both", expand=True)

        header = ttk.Frame(self.container)
        header.pack(fill="x", pady=(0, 18))
        ttk.Label(
            header,
            text="Propriedades",
            font=("Helvetica", 22, "bold"),
        ).pack(anchor="w", pady=(0, 14))

        actions = ttk.Frame(header)
        actions.pack(fill="x")
        ttk.Button(
            actions,
            text="Voltar",
            style=DARK,
            command=self.return_to_launcher,
        ).pack(side="left")
        ttk.Button(
            actions,
            text="Nova Propriedade",
            style=INFO,
            command=self.show_new_property_form,
        ).pack(side="left", padx=(10, 0))

        columns = (
            "status",
            "title",
            "category",
            "type",
            "address",
            "updated_at",
        )
        self.properties_tree = ttk.Treeview(
            self.container, columns=columns, show="headings"
        )
        headings = {
            "title": "Título",
            "category": "Categoria",
            "type": "Tipo",
            "address": "Endereço",
            "status": "Status",
            "updated_at": "Atualizada em",
        }
        widths = {
            "title": 190,
            "category": 110,
            "type": 90,
            "address": 260,
            "status": 125,
            "updated_at": 145,
        }
        for column in columns:
            self.properties_tree.heading(column, text=headings[column])
            self.properties_tree.column(
                column,
                width=widths[column],
                anchor="center"
                if column in {"type", "status", "updated_at"}
                else "w",
                stretch=column in {"title", "address"},
            )

        self.properties_tree.tag_configure("not_sync", foreground="#6c757d")

        self.properties_tree.pack(fill="both", expand=True)
        self.properties_tree.bind(
            "<Double-1>", lambda _event: self.open_selected_property()
        )

        for property_data in self.property_repository.list_all():
            self.properties_tree.insert(
                "",
                "end",
                iid=str(property_data["id"]),
                values=(
                    self._status_label(property_data["status"]),
                    property_data["title"],
                    property_data["category"],
                    property_data["property_type"],
                    property_data["address"],
                    property_data["updated_at"],
                ),
                tags=("not_sync",) if property_data["status"] == "NOT_SYNC" else (),
            )

        footer = ttk.Frame(self.container)
        footer.pack(fill="x", pady=(14, 0))
        ttk.Button(
            footer,
            text="Abrir selecionada",
            style=INFO,
            command=self.open_selected_property,
        ).pack(side="right")

        if not self.properties_tree.get_children():
            ttk.Label(
                self.container,
                text="Nenhuma propriedade cadastrada. Clique em Nova Propriedade.",
                style=SECONDARY,
            ).place(relx=0.5, rely=0.5, anchor="center")

    def return_to_launcher(self):
        if getattr(sys, "frozen", False):
            command = [sys.executable]
        else:
            launcher_path = Path(__file__).resolve().parents[2] / "launcher.pyw"
            command = [sys.executable, str(launcher_path)]

        subprocess.Popen(command)
        self.destroy()

    def show_new_property_form(self):
        self._show_property_form()

    @staticmethod
    def _status_label(status: str) -> str:
        return {"NOT_SYNC": "Não sincronizado"}.get(status, status)

    def _show_property_form(self, property_id: str | None = None):
        self._clear_screen()
        self.state = FormState(self)
        self._build_layout()
        self._build_sections()
        self.reset_form()
        if property_id is not None:
            self._load_property(property_id)

    def _build_layout(self):
        # build container
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        # build toolbar
        self.top = ttk.Frame(self.container)
        self.top.pack(fill="x")
        self.top.columnconfigure(3, weight=1)

        ttk.Button(
            self.top,
            text="Voltar",
            style=DARK,
            command=self.show_property_list,
        ).grid(row=0, column=0, padx=(16, 8), pady=(14, 8))

        ttk.Button(
            self.top,
            text="Nova Propriedade",
            style=INFO,
            command=self.show_new_property_form,
        ).grid(row=0, column=1, padx=(8, 8), pady=(14, 8))

        ttk.Button(
            self.top,
            text="Salvar Propriedade",
            style=SUCCESS,
            command=self.save_property,
        ).grid(row=0, column=2, padx=8, pady=(14, 8))

        self.btn_delete_property = ttk.Button(
            self.top,
            text="Excluir Propriedade",
            style=DANGER,
            command=self.delete_property,
        )
        self.btn_delete_property.grid(
            row=0, column=4, sticky="e", padx=(8, 16), pady=(14, 8)
        )
        self.btn_delete_property.grid_remove()

        ttk.Separator(self.container, orient="horizontal").pack(fill="x")

        # build scrollable area
        self.canvas = tk.Canvas(self.container, highlightthickness=0)
        self.v_scroll = ttk.Scrollbar(
            self.container, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.v_scroll.set)
        bind_mousewheel(self.canvas, self)

        self.v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.columnconfigure(0, weight=1)

        self._canvas_window_id = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self._canvas_window_id, width=e.width),
        )
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

    def _create_section(self, row: int, title: str) -> ttk.Frame:
        section = ttk.Frame(self.scrollable_frame, padding=16)
        section.grid(row=row, column=0, sticky="nsew", padx=16, pady=(8, 16))
        section.columnconfigure(0, weight=1)

        ttk.Label(
            section,
            text=title,
            style=SECONDARY,
            font=("Helvetica", 18, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        return section

    def _build_sections(self):
        self._build_section_detalhes(row=0)
        self._build_section_seo(row=1)
        self._build_section_perto_lugares(row=2)
        self._build_section_localizacao_inkaza(row=3)
        self._build_section_imagens(row=4)
        self._build_section_traducoes(row=5)

    def _build_section_detalhes(self, row: int):
        section = self._create_section(row, "Detalhes")

        ttk.Label(section, text="CATEGORIA*").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            section,
            textvariable=self.state.detalhes_categoria,
            values=CATEGORIAS_DETALHES,
            state="readonly",
        ).grid(row=2, column=0, sticky="ew", pady=(6, 12))

        ttk.Label(section, text="TÍTULO*").grid(row=3, column=0, sticky="w")
        ttk.Entry(section, textvariable=self.state.detalhes_titulo).grid(
            row=4, column=0, sticky="ew", pady=(6, 12)
        )
        self.state.detalhes_titulo.trace_add("write", self._sync_detalhes_slug)

        ttk.Label(section, text="LESMA").grid(row=5, column=0, sticky="w")
        slug_entry = ttk.Entry(section, textvariable=self.state.detalhes_slug)
        slug_entry.grid(row=6, column=0, sticky="ew", pady=(6, 2))
        slug_entry.configure(
            validate="key",
            validatecommand=(self.register(self._validate_slug), "%P"),
        )
        ttk.Label(
            section,
            text="Somente letras sem acento, números e hífens são permitidos",
            bootstyle="danger",
        ).grid(row=7, column=0, sticky="w", pady=(0, 12))

        ttk.Label(section, text="DESCRIÇÃO*").grid(row=8, column=0, sticky="w")
        self.state.detalhes_descricao = tk.Text(section, height=7, wrap="word")
        self.state.detalhes_descricao.grid(
            row=9, column=0, sticky="ew", pady=(6, 16)
        )

        ttk.Label(section, text="TIPO DE PROPRIEDADE*").grid(
            row=10, column=0, sticky="w", pady=(0, 6)
        )
        type_box = ttk.Frame(section)
        type_box.grid(row=11, column=0, sticky="w", pady=(0, 14))
        ttk.Radiobutton(
            type_box,
            text="Para vender",
            variable=self.state.detalhes_tipo,
            value="venda",
        ).pack(anchor="w")
        ttk.Radiobutton(
            type_box,
            text="Para alugar",
            variable=self.state.detalhes_tipo,
            value="aluguel",
        ).pack(anchor="w")

        self.detalhes_duracao_box = ttk.Frame(section)
        self.detalhes_duracao_box.columnconfigure(0, weight=1)
        ttk.Label(self.detalhes_duracao_box, text="DURAÇÃO POR PREÇO*").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Combobox(
            self.detalhes_duracao_box,
            textvariable=self.state.detalhes_duracao_preco,
            values=DURACOES_PRECO,
            state="readonly",
        ).grid(row=1, column=0, sticky="ew", pady=(6, 12))

        ttk.Label(section, text="PREÇO (R$)*").grid(row=14, column=0, sticky="w")
        price_entry = ttk.Entry(section, textvariable=self.state.detalhes_preco)
        price_entry.grid(row=15, column=0, sticky="ew", pady=(6, 0))
        price_entry.configure(
            validate="key",
            validatecommand=(self.register(self._validate_numeric), "%P"),
        )

        self.state.detalhes_tipo.trace_add("write", self._toggle_detalhes_duracao)
        self._toggle_detalhes_duracao()

    @staticmethod
    def _validate_slug(value: str) -> bool:
        return all(char.isascii() and (char.isalnum() or char == "-") for char in value)

    def _toggle_detalhes_duracao(self, *_):
        if self.state.detalhes_tipo.get() == "aluguel":
            if not self.state.detalhes_duracao_preco.get():
                self.state.detalhes_duracao_preco.set("Mensal")
            self.detalhes_duracao_box.grid(
                row=12, column=0, sticky="ew", pady=(0, 2)
            )
        else:
            self.detalhes_duracao_box.grid_remove()

    def _sync_detalhes_slug(self, *_):
        title = self.state.detalhes_titulo.get().lower().strip()
        normalized = unicodedata.normalize("NFKD", title)
        without_accents = "".join(
            char for char in normalized if not unicodedata.combining(char)
        )
        slug = re.sub(r"[^a-z0-9]+", "-", without_accents).strip("-")
        self.state.detalhes_slug.set(slug)

    def _build_section_seo(self, row: int):
        section = self._create_section(row, "Detalhes de SEO")

        ttk.Label(section, text="TÍTULO").grid(row=1, column=0, sticky="w")
        self.state.seo_titulo = tk.Text(section, height=3, wrap="word")
        self.state.seo_titulo.grid(row=2, column=0, sticky="ew", pady=(6, 2))
        self.lbl_seo_titulo = ttk.Label(
            section,
            text="Recomendado: 55–60 caracteres. Tamanho máximo: 255 caracteres",
            style=SECONDARY,
        )
        self.lbl_seo_titulo.grid(row=3, column=0, sticky="w", pady=(0, 14))

        ttk.Label(section, text="IMAGEM").grid(row=4, column=0, sticky="w")
        ttk.Button(
            section,
            text="Selecione uma imagem",
            command=self._select_seo_image,
            bootstyle="secondary-outline",
        ).grid(row=5, column=0, sticky="ew", pady=(6, 4), ipady=14)
        self.lbl_seo_imagem = ttk.Label(section, style=SECONDARY)
        self.lbl_seo_imagem.grid(row=6, column=0, sticky="w")
        self.seo_image_preview_box = ttk.Frame(section)
        self.seo_image_preview_box.grid(row=7, column=0, sticky="w", pady=(8, 2))
        self.seo_image_preview = ttk.Label(
            self.seo_image_preview_box, anchor="center"
        )
        self.seo_image_preview.grid(row=0, column=0)
        self.btn_remove_seo_image = ttk.Button(
            self.seo_image_preview_box,
            text="✕",
            command=lambda: self.state.seo_imagem.set(""),
            bootstyle="danger",
            width=3,
        )
        self.btn_remove_seo_image.grid(row=0, column=1, sticky="ne", padx=(6, 0))
        self.seo_image_preview_reference = None
        ttk.Label(
            section,
            text="Permitido: qualquer formato de imagem. Tamanho máximo: 5 MB",
            style=SECONDARY,
        ).grid(row=8, column=0, sticky="w", pady=(2, 14))

        ttk.Label(section, text="DESCRIÇÃO").grid(row=9, column=0, sticky="w")
        self.state.seo_descricao = tk.Text(section, height=4, wrap="word")
        self.state.seo_descricao.grid(row=10, column=0, sticky="ew", pady=(6, 2))
        self.lbl_seo_descricao = ttk.Label(
            section,
            text="Recomendado: 155–160 caracteres. Tamanho máximo: 255 caracteres",
            style=SECONDARY,
        )
        self.lbl_seo_descricao.grid(row=11, column=0, sticky="w", pady=(0, 14))

        ttk.Label(section, text="PALAVRAS-CHAVE (Separe por vírgulas)").grid(row=12, column=0, sticky="w")
        self.state.seo_palavras_chave = tk.Text(section, height=4, wrap="word")
        self.state.seo_palavras_chave.grid(
            row=13, column=0, sticky="ew", pady=(6, 2)
        )
        self.lbl_seo_palavras = ttk.Label(
            section,
            text="Tamanho máximo: 255 caracteres",
            style=SECONDARY,
        )
        self.lbl_seo_palavras.grid(row=14, column=0, sticky="w")

        for widget, label, recommendation in (
            (self.state.seo_titulo, self.lbl_seo_titulo, "Recomendado: 55–60"),
            (
                self.state.seo_descricao,
                self.lbl_seo_descricao,
                "Recomendado: 155–160",
            ),
            (self.state.seo_palavras_chave, self.lbl_seo_palavras, ""),
        ):
            widget.bind(
                "<KeyRelease>",
                lambda _event, w=widget, lbl=label, rec=recommendation: self._limit_seo_text(
                    w, lbl, rec
                ),
            )

        self.state.seo_imagem.trace_add("write", self._update_seo_image_label)
        self._update_seo_image_label()

    def _select_seo_image(self):
        path = filedialog.askopenfilename(
            title="Selecionar imagem de SEO",
            filetypes=[
                (
                    "Imagens",
                    (
                        "*.jpg",
                        "*.jpeg",
                        "*.png",
                        "*.webp",
                        "*.gif",
                        "*.bmp",
                        "*.tif",
                        "*.tiff",
                        "*.svg",
                        "*.heic",
                        "*.heif",
                    ),
                ),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not path:
            return

        image_path = Path(path)
        mime_type = mimetypes.guess_type(image_path.name)[0] or ""
        if not mime_type.startswith("image/"):
            toast_error("Formato inválido. Selecione um arquivo de imagem")
            return
        if image_path.stat().st_size > 5 * 1024 * 1024:
            toast_error("A imagem deve ter no máximo 5 MB")
            return

        self.state.seo_imagem.set(str(image_path))

    def _update_seo_image_label(self, *_):
        path = self.state.seo_imagem.get().strip()
        self.lbl_seo_imagem.configure(
            text=f"Imagem selecionada: {Path(path).name}" if path else "Nenhuma imagem selecionada"
        )
        self.seo_image_preview.configure(image="", text="")
        self.seo_image_preview_reference = None
        if not path:
            self.btn_remove_seo_image.grid_remove()
            return
        self.btn_remove_seo_image.grid()

        try:
            with Image.open(path) as source_image:
                image = ImageOps.exif_transpose(source_image).copy()
            image.thumbnail((320, 180))
            preview = ImageTk.PhotoImage(image)
            self.seo_image_preview_reference = preview
            self.seo_image_preview.configure(image=preview)
        except (OSError, UnidentifiedImageError):
            self.seo_image_preview.configure(text="Pré-visualização indisponível")

    @staticmethod
    def _limit_seo_text(widget, label, recommendation: str):
        value = widget.get("1.0", "end-1c")
        if len(value) > 255:
            widget.delete("1.0", "end")
            widget.insert("1.0", value[:255])
            value = value[:255]

        prefix = f"{recommendation} caracteres. " if recommendation else ""
        label.configure(
            text=f"{prefix}Tamanho máximo: 255 caracteres — {255 - len(value)} restantes"
        )

    def _build_section_perto_lugares(self, row: int):
        section = self._create_section(row, "Perto de lugares")
        grid = ttk.Frame(section)
        grid.grid(row=1, column=0, sticky="ew")
        for column in range(4):
            grid.columnconfigure(column, weight=1, uniform="lugares")

        self.perto_lugares_entries = {}
        self.perto_lugares_labels = {}
        for index, lugar in enumerate(LUGARES_PROXIMOS):
            item_row, item_column = divmod(index, 4)
            item = ttk.Frame(grid)
            item.grid(
                row=item_row,
                column=item_column,
                sticky="new",
                padx=(0 if item_column == 0 else 10, 0),
                pady=(0, 12),
            )
            item.columnconfigure(0, weight=1)

            fields = self.state.perto_lugares[lugar]
            ttk.Checkbutton(
                item,
                text=lugar,
                variable=fields["selecionado"],
            ).grid(row=0, column=0, sticky="w")

            entry = ttk.Entry(
                item,
                textvariable=fields["distancia_km"],
                validate="key",
                validatecommand=(self.register(self._validate_numeric), "%P"),
            )
            distance_label = ttk.Label(
                item,
                text="Distância (km)",
                style=SECONDARY,
            )
            self.perto_lugares_entries[lugar] = entry
            self.perto_lugares_labels[lugar] = distance_label
            fields["selecionado"].trace_add(
                "write",
                lambda *_args, place=lugar: self._toggle_lugar_distance(place),
            )
            self._toggle_lugar_distance(lugar)

    def _toggle_lugar_distance(self, lugar: str):
        entry = self.perto_lugares_entries[lugar]
        label = self.perto_lugares_labels[lugar]
        if self.state.perto_lugares[lugar]["selecionado"].get():
            entry.grid(row=1, column=0, sticky="ew", pady=(6, 0))
            label.grid(row=2, column=0, sticky="w", pady=(2, 0))
        else:
            entry.grid_remove()
            label.grid_remove()

    def _build_section_localizacao_inkaza(self, row: int):
        section = self._create_section(row, "Localização")

        ttk.Label(section, text="CIDADE*").grid(row=1, column=0, sticky="w")
        ttk.Entry(
            section,
            textvariable=self.state.localizacao_cidade,
            state="disabled",
        ).grid(
            row=2, column=0, sticky="ew", pady=(6, 12)
        )

        country_state = ttk.Frame(section)
        country_state.grid(row=3, column=0, sticky="ew")
        country_state.columnconfigure(0, weight=1, uniform="localizacao")
        country_state.columnconfigure(1, weight=1, uniform="localizacao")

        country_box = ttk.Frame(country_state)
        country_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        country_box.columnconfigure(0, weight=1)
        ttk.Label(country_box, text="PAÍS*").grid(row=0, column=0, sticky="w")
        ttk.Entry(
            country_box,
            textvariable=self.state.localizacao_pais,
            state="disabled",
        ).grid(
            row=1, column=0, sticky="ew", pady=(6, 12)
        )

        state_box = ttk.Frame(country_state)
        state_box.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        state_box.columnconfigure(0, weight=1)
        ttk.Label(state_box, text="ESTADO*").grid(row=0, column=0, sticky="w")
        ttk.Entry(
            state_box,
            textvariable=self.state.localizacao_estado,
            state="disabled",
        ).grid(
            row=1, column=0, sticky="ew", pady=(6, 12)
        )

        ttk.Label(section, text="ENDEREÇO DO CLIENTE*").grid(
            row=4, column=0, sticky="w"
        )
        self.state.localizacao_endereco_cliente = tk.Text(
            section, height=4, wrap="word"
        )
        self.state.localizacao_endereco_cliente.grid(
            row=5, column=0, sticky="ew", pady=(6, 12)
        )

        ttk.Label(section, text="ENDEREÇO*").grid(row=6, column=0, sticky="w")
        self.state.localizacao_endereco = tk.Text(section, height=4, wrap="word")
        self.state.localizacao_endereco.grid(
            row=7, column=0, sticky="ew", pady=(6, 0)
        )

    def _build_section_imagens(self, row: int):
        section = self._create_section(row, "Imagens")
        upload_grid = ttk.Frame(section)
        upload_grid.grid(row=1, column=0, sticky="ew")
        for column in range(4):
            upload_grid.columnconfigure(column, weight=1, uniform="imagens")

        upload_fields = (
            ("Imagem do título *", "titulo"),
            ("Imagem 3D", "3d"),
            ("Imagens da galeria", "galeria"),
            ("Documentos", "documentos"),
        )
        self.imagens_labels = {}
        self.imagens_preview_boxes = {}
        for column, (label, kind) in enumerate(upload_fields):
            box = ttk.Frame(upload_grid, padding=10, borderwidth=1, relief="solid")
            box.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 10, 0),
            )
            box.columnconfigure(0, weight=1)
            ttk.Label(box, text=label).grid(row=0, column=0, sticky="w")
            ttk.Button(
                box,
                text="Selecione seus arquivos\nou navegue",
                command=lambda file_kind=kind: self._select_image_section_files(
                    file_kind
                ),
                bootstyle="secondary-outline",
            ).grid(row=1, column=0, sticky="ew", pady=(6, 4), ipady=10)
            selected_label = ttk.Label(box, style=SECONDARY, wraplength=190)
            selected_label.grid(row=2, column=0, sticky="w")
            self.imagens_labels[kind] = selected_label
            preview_box = ttk.Frame(box)
            preview_box.grid(row=3, column=0, sticky="ew", pady=(10, 0))
            preview_box.columnconfigure(0, weight=1)
            self.imagens_preview_boxes[kind] = preview_box
        self.image_preview_references = []

        ttk.Label(section, text="LINK DO VÍDEO").grid(
            row=2, column=0, sticky="w", pady=(18, 0)
        )
        ttk.Entry(section, textvariable=self.state.link_video).grid(
            row=3, column=0, sticky="ew", pady=(6, 0)
        )
        self._update_images_labels()

    def _select_image_section_files(self, kind: str):
        image_types = [("Imagens", ("*.jpg", "*.jpeg", "*.png", "*.webp"))]

        if kind in {"titulo", "3d"}:
            filetypes = image_types
            if kind == "3d":
                filetypes = [
                    (
                        "Imagens",
                        (
                            "*.jpg",
                            "*.jpeg",
                            "*.png",
                            "*.webp",
                            "*.gif",
                            "*.bmp",
                            "*.tif",
                            "*.tiff",
                        ),
                    ),
                    ("Todos os arquivos", "*.*"),
                ]
            path = filedialog.askopenfilename(
                title="Selecionar imagem",
                filetypes=filetypes,
            )
            if not path:
                return
            if not self._validate_media_selection(kind, [path]):
                return
            target = self.state.imagem_titulo if kind == "titulo" else self.state.imagem_3d
            target.set(path)
        elif kind == "galeria":
            paths = filedialog.askopenfilenames(
                title="Selecionar imagens da galeria",
                filetypes=image_types,
            )
            if not paths:
                return
            if not self._validate_media_selection(kind, paths):
                return
            self.state.imagens_galeria = list(paths)
        else:
            paths = filedialog.askopenfilenames(
                title="Selecionar documentos",
                filetypes=[
                    ("Documentos", ("*.pdf", "*.doc", "*.docx")),
                ],
            )
            if not paths:
                return
            if not self._validate_media_selection(kind, paths):
                return
            self.state.documentos = list(paths)

        self._update_images_labels()

    def _update_images_labels(self):
        title_path = self.state.imagem_titulo.get().strip()
        image_3d_path = self.state.imagem_3d.get().strip()
        self.imagens_labels["titulo"].configure(
            text=Path(title_path).name if title_path else "Nenhum arquivo selecionado"
        )
        self.imagens_labels["3d"].configure(
            text=Path(image_3d_path).name
            if image_3d_path
            else "Nenhum arquivo selecionado"
        )
        self.imagens_labels["galeria"].configure(
            text=f"{len(self.state.imagens_galeria)} arquivo(s) selecionado(s)"
        )
        self.imagens_labels["documentos"].configure(
            text=f"{len(self.state.documentos)} arquivo(s) selecionado(s)"
        )
        self._render_image_previews()

    @staticmethod
    def _validate_media_selection(kind: str, paths) -> bool:
        allowed_images = {"image/jpg", "image/jpeg", "image/png", "image/webp"}
        allowed_documents = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        for raw_path in paths:
            mime_type = mimetypes.guess_type(raw_path)[0] or ""
            if kind == "3d":
                valid = mime_type.startswith("image/")
            elif kind == "documentos":
                valid = mime_type in allowed_documents
            else:
                valid = mime_type in allowed_images
            if not valid:
                toast_error(f"Formato não permitido: {Path(raw_path).name}")
                return False
        return True

    def _render_image_previews(self):
        for preview_box in self.imagens_preview_boxes.values():
            for widget in preview_box.winfo_children():
                widget.destroy()
        self.image_preview_references.clear()

        previews = []
        if self.state.imagem_titulo.get().strip():
            previews.append(
                ("titulo", self.state.imagem_titulo.get(), None)
            )
        if self.state.imagem_3d.get().strip():
            previews.append(("3d", self.state.imagem_3d.get(), None))
        previews.extend(
            ("galeria", path, gallery_index)
            for gallery_index, path in enumerate(self.state.imagens_galeria)
        )

        for kind, raw_path, item_index in previews:
            card = ttk.Frame(self.imagens_preview_boxes[kind], padding=(0, 6))
            card.pack(fill="x")
            ttk.Button(
                card,
                text="✕",
                command=lambda media_kind=kind, media_index=item_index: self._remove_media_item(
                    media_kind, media_index
                ),
                bootstyle="danger",
                width=3,
            ).pack(anchor="e", pady=(0, 4))
            try:
                with Image.open(raw_path) as source_image:
                    image = ImageOps.exif_transpose(source_image).copy()
                image.thumbnail((170, 110))
                preview = ImageTk.PhotoImage(image)
                self.image_preview_references.append(preview)
                ttk.Label(card, image=preview, anchor="center").pack(fill="x")
            except (OSError, UnidentifiedImageError):
                ttk.Label(card, text="Pré-visualização indisponível").pack(fill="x")

            ttk.Label(
                card,
                text=Path(raw_path).name,
                style=SECONDARY,
                anchor="center",
                wraplength=170,
            ).pack(fill="x")

        if self.state.documentos:
            documents = self.imagens_preview_boxes["documentos"]
            for document_index, path in enumerate(self.state.documentos):
                document_row = ttk.Frame(documents)
                document_row.pack(fill="x", pady=2)
                ttk.Label(
                    document_row,
                    text=f"• {Path(path).name}",
                    style=SECONDARY,
                ).pack(side="left", fill="x", expand=True)
                ttk.Button(
                    document_row,
                    text="✕",
                    command=lambda media_index=document_index: self._remove_media_item(
                        "documentos", media_index
                    ),
                    bootstyle="danger",
                    width=3,
                ).pack(side="right")

    def _remove_media_item(self, kind: str, item_index: int | None = None):
        if kind == "titulo":
            self.state.imagem_titulo.set("")
        elif kind == "3d":
            self.state.imagem_3d.set("")
        elif kind == "galeria" and item_index is not None:
            self.state.imagens_galeria.pop(item_index)
        elif kind == "documentos" and item_index is not None:
            self.state.documentos.pop(item_index)
        self._update_images_labels()

    def _build_section_traducoes(self, row: int):
        section = self._create_section(row, "Propriedade")

        portuguese_box = ttk.Frame(section)
        portuguese_box.grid(row=1, column=0, sticky="ew")
        portuguese_box.columnconfigure(0, weight=1)

        ttk.Label(portuguese_box, text="TÍTULO").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Entry(
            portuguese_box,
            textvariable=self.state.traducao_portugues_titulo,
        ).grid(row=2, column=0, sticky="ew", pady=(6, 14))

        ttk.Label(portuguese_box, text="DESCRIÇÃO").grid(
            row=3, column=0, sticky="w"
        )
        self.state.traducao_portugues_descricao = tk.Text(
            portuguese_box,
            height=6,
            wrap="word",
        )
        self.state.traducao_portugues_descricao.grid(
            row=4, column=0, sticky="ew", pady=(6, 0)
        )


    def _validate_numeric(self, value: str) -> bool:
        return value == "" or value.isdigit()



    def _scroll_to_top(self):
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(0)

    # ---------- AD DATA ----------
    def _set_current_property(self, property_id: str | None, title: str = ""):
        self.current_property_id = property_id
        if property_id is None:
            self.btn_delete_property.grid_remove()
            return
        self.btn_delete_property.grid()

    def _build_default_payload(self):
        return {
            "detalhes": {
                "categoria": "",
                "titulo": "",
                "slug": "",
                "descricao": "",
                "tipo": "venda",
                "duracao_preco": "",
                "preco": "",
            },
            "seo": {
                "titulo": "",
                "imagem": "",
                "descricao": "",
                "palavras_chave": "",
            },
            "perto_de_lugares": {
                lugar: {"selecionado": False, "distancia_km": ""}
                for lugar in LUGARES_PROXIMOS
            },
            "imagens": {
                "imagem_titulo": "",
                "imagem_3d": "",
                "galeria": [],
                "documentos": [],
                "link_video": "",
            },
            "traducoes": {
                "portugues": {
                    "titulo": "",
                    "descricao": "",
                }
            },
            "anuncio": {
                "repeticoes": 3,
                "ciclos": 1,
                "codigo": "",
                "titulo": "",
                "descricao": "",
            },
            "imovel": {
                "finalidade": "residencial",
                "tipo": "Apartamento",
                "categoria": "Padrão",
                "quartos": 0,
                "suites": 0,
                "banheiros": 0,
                "vagas": 0,
                "area_util_m2": 0,
                "area_total_m2": 0,
                "andar": 0,
            },
            "localizacao": {
                "cidade": "Fortaleza",
                "pais": "Brasil",
                "estado": "Ceará",
                "endereco_cliente": "",
                "endereco": "",
            },
            "caracteristicas": {
                "diferenciais": [],
                "outras": "",
            },
            "condominio": {
                "andares": 0,
                "unidades_por_andar": 0,
                "torres": 0,
                "ano_construcao": "",
            },
            "negociacao": {
                "tipo": "venda",
                "valor_venda": 0,
                "valor_aluguel": 0,
                "pagamento_aluguel": "Mensal",
                "condominio_isento": False,
                "valor_condominio": "",
                "iptu_isento": False,
                "valor_iptu": "",
                "periodo_iptu": "Anual",
                "modalidade_aluguel": [],
            },
        }

    def reset_form(self):
        self._set_current_property(None)
        self._scroll_to_top()
        self.ad_mapper.apply_to_state(self.state, self._build_default_payload())
        self._refresh_form_ui()

    def open_selected_property(self):
        selection = self.properties_tree.selection()
        if not selection:
            toast_error("Selecione uma propriedade")
            return
        self._show_property_form(selection[0])

    def _load_property(self, property_id: str):
        try:
            data = self.property_repository.load(property_id)
            self.ad_mapper.apply_to_state(self.state, data)
            self._refresh_form_ui()
            title = data.get("detalhes", {}).get("titulo", "")
            self._set_current_property(property_id, title)
        except Exception as error:
            print(error)
            toast_error("Erro ao carregar a propriedade")
            self.show_property_list()

    def save_property(self):
        try:
            data = self.ad_mapper.to_dict(self.state)
            if not data.get("imagens", {}).get("imagem_titulo"):
                toast_error("Selecione a imagem do título")
                return
            property_id = self.property_repository.save(
                data, self.current_property_id
            )
            title = data.get("detalhes", {}).get("titulo", "")
            self._set_current_property(property_id, title)
            self._scroll_to_top()
            toast_ok("Propriedade salva com sucesso")
        except Exception as error:
            print(error)
            toast_error("Erro ao salvar propriedade")

    def delete_property(self):
        if self.current_property_id is None:
            return

        confirmed = messagebox.askyesno(
            "Excluir Propriedade",
            "Tem certeza de que deseja excluir esta propriedade? "
            "Esta ação não poderá ser desfeita.",
            parent=self,
        )
        if not confirmed:
            return

        try:
            self.property_repository.delete(self.current_property_id)
            toast_ok("Propriedade excluída com sucesso")
            self.show_property_list()
        except Exception as error:
            print(error)
            toast_error("Erro ao excluir propriedade")


    def _refresh_form_ui(self):
        self._update_images_labels()
        self._limit_seo_text(
            self.state.seo_titulo, self.lbl_seo_titulo, "Recomendado: 55–60"
        )
        self._limit_seo_text(
            self.state.seo_descricao,
            self.lbl_seo_descricao,
            "Recomendado: 155–160",
        )
        self._limit_seo_text(
            self.state.seo_palavras_chave, self.lbl_seo_palavras, ""
        )


def main():
    app = AdminWindow()
    app.mainloop()
