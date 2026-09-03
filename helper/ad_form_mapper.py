from domain.catalog_admin import TIPOS_IMOVEL_COMERCIAL, TIPOS_IMOVEL_RESIDENCIAL
from helper.ad_helper import AdHelper
from ui.admin.form_state import FormState


class AdFormMapper:

    @staticmethod
    def to_dict(state: FormState) -> dict:
        return {
            "detalhes": AdFormMapper._collect_detalhes(state),
            "seo": AdFormMapper._collect_seo(state),
            "perto_de_lugares": AdFormMapper._collect_perto_de_lugares(state),
            "localizacao": AdFormMapper._collect_localizacao(state),
            "imagens": AdFormMapper._collect_imagens(state),
            "traducoes": AdFormMapper._collect_traducoes(state),
            "anuncio": AdFormMapper._collect_anuncio(state),
            "imovel": AdFormMapper._collect_imovel(state),
            "condominio": AdFormMapper._collect_condominio(state),
            "negociacao": AdFormMapper._collect_negociacao(state),
        }

    @staticmethod
    def _collect_traducoes(state: FormState) -> dict:
        return {
            "portugues": {
                "titulo": state.traducao_portugues_titulo.get().strip(),
                "descricao": state.traducao_portugues_descricao.get(
                    "1.0", "end-1c"
                ).strip(),
            }
        }

    @staticmethod
    def _collect_localizacao(state: FormState) -> dict:
        return {
            "cidade": state.localizacao_cidade.get().strip(),
            "pais": state.localizacao_pais.get().strip(),
            "estado": state.localizacao_estado.get().strip(),
            "endereco_cliente": state.localizacao_endereco_cliente.get(
                "1.0", "end-1c"
            ).strip(),
            "endereco": state.localizacao_endereco.get("1.0", "end-1c").strip(),
        }

    @staticmethod
    def _collect_imagens(state: FormState) -> dict:
        return {
            "imagem_titulo": state.imagem_titulo.get().strip(),
            "imagem_3d": state.imagem_3d.get().strip(),
            "galeria": list(state.imagens_galeria),
            "documentos": list(state.documentos),
            "link_video": state.link_video.get().strip(),
        }

    @staticmethod
    def _collect_perto_de_lugares(state: FormState) -> dict:
        return {
            lugar: {
                "selecionado": fields["selecionado"].get(),
                "distancia_km": fields["distancia_km"].get().strip(),
            }
            for lugar, fields in state.perto_lugares.items()
        }

    @staticmethod
    def _collect_seo(state: FormState) -> dict:
        return {
            "titulo": state.seo_titulo.get("1.0", "end-1c").strip(),
            "imagem": state.seo_imagem.get().strip(),
            "descricao": state.seo_descricao.get("1.0", "end-1c").strip(),
            "palavras_chave": state.seo_palavras_chave.get(
                "1.0", "end-1c"
            ).strip(),
        }

    @staticmethod
    def _collect_detalhes(state: FormState) -> dict:
        return {
            "categoria": state.detalhes_categoria.get().strip(),
            "titulo": state.detalhes_titulo.get().strip(),
            "slug": state.detalhes_slug.get().strip(),
            "descricao": state.detalhes_descricao.get("1.0", "end-1c").strip(),
            "tipo": state.detalhes_tipo.get(),
            "duracao_preco": (
                state.detalhes_duracao_preco.get()
                if state.detalhes_tipo.get() == "aluguel"
                else ""
            ),
            "preco": str(state.detalhes_preco.get()).strip(),
        }

    @staticmethod
    def _collect_anuncio(state: FormState) -> dict:
        return {
            "ciclos": state.ciclos_anuncio.get(),
            "repeticoes": state.repeticoes_anuncio.get(),
            "codigo": state.codigo_anuncio.get().strip(),
            "titulos": [
                t.get().strip() for t in state.titulos_anuncio if t.get().strip()
            ],
            "descricao": state.descricao_anuncio.get("1.0", "end-1c").strip(),
        }

    @staticmethod
    def _collect_imovel(state: FormState) -> dict:
        return {
            "finalidade": state.finalidade.get(),
            "tipo": state.tipo.get(),
            "categoria": state.categoria.get(),
            "quartos": AdHelper.to_int(state.quartos.get()),
            "suites": AdHelper.to_int(state.suites.get()),
            "banheiros": AdHelper.to_int(state.banheiros.get()),
            "vagas": AdHelper.to_int(state.vagas.get()),
            "area_util_m2": state.area_util.get(),
            "area_total_m2": state.area_total.get(),
            "andar": AdHelper.to_int(state.andar.get()),
            "localizacao": {
                "cep": state.cep.get().strip(),
                "bairro": state.bairro.get().strip(),
                "endereco": state.endereco.get().strip(),
                "numero": AdHelper.to_int(state.numero.get()),
                "complemento": state.complemento.get().strip(),
            },
            "caracteristicas": {
                "diferenciais": AdHelper.collect_checked(state.diferenciais),
                "outras": AdHelper.collect_checked(state.outras_caracteristicas_imovel),
            },
        }

    @staticmethod
    def _collect_condominio(state: FormState) -> dict:
        ano = str(state.cond_ano_construcao.get()).strip()

        return {
            "andares": AdHelper.to_int(state.cond_andares.get()),
            "unidades_por_andar": AdHelper.to_int(state.cond_unidades_por_andar.get()),
            "torres": AdHelper.to_int(state.cond_torres.get()),
            "ano_construcao": (AdHelper.to_int(ano) if ano else ""),
            "caracteristicas": {
                "lazer_esporte": AdHelper.collect_checked(state.cond_lazer_esporte),
                "comodidades_servicos": AdHelper.collect_checked(state.cond_comod_serv),
                "seguranca": AdHelper.collect_checked(state.cond_seguranca),
                "outras": AdHelper.collect_checked(
                    state.outras_caracteristicas_condominio
                ),
            },
        }

    @staticmethod
    def _collect_negociacao(state: FormState) -> dict:
        return {
            "tipo": state.tipo_negociacao.get(),
            "valor_venda": str(state.valor_venda.get()).strip(),
            "valor_aluguel": str(state.valor_aluguel.get()).strip(),
            "pagamento_aluguel": state.pagamento_aluguel.get().strip(),
            "condominio_isento": state.condominio_isento.get() == "sim",
            "valor_condominio": str(state.valor_condominio.get()).strip(),
            "iptu_isento": state.iptu_isento.get() == "sim",
            "valor_iptu": str(state.valor_iptu.get()).strip(),
            "periodo_iptu": state.periodo_iptu.get(),
            "modalidade_aluguel": AdHelper.collect_checked(state.modalidade_aluguel),
        }

    @staticmethod
    def apply_to_state(state: FormState, data: dict) -> None:
        AdFormMapper._populate_detalhes(state, data.get("detalhes", {}))
        AdFormMapper._populate_seo(state, data.get("seo", {}))
        AdFormMapper._populate_perto_de_lugares(
            state, data.get("perto_de_lugares", {})
        )
        AdFormMapper._populate_localizacao(state, data.get("localizacao", {}))
        AdFormMapper._populate_imagens(state, data.get("imagens", {}))
        AdFormMapper._populate_traducoes(state, data.get("traducoes", {}))
        AdFormMapper._populate_anuncio(state, data.get("anuncio", {}))
        AdFormMapper._populate_imovel(state, data.get("imovel", {}))
        AdFormMapper._populate_condominio(state, data.get("condominio", {}))
        AdFormMapper._populate_negociacao(state, data.get("negociacao", {}))

    @staticmethod
    def _populate_detalhes(state: FormState, detalhes: dict) -> None:
        state.detalhes_categoria.set(detalhes.get("categoria", ""))
        state.detalhes_titulo.set(detalhes.get("titulo", ""))
        state.detalhes_slug.set(detalhes.get("slug", ""))
        state.detalhes_tipo.set(detalhes.get("tipo", "venda"))
        state.detalhes_duracao_preco.set(detalhes.get("duracao_preco", ""))
        state.detalhes_preco.set(str(detalhes.get("preco", "")))
        state.detalhes_descricao.delete("1.0", "end")
        state.detalhes_descricao.insert("1.0", detalhes.get("descricao", ""))

    @staticmethod
    def _populate_seo(state: FormState, seo: dict) -> None:
        state.seo_imagem.set(seo.get("imagem", ""))
        for widget, value in (
            (state.seo_titulo, seo.get("titulo", "")),
            (state.seo_descricao, seo.get("descricao", "")),
            (state.seo_palavras_chave, seo.get("palavras_chave", "")),
        ):
            widget.delete("1.0", "end")
            widget.insert("1.0", value)

    @staticmethod
    def _populate_perto_de_lugares(state: FormState, lugares: dict) -> None:
        for lugar, fields in state.perto_lugares.items():
            saved = lugares.get(lugar, {})
            fields["selecionado"].set(bool(saved.get("selecionado", False)))
            fields["distancia_km"].set(str(saved.get("distancia_km", "")))

    @staticmethod
    def _populate_localizacao(state: FormState, localizacao: dict) -> None:
        state.localizacao_cidade.set(localizacao.get("cidade", ""))
        state.localizacao_pais.set(localizacao.get("pais", ""))
        state.localizacao_estado.set(localizacao.get("estado", ""))
        for widget, value in (
            (
                state.localizacao_endereco_cliente,
                localizacao.get("endereco_cliente", ""),
            ),
            (state.localizacao_endereco, localizacao.get("endereco", "")),
        ):
            widget.delete("1.0", "end")
            widget.insert("1.0", value)

    @staticmethod
    def _populate_imagens(state: FormState, imagens: dict) -> None:
        state.imagem_titulo.set(imagens.get("imagem_titulo", ""))
        state.imagem_3d.set(imagens.get("imagem_3d", ""))
        state.imagens_galeria = list(imagens.get("galeria", []))
        state.documentos = list(imagens.get("documentos", []))
        state.link_video.set(imagens.get("link_video", ""))

    @staticmethod
    def _populate_traducoes(state: FormState, traducoes: dict) -> None:
        portugues = traducoes.get("portugues", {})
        state.traducao_portugues_titulo.set(portugues.get("titulo", ""))
        state.traducao_portugues_descricao.delete("1.0", "end")
        state.traducao_portugues_descricao.insert(
            "1.0", portugues.get("descricao", "")
        )

    @staticmethod
    def _populate_anuncio(state: FormState, anuncio: dict) -> None:
        state.repeticoes_anuncio.set(anuncio.get("repeticoes", 1))
        state.ciclos_anuncio.set(anuncio.get("ciclos", 1))
        state.codigo_anuncio.set(anuncio.get("codigo", ""))
        titulos_anuncio = anuncio.get("titulos", [])
        for i, var in enumerate(state.titulos_anuncio):
            if i < len(titulos_anuncio):
                var.set(titulos_anuncio[i])
            else:
                var.set("")

        state.descricao_anuncio.delete("1.0", "end")
        state.descricao_anuncio.insert("1.0", anuncio.get("descricao", ""))

    @staticmethod
    def _populate_imovel(state: FormState, imovel: dict) -> None:
        state.finalidade.set(imovel.get("finalidade", "residencial"))
        type_options = (
            TIPOS_IMOVEL_COMERCIAL
            if state.finalidade.get() == "comercial"
            else TIPOS_IMOVEL_RESIDENCIAL
        )
        state.tipo.set(imovel.get("tipo", type_options[0]))
        state.categoria.set(imovel.get("categoria", "Padrão"))
        state.quartos.set(str(imovel.get("quartos", "1")))
        state.suites.set(str(imovel.get("suites", "0")))
        state.banheiros.set(str(imovel.get("banheiros", "1")))
        state.vagas.set(str(imovel.get("vagas", "0")))
        state.area_util.set(str(imovel.get("area_util_m2", "0")))
        state.area_total.set(str(imovel.get("area_total_m2", "0")))
        state.andar.set(str(imovel.get("andar", "0")))

        localizacao = imovel.get("localizacao", {})
        state.cep.set(localizacao.get("cep", ""))
        state.bairro.set(localizacao.get("bairro", ""))
        state.endereco.set(localizacao.get("endereco", ""))
        state.numero.set(localizacao.get("numero", 0))
        state.complemento.set(localizacao.get("complemento", ""))

        caracteristicas_imovel = imovel.get("caracteristicas", {})
        diferenciais = caracteristicas_imovel.get("diferenciais", [])
        AdHelper.apply_checklist(state.diferenciais, diferenciais)

        outras_caracteristicas_imovel = caracteristicas_imovel.get("outras", [])
        AdHelper.apply_checklist(
            state.outras_caracteristicas_imovel, outras_caracteristicas_imovel
        )

    @staticmethod
    def _populate_condominio(state: FormState, condominio: dict) -> None:
        state.cond_andares.set(str(condominio.get("andares", 0)))
        state.cond_unidades_por_andar.set(str(condominio.get("unidades_por_andar", 0)))
        state.cond_torres.set(str(condominio.get("torres", 0)))
        state.cond_ano_construcao.set(str(condominio.get("ano_construcao", "")))

        caracteristicas_condominio = condominio.get("caracteristicas", {})

        caracteristicas_lazer = caracteristicas_condominio.get("lazer_esporte", [])
        AdHelper.apply_checklist(state.cond_lazer_esporte, caracteristicas_lazer)

        caracteristicas_comod = caracteristicas_condominio.get(
            "comodidades_servicos", []
        )
        AdHelper.apply_checklist(state.cond_comod_serv, caracteristicas_comod)

        caracteristicas_seg = caracteristicas_condominio.get("seguranca", [])
        AdHelper.apply_checklist(state.cond_seguranca, caracteristicas_seg)

        outras_caracteristicas_condominio = caracteristicas_condominio.get("outras", [])
        AdHelper.apply_checklist(
            state.outras_caracteristicas_condominio,
            outras_caracteristicas_condominio,
        )

    @staticmethod
    def _populate_negociacao(state: FormState, negociacao: dict) -> None:
        state.tipo_negociacao.set(negociacao.get("tipo", "venda"))

        state.valor_venda.set(str(negociacao.get("valor_venda", 0)))
        state.valor_aluguel.set(str(negociacao.get("valor_aluguel", 0)))
        state.pagamento_aluguel.set(str(negociacao.get("pagamento_aluguel", "")))

        state.condominio_isento.set(
            "sim" if negociacao.get("condominio_isento", False) else "nao"
        )
        state.valor_condominio.set(str(negociacao.get("valor_condominio", 0)))

        state.iptu_isento.set("sim" if negociacao.get("iptu_isento", False) else "nao")
        state.valor_iptu.set(str(negociacao.get("valor_iptu", 0)))
        state.periodo_iptu.set(negociacao.get("periodo_iptu", "Anual"))

        modalidade_aluguel = negociacao.get("modalidade_aluguel", [])
        AdHelper.apply_checklist(state.modalidade_aluguel, modalidade_aluguel)
