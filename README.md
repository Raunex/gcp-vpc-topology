# gcp-vpc-topology

## GCP VPC Topology Mapper

Este projeto permite mapear automaticamente a **topologia de redes VPC** no Google Cloud Platform (GCP), incluindo:

- VPCs e Subnets
- Peerings entre redes
- Instâncias conectadas por sub-rede
- Rotas e regras de firewall
- Túneis VPN
- Suporte a múltiplos projetos
- Visualização em imagem PNG (legível) e HTML interativo

---

### 🚀 Funcionalidades

- Agrupamento por **projeto e região**
- Visualização em **PNG com legenda**
- Visualização em **HTML interativo com PyVis**
- Exportação de **rotas, regras de firewall e VPNs** em tabelas HTML

---

### 🧰 Pré-requisitos

- Python 3.8+
- Google Cloud SDK (`gcloud`) instalado e autenticado
- Permissões de leitura de rede no(s) projeto(s)
- Pacotes Python

---

### 📦 Como usar

1. Ative seu ambiente virtual (opcional)

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instale as dependências

```bash
pip install -r requirements.txt
```

3. Execute o script principal

```bash
python topologia_vpcs_tool.py --coletar --salvar --html
```

---

### 🛠  Opções disponíveis

| Argumento        | Descrição                                                                 |
|------------------|---------------------------------------------------------------------------|
| `--coletar`      | Coleta dados da GCP usando `gcloud` e salva no arquivo JSON               |
| `--salvar`       | Gera imagem PNG da topologia com layout visual e legenda                 |
| `--exibir`       | Abre a visualização da topologia em uma janela (usando matplotlib)        |
| `--html`         | Gera duas visualizações HTML: grafo interativo e tabelas de rede          |
| `--arquivo`      | (Opcional) Define o nome base do arquivo JSON de entrada/saída            |

---

### 📁 Estrutura esperada dos arquivos

```bash
gcp-vpc-topology/
├── topologia_vpcs_tool.py
├── requirements.txt
├── README.md
├── topologia_vpcs_20250510_143000.json
├── topologia_vpcs_20250510_143000.png
├── topologia_vpcs_20250510_143000.html
└── topologia_tabelas_20250510_143000.html
```

---

### ✅ Requisitos de permissão no GCP

Você precisa ter permissões nos projetos para visualizar redes:

- *roles/compute.networkViewer*

- *roles/compute.viewer*

Se estiver usando vários projetos, alterne entre eles com:

```bash
gcloud config set project PROJECT_ID
```

---

### 📋 Dependências incluídas

```txt
matplotlib==3.10.3
networkx==3.4.2
pyvis==0.3.1
pydot==4.0.0
```

**Recomendado:** instalar também o Graphviz para layout avançado:

**Ubuntu/Debian:** sudo apt install graphviz

**macOS:** brew install graphviz

**Windows:** https://graphviz.org/download




