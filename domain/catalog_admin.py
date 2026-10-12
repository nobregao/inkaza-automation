TIPOS_IMOVEL_RESIDENCIAL = [
    "Apartamento",
    "Casa",
    "Casa de condomínio",
    "Casa de vila",
    "Cobertura",
    "Fazenda/Sítio/Chácara",
    "Flat",
    "Kitnet/Conjugado",
    "Loft",
    "Lote/Terreno",
    "Prédio/Edifício inteiro",
    "Studio",
]

TIPOS_IMOVEL_COMERCIAL = [
    "Casa",
    "Escritório",
    "Galpão/Depósito/Armazém",
    "Garagem",
    "Hotel/Motel/Pousada",
    "Lote/Terreno",
    "Ponto comercial/Loja/Box",
    "Prédio/Edifício inteiro",
]

CATEGORIAS_RESIDENCIAL = ["Duplex", "Triplex", "Padrão"]

CATEGORIAS_COMERCIAL = ["Padrão", "Sobrado"]

NUMERO_OPCOES = [str(i) for i in range(0, 51)]

CATEGORIAS_DETALHES = [
    "Condo",
    "House",
    "Plote",
    "Apartament",
    "Penthouse",
    "Commercial",
    "Farm",
    "New Property",
    "Transfer",
]

DURACOES_PRECO = ["Diariamente", "Mensalmente", "Anualmente", "Trimestralmente"]

INSTALACOES_POR_CATEGORIA = {
    "Condo": (
        "piscina", "wifi", "elevadores", "fitness", "cctv",
        "ar_condicionado", "seguranca", "estacionamento", "area",
        "recepcao", "garagem", "extras",
    ),
    "House": (
        "piscina", "wifi", "ar_condicionado", "area", "garagem",
        "cozinha", "banheiros", "quartos",
    ),
    "Plote": ("area",),
    "Apartment": ("area", "garagem", "banheiros", "quartos"),
    "Apartament": ("area", "garagem", "banheiros", "quartos"),
    "Penthouse": (
        "piscina", "wifi", "elevadores", "fitness", "cctv",
        "ar_condicionado", "seguranca", "estacionamento", "area",
        "recepcao", "garagem", "sacadas", "extras",
    ),
    "Commercial": ("area", "garagem", "banheiros"),
    "Farm": (
        "wifi", "cctv", "ar_condicionado", "seguranca",
        "estacionamento", "recepcao", "garagem",
    ),
    "New Property": ("area", "garagem", "banheiros", "quartos"),
    "Transfer": ("area", "garagem", "banheiros", "quartos"),
}

INSTALACOES_OBRIGATORIAS_POR_CATEGORIA = {
    "Condo": {"area", "garagem"},
    "House": {"area", "garagem", "banheiros", "quartos"},
    "Plote": {"area"},
    "Apartment": {"area", "garagem", "banheiros", "quartos"},
    "Apartament": {"area", "garagem", "banheiros", "quartos"},
    "Penthouse": {"area", "garagem"},
    "Commercial": {"area", "garagem", "banheiros"},
    "Farm": {"garagem"},
    "New Property": {"area", "garagem", "banheiros", "quartos"},
    "Transfer": {"area", "garagem", "banheiros", "quartos"},
}

LUGARES_PROXIMOS = [
    "Mall",
    "Gas Station",
    "Garden",
    "Gym",
    "Bus Stop",
    "Bank ATM",
    "Supermarket",
    "School",
    "Hospital",
]
