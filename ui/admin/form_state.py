import tkinter as tk

from domain.catalog_admin import LUGARES_PROXIMOS, TIPOS_IMOVEL_RESIDENCIAL


class FormState:

    def __init__(self, main):
        self.detalhes_categoria = tk.StringVar(main, value="")
        self.detalhes_titulo = tk.StringVar(main, value="")
        self.detalhes_slug = tk.StringVar(main, value="")
        self.detalhes_descricao = tk.StringVar(main, value="")
        self.detalhes_tipo = tk.StringVar(main, value="venda")
        self.detalhes_duracao_preco = tk.StringVar(main, value="Mensal")
        self.detalhes_preco = tk.StringVar(main, value="")

        self.seo_titulo = tk.StringVar(main, value="")
        self.seo_imagem = tk.StringVar(main, value="")
        self.seo_descricao = tk.StringVar(main, value="")
        self.seo_palavras_chave = tk.StringVar(main, value="")

        self.perto_lugares = {
            lugar: {
                "selecionado": tk.BooleanVar(main, value=False),
                "distancia_km": tk.StringVar(main, value=""),
            }
            for lugar in LUGARES_PROXIMOS
        }

        self.localizacao_cidade = tk.StringVar(main, value="Fortaleza")
        self.localizacao_pais = tk.StringVar(main, value="Brasil")
        self.localizacao_estado = tk.StringVar(main, value="Ceará")
        self.localizacao_endereco_cliente = tk.StringVar(main, value="")
        self.localizacao_endereco = tk.StringVar(main, value="")

        self.imagem_titulo = tk.StringVar(main, value="")
        self.imagem_3d = tk.StringVar(main, value="")
        self.imagens_galeria = []
        self.documentos = []
        self.link_video = tk.StringVar(main, value="")

        self.traducao_portugues_titulo = tk.StringVar(main, value="")
        self.traducao_portugues_descricao = tk.StringVar(main, value="")

        self.ciclos_anuncio = tk.IntVar(value=5)
        self.repeticoes_anuncio = tk.IntVar(value=1)
        self.codigo_anuncio = tk.StringVar(value="")
        self.titulos_anuncio = [tk.StringVar() for _ in range(self.repeticoes_anuncio.get())]
        self.descricao_anuncio = tk.Text(main)

        self.finalidade = tk.StringVar(main, value="residencial")
        self.tipo = tk.StringVar(main, value=TIPOS_IMOVEL_RESIDENCIAL[0])
        self.categoria = tk.StringVar(main, value="Padrão")
        self.quartos = tk.StringVar(main, value="0")
        self.suites = tk.StringVar(main, value="0")
        self.banheiros = tk.StringVar(main, value="0")
        self.vagas = tk.StringVar(main, value="0")
        self.area_util = tk.StringVar(main, value="0")
        self.area_total = tk.StringVar(main, value="0")
        self.andar = tk.StringVar(main, value="0")

        self.cep = tk.StringVar(main, value="")
        self.bairro = tk.StringVar(main, value="")
        self.endereco = tk.StringVar(main, value="")
        self.numero = tk.IntVar(main, value=0)
        self.complemento = tk.StringVar(main, value="")

        self.diferenciais = {
            "Aceita animais": tk.BooleanVar(value=False),
            "Ar-condicionado": tk.BooleanVar(value=False),
            "Closet": tk.BooleanVar(value=False),
            "Cozinha americana": tk.BooleanVar(value=False),
            "Lareira": tk.BooleanVar(value=False),
            "Mobiliado": tk.BooleanVar(value=False),
            "Varanda gourmet": tk.BooleanVar(value=False),
        }
        self.outras_caracteristicas_imovel = {
            "Conexão à internet": tk.BooleanVar(value=False),
            "Ambientes integrados": tk.BooleanVar(value=False),
            "Andar inteiro": tk.BooleanVar(value=False),
            "Aquário": tk.BooleanVar(value=False),
            "Área de serviço": tk.BooleanVar(value=False),
            "Armário embutido": tk.BooleanVar(value=False),
            "Armário embutido no quarto": tk.BooleanVar(value=False),
            "Armário na cozinha": tk.BooleanVar(value=False),
            "Armário no banheiro": tk.BooleanVar(value=False),
            "Banheira": tk.BooleanVar(value=False),
            "Banheiro de serviço": tk.BooleanVar(value=False),
            "Bar": tk.BooleanVar(value=False),
            "Box blindex": tk.BooleanVar(value=False),
            "Carpete": tk.BooleanVar(value=False),
            "Casa de caseiro": tk.BooleanVar(value=False),
            "Casa de fundo": tk.BooleanVar(value=False),
            "Casa sede": tk.BooleanVar(value=False),
            "Churrasqueira na varanda": tk.BooleanVar(value=False),
            "Chuveiro a gás": tk.BooleanVar(value=False),
            "Cimento queimado": tk.BooleanVar(value=False),
            "Copa": tk.BooleanVar(value=False),
            "Cozinha gourmet": tk.BooleanVar(value=False),
            "Cozinha grande": tk.BooleanVar(value=False),
            "Dependência de empregados": tk.BooleanVar(value=False),
            "Depósito": tk.BooleanVar(value=False),
            "Despensa": tk.BooleanVar(value=False),
            "Drywall": tk.BooleanVar(value=False),
            "Edícula": tk.BooleanVar(value=False),
            "Escada": tk.BooleanVar(value=False),
            "Escritório": tk.BooleanVar(value=False),
            "Fogão": tk.BooleanVar(value=False),
            "Forno de pizza": tk.BooleanVar(value=False),
            "Freezer": tk.BooleanVar(value=False),
            "Geminada": tk.BooleanVar(value=False),
            "Gesso - Sanca - Teto Rebaixado": tk.BooleanVar(value=False),
            "Hidromassagem": tk.BooleanVar(value=False),
            "Imóvel de esquina": tk.BooleanVar(value=False),
            "Interfone": tk.BooleanVar(value=False),
            "Isolamento acústico": tk.BooleanVar(value=False),
            "Isolamento térmico": tk.BooleanVar(value=False),
            "Janela de alumínio": tk.BooleanVar(value=False),
            "Janela grande": tk.BooleanVar(value=False),
            "Laje": tk.BooleanVar(value=False),
            "Lavabo": tk.BooleanVar(value=False),
            "Meio andar": tk.BooleanVar(value=False),
            "Mezanino": tk.BooleanVar(value=False),
            "Móvel planejado": tk.BooleanVar(value=False),
            "Muro de vidro": tk.BooleanVar(value=False),
            "Muro e grade": tk.BooleanVar(value=False),
            "Ofurô": tk.BooleanVar(value=False),
            "Pé direito alto": tk.BooleanVar(value=False),
            "Piso de madeira": tk.BooleanVar(value=False),
            "Piso elevado": tk.BooleanVar(value=False),
            "Piso frio": tk.BooleanVar(value=False),
            "Piso laminado": tk.BooleanVar(value=False),
            "Piso vinílico": tk.BooleanVar(value=False),
            "Platibanda": tk.BooleanVar(value=False),
            "Porcelanato": tk.BooleanVar(value=False),
            "Possui divisória": tk.BooleanVar(value=False),
            "Quarto de serviço": tk.BooleanVar(value=False),
            "Quarto extra reversível": tk.BooleanVar(value=False),
            "Quintal": tk.BooleanVar(value=False),
            "TV a cabo": tk.BooleanVar(value=False),
            "Varanda": tk.BooleanVar(value=False),
            "Varanda fechada com vidro": tk.BooleanVar(value=False),
            "Ventilação natural": tk.BooleanVar(value=False),
            "Vista para o mar": tk.BooleanVar(value=False),
            "Vista panorâmica": tk.BooleanVar(value=False),
            "Vista para a montanha": tk.BooleanVar(value=False),
            "Vista para lago": tk.BooleanVar(value=False),
            "Sala de almoço": tk.BooleanVar(value=False),
            "Sala de jantar": tk.BooleanVar(value=False),
            "Sala grande": tk.BooleanVar(value=False),
            "Sala pequena": tk.BooleanVar(value=False),
            "Piscina privativa": tk.BooleanVar(value=False),
        }
        self.cond_andares = tk.StringVar(value="0")
        self.cond_unidades_por_andar = tk.StringVar(value="0")
        self.cond_torres = tk.StringVar(value="0")
        self.cond_ano_construcao = tk.StringVar(value="")
        self.cond_lazer_esporte = {
            "Academia": tk.BooleanVar(value=False),
            "Churrasqueira": tk.BooleanVar(value=False),
            "Cinema": tk.BooleanVar(value=False),
            "Espaço gourmet": tk.BooleanVar(value=False),
            "Jardim": tk.BooleanVar(value=False),
            "Piscina": tk.BooleanVar(value=False),
            "Playground": tk.BooleanVar(value=False),
            "Quadra de squash": tk.BooleanVar(value=False),
            "Quadra de tênis": tk.BooleanVar(value=False),
            "Quadra poliesportiva": tk.BooleanVar(value=False),
            "Salão de festas": tk.BooleanVar(value=False),
            "Salão de jogos": tk.BooleanVar(value=False),
        }
        self.cond_comod_serv = {
            "Acesso para deficientes": tk.BooleanVar(value=False),
            "Bicicletário": tk.BooleanVar(value=False),
            "Coworking": tk.BooleanVar(value=False),
            "Elevador": tk.BooleanVar(value=False),
            "Lavanderia": tk.BooleanVar(value=False),
            "Sauna": tk.BooleanVar(value=False),
            "Spa": tk.BooleanVar(value=False),
        }
        self.cond_seguranca = {
            "Condomínio fechado": tk.BooleanVar(value=False),
            "Portão eletrônico": tk.BooleanVar(value=False),
            "Portaria 24h": tk.BooleanVar(value=False),
        }
        self.outras_caracteristicas_condominio = {
            "Aquário": tk.BooleanVar(value=False),
            "Área de lazer": tk.BooleanVar(value=False),
            "Árvore frutífera": tk.BooleanVar(value=False),
            "Arvorismo": tk.BooleanVar(value=False),
            "Bar na piscina": tk.BooleanVar(value=False),
            "Biblioteca": tk.BooleanVar(value=False),
            "Brinquedoteca": tk.BooleanVar(value=False),
            "Câmera de segurança": tk.BooleanVar(value=False),
            "Campo de futebol": tk.BooleanVar(value=False),
            "Campo de golfe": tk.BooleanVar(value=False),
            "Canil": tk.BooleanVar(value=False),
            "Celeiro": tk.BooleanVar(value=False),
            "Centro de estética": tk.BooleanVar(value=False),
            "Cerca": tk.BooleanVar(value=False),
            "Children care": tk.BooleanVar(value=False),
            "Circuito de segurança": tk.BooleanVar(value=False),
            "Cobertura coletiva": tk.BooleanVar(value=False),
            "Coffee shop": tk.BooleanVar(value=False),
            "Curral": tk.BooleanVar(value=False),
            "Deck": tk.BooleanVar(value=False),
            "Entrada de serviço": tk.BooleanVar(value=False),
            "Entrada lateral": tk.BooleanVar(value=False),
            "Espaço teen": tk.BooleanVar(value=False),
            "Espaço Pet": tk.BooleanVar(value=False),
            "Espaço verde / Parque": tk.BooleanVar(value=False),
            "Espaço zen": tk.BooleanVar(value=False),
            "Estacionamento para visitantes": tk.BooleanVar(value=False),
            "Forno de pizza": tk.BooleanVar(value=False),
            "Gerador elétrico": tk.BooleanVar(value=False),
            "Gramado": tk.BooleanVar(value=False),
            "Guarita": tk.BooleanVar(value=False),
            "Hall de entrada": tk.BooleanVar(value=False),
            "Heliponto": tk.BooleanVar(value=False),
            "Hidromassagem": tk.BooleanVar(value=False),
            "Horta": tk.BooleanVar(value=False),
            "Lago": tk.BooleanVar(value=False),
            "Marina": tk.BooleanVar(value=False),
            "Muro de escalada": tk.BooleanVar(value=False),
            "Ofurô": tk.BooleanVar(value=False),
            "Orquidário": tk.BooleanVar(value=False),
            "Pasto": tk.BooleanVar(value=False),
            "Piscina aquecida": tk.BooleanVar(value=False),
            "Piscina coberta": tk.BooleanVar(value=False),
            "Piscina infantil": tk.BooleanVar(value=False),
            "Piscina para adulto": tk.BooleanVar(value=False),
            "Pista de cooper": tk.BooleanVar(value=False),
            "Pista de skate": tk.BooleanVar(value=False),
            "Poço": tk.BooleanVar(value=False),
            "Poço artesiano": tk.BooleanVar(value=False),
            "Pomar": tk.BooleanVar(value=False),
            "Praça": tk.BooleanVar(value=False),
            "Recepção": tk.BooleanVar(value=False),
            "Redario": tk.BooleanVar(value=False),
            "Reservatório de água": tk.BooleanVar(value=False),
            "Restaurante": tk.BooleanVar(value=False),
            "Rio": tk.BooleanVar(value=False),
            "Ronda/Vigilância": tk.BooleanVar(value=False),
            "Sala de massagem": tk.BooleanVar(value=False),
            "Sala de reunião": tk.BooleanVar(value=False),
            "Salão de convenção": tk.BooleanVar(value=False),
            "Serviços pay per use": tk.BooleanVar(value=False),
            "Sistema de alarme": tk.BooleanVar(value=False),
            "Solarium": tk.BooleanVar(value=False),
            "Vestiário para diaristas": tk.BooleanVar(value=False),
            "Vigia": tk.BooleanVar(value=False),
        }

        self.tipo_negociacao = tk.StringVar(value="venda")
        self.valor_venda = tk.StringVar(value="0")
        self.valor_aluguel = tk.StringVar(value="0")
        self.pagamento_aluguel = tk.StringVar(value="Mensal")
        self.condominio_isento = tk.StringVar(value="nao")
        self.valor_condominio = tk.StringVar(value="0")
        self.iptu_isento = tk.StringVar(value="nao")
        self.valor_iptu = tk.StringVar(value="0")
        self.periodo_iptu = tk.StringVar(value="Anual")
        self.modalidade_aluguel = {
            "Depósito caução": tk.BooleanVar(value=False),
            "Carta fiança": tk.BooleanVar(value=False),
            "Título de capitalização": tk.BooleanVar(value=False),
            "Seguro fiança": tk.BooleanVar(value=False),
            "Fiador": tk.BooleanVar(value=False),
        }
        self.mod_dep_caucao = tk.BooleanVar(value=False)
        self.mod_carta_fianca = tk.BooleanVar(value=False)
        self.mod_titulo_cap = tk.BooleanVar(value=False)
        self.mod_seguro_fianca = tk.BooleanVar(value=False)
        self.mod_fiador = tk.BooleanVar(value=False)
