# INKAZA

Publicador automatizado de anúncios, com interface para gerenciamento dos dados do anúncio e execução do processo de publicação.

O projeto possui um launcher com dois fluxos principais:

- **Gerenciar Propriedade**: utilizado para criar e editar os dados dos anúncios
- **Publicar Propriedade**: utilizado para executar a publicação automatizada

No ambiente de desenvolvimento, esses fluxos podem ser executados a partir do código-fonte. Para distribuição ao cliente, o projeto gera executáveis específicos para cada sistema operacional:

- **macOS**: `.app`
- **Windows**: `.exe`

## Requisitos

Antes de iniciar, tenha instalado na máquina:

- **Python 3**
- **pip3**
- Dependências necessárias para execução do **Playwright**

## Setup do ambiente

```bash
python3 -m venv .venv # Crie e ative um ambiente virtual:
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip3 install -r requirements.txt # Instale as dependências do projeto:
playwright install # Instale os navegadores utilizados pelo Playwright:
```

## Gerando executáveis

Para gerar os executáveis do projeto:
```bash
make release
```
Esse comando gera um único aplicativo, **INKAZA**. Nesta primeira entrega, o
fluxo de gerenciamento de propriedades está disponível e a publicação permanece
desativada no launcher.

Resultado esperado:

- no macOS, será gerado um aplicativo `.app`
- no Windows, será gerado um executável `.exe`

## CI

A pipeline `CI` é executada em pushes para `main` e em pull requests. Ela:

- valida a sintaxe dos módulos Python;
- valida os imports do launcher e do administrador;
- testa criação, leitura, atualização e exclusão de propriedades e mídias;
- executa um build de verificação com PyInstaller.

## Criando uma entrega para teste

No GitHub, acesse **Actions → Release INKAZA → Run workflow** e informe:

- `target`: `all`, `windows` ou `macos`;
- `prerelease`: mantenha marcado para entregas de homologação.

A versão é calculada automaticamente a partir da maior tag `vX.Y.Z` e dos
commits posteriores, seguindo Conventional Commits:

- `fix:` incrementa patch (`0.0.1` → `0.0.2`);
- `feat:` incrementa minor (`0.0.2` → `0.1.0`);
- `BREAKING CHANGE:` ou `feat!:` incrementa major (`0.1.0` → `1.0.0`).

Quando há commits de tipos diferentes, prevalece o de maior impacto. A release é
interrompida se nenhum commit posterior à última tag usar um desses formatos.

A opção `all` gera os seguintes arquivos:

- `INKAZA-vX.Y.Z-windows-x64.zip`;
- `INKAZA-vX.Y.Z-macos-x64.zip`, para Macs Intel;
- `INKAZA-vX.Y.Z-macos-arm64.zip`, para Macs Apple Silicon.

No Windows, extraia todo o conteúdo do ZIP e execute `INKAZA/INKAZA.exe`. Os
arquivos que acompanham o executável na pasta `INKAZA` são necessários para o
funcionamento da aplicação.

Ao concluir, os pacotes ficam disponíveis tanto nos artefatos da execução quanto
na pré-release criada na seção **Releases** do repositório.

Esta primeira versão não possui assinatura comercial. No macOS, pode ser
necessário clicar com o botão direito no aplicativo e selecionar **Abrir**. No
Windows, o SmartScreen pode solicitar confirmação para executar o aplicativo.
