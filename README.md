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
Esse comando gera um único aplicativo, **INKAZA**. O fluxo de publicação abre o
Google Chrome com uma sessão persistente e usa as credenciais salvas na aplicação
quando a sessão da INKAZA expirar.

## Testando o publicador

Cadastre propriedades completas e clique em **Publicar Propriedade** no launcher.
Informe o login e a senha uma vez; as credenciais são criptografadas antes de serem
armazenadas no SQLite e são carregadas automaticamente nas próximas execuções.

Ao clicar em **Publicar todas não sincronizadas**, a aplicação solicita uma única
confirmação, reutiliza a mesma sessão do Chrome e publica sequencialmente todas as
propriedades com status `NOT_SYNC`. Cada propriedade confirmada pela INKAZA passa
para o status `SYNC`; erros são apresentados na tela e não interrompem as demais.

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
Depois de calcular a versão, a pipeline atualiza `version.py`, cria automaticamente
um commit `chore(release)` na branch `main` e usa esse mesmo commit para gerar os
executáveis e a tag da release.

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

### Licença para publicação

Na tela de publicação, informe a **Licença** ao lado da senha. Antes de abrir o
navegador, cada tentativa de publicação consulta
`https://raw.githubusercontent.com/nobregao/inkaza-license/refs/heads/main/license.json`.
O arquivo deve conter um objeto por chave de licença, neste formato:

```json
{
  "CHAVE-DO-CLIENTE": {
    "active": true,
    "expires_at": "2026-10-22"
  }
}
```

A publicação exige uma chave existente, `active` igual a `true` e uma data
`expires_at` válida (`AAAA-MM-DD`), inclusiva até o fim do dia no horário de
Recife (UTC-3). Licenças ausentes, inativas, vencidas, respostas inválidas ou
falhas de conexão bloqueiam a publicação. A consulta tem timeout de 15 segundos
e ocorre em segundo plano. Ao iniciar a publicação, a licença é salva criptografada
na mesma tabela e com a mesma chave de login e senha, sendo carregada ao reabrir
a tela. O armazenamento local não substitui a validação online a cada publicação.

Para desativar uma licença, altere `active` para `false` no arquivo remoto;
a alteração será verificada na próxima tentativa, sujeita à propagação do
GitHub. Um lote já iniciado não é interrompido. Como o arquivo é público,
suas chaves também são públicas: esta verificação não autentica a identidade
do cliente nem impede alterações no código de uma instalação sob seu controle.
