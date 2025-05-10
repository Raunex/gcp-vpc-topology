# topologia_vpcs_tool.py
# Script para mapear e visualizar a topologia de VPCs na GCP com suporte a múltiplos projetos e regiões

from datetime import datetime
import json
import subprocess
import argparse
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import matplotlib.patches as mpatches

def run_gcloud_command(command):
    try:
        output = subprocess.check_output(command, shell=True)
        return json.loads(output)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar: {command}")
        return []

def coletar_topologia(output_file="topologia_vpcs.json"):
    topologia = {"vpcs": []}

    redes = run_gcloud_command("gcloud compute networks list --format=json")
    todas_subnets = run_gcloud_command("gcloud compute networks subnets list --format=json")
    todas_instancias = run_gcloud_command("gcloud compute instances list --format=json")

    for rede in redes:
        vpc_name = rede['name']
        project_id = rede["selfLink"].split("/")[6]
        vpc = {
            "name": vpc_name,
            "autoCreateSubnetworks": rede.get('autoCreateSubnetworks'),
            "subnets": [],
            "peerings": rede.get("peerings", []),
            "instances": [],
            "project": project_id
        }

        for subnet in todas_subnets:
            if subnet["network"].endswith(f"/{vpc_name}"):
                vpc["subnets"].append({
                    "name": subnet["name"],
                    "region": subnet["region"].split("/")[-1],
                    "ipCidrRange": subnet["ipCidrRange"],
                    "gatewayAddress": subnet.get("gatewayAddress"),
                    "secondaryIpRanges": subnet.get("secondaryIpRanges", [])
                })

        for instance in todas_instancias:
            for nic in instance.get("networkInterfaces", []):
                if nic["network"].endswith(f"/{vpc_name}"):
                    vpc["instances"].append({
                        "name": instance["name"],
                        "zone": instance["zone"].split("/")[-1],
                        "subnet": nic["subnetwork"].split("/")[-1] if "subnetwork" in nic else "N/A",
                        "ip": nic.get("networkIP")
                    })

        topologia["vpcs"].append(vpc)

    topologia["vpns"] = run_gcloud_command("gcloud compute vpn-tunnels list --format=json")
    topologia["routes"] = run_gcloud_command("gcloud compute routes list --format=json")
    topologia["firewalls"] = run_gcloud_command("gcloud compute firewall-rules list --format=json")

    with open(output_file, "w") as f:
        json.dump(topologia, f, indent=2)

    print(f"Topologia coletada e salva em '{output_file}'.")

def carregar_topologia(caminho="topologia_vpcs.json"):
    with open(caminho, "r") as f:
        return json.load(f)

def criar_grafo(topologia):
    G = nx.Graph()

    for vpc in topologia["vpcs"]:
        vpc_name = vpc["name"]
        project = vpc["project"]
        G.add_node(vpc_name, label=vpc_name, color="skyblue", project=project)

        for subnet in vpc["subnets"]:
            subnet_label = f"{subnet['name']} ({subnet['ipCidrRange']})"
            subnet_node = f"{vpc_name}:{subnet['name']}"
            G.add_node(subnet_node, label=subnet_label, color="lightgreen", region=subnet["region"], project=project)
            G.add_edge(vpc_name, subnet_node)

        for instance in vpc["instances"]:
            instance_label = f"{instance['name']} ({instance['ip']})"
            subnet_node = f"{vpc_name}:{instance['subnet']}"
            instance_node = f"{vpc_name}:{instance['name']}"
            G.add_node(instance_node, label=instance_label, color="orange", shape="ellipse", region=instance['zone'].split("-")[0], project=project)
            G.add_edge(subnet_node, instance_node)

        for peer in vpc["peerings"]:
            peer_name = peer["network"].split("/")[-1]
            if peer_name not in G:
                G.add_node(peer_name, label=peer_name, color="lightgray", shape="box")
            G.add_edge(vpc_name, peer_name, label="peering", color="gray")

    return G

def desenhar_grafo(G, mostrar=True, salvar=False, arquivo_saida="topologia_vpcs.png"):
    project_groups = {}
    for node in G.nodes:
        project = G.nodes[node].get("project", "default")
        region = G.nodes[node].get("region", "global")
        if project not in project_groups:
            project_groups[project] = {}
        if region not in project_groups[project]:
            project_groups[project][region] = []
        project_groups[project][region].append(node)

    pos = {}
    y_step = 10
    x_step = 5
    y = 0

    for project, regions in sorted(project_groups.items()):
        for region, nodes in sorted(regions.items()):
            x = 0
            for node in nodes:
                pos[node] = (x, -y)
                x += x_step
            y += y_step

    node_colors = [G.nodes[n].get("color", "lightgrey") for n in G.nodes]
    labels = {n: G.nodes[n].get("label", n) for n in G.nodes}

    plt.figure(figsize=(18, 12))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1400)
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7)

    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)

    plt.title("Topologia de VPCs GCP", fontsize=12)
    plt.axis("off")

    legend_elements = [
        mpatches.Patch(color="skyblue", label="VPC"),
        mpatches.Patch(color="lightgreen", label="Sub-rede"),
        mpatches.Patch(color="orange", label="Instância"),
        mpatches.Patch(color="lightgray", label="VPC (Peering externo)"),
    ]
    plt.legend(handles=legend_elements, loc="lower center", fontsize=9, ncol=4, frameon=True)

    for project, regions in sorted(project_groups.items()):
        for region, nodes in sorted(regions.items()):
            if not nodes:
                continue
            region_x = sum([pos[n][0] for n in nodes]) / len(nodes)
            region_y = min([pos[n][1] for n in nodes]) - 2
            plt.text(region_x, region_y, f"{region.upper()} ({project})", fontsize=9, fontweight="bold",
                     ha="center", bbox=dict(facecolor='lightgray', alpha=0.3, boxstyle='round,pad=0.3'))

    plt.tight_layout()

    if salvar:
        plt.savefig(arquivo_saida, format="png", dpi=300)
        print(f"Imagem salva em: {arquivo_saida}")
    if mostrar:
        try:
            plt.show()
        except Exception:
            print("Aviso: ambiente não suporta visualização interativa (plt.show()).")
    else:
        plt.close()

def gerar_html_interativo(topologia, arquivo_saida="topologia_vpcs.html"):
    net = Network(height="800px", width="100%", directed=False, notebook=False, bgcolor="#ffffff")

    for vpc in topologia["vpcs"]:
        vpc_name = vpc["name"]
        net.add_node(vpc_name, label=vpc_name, color="skyblue", shape="box")

        for subnet in vpc["subnets"]:
            subnet_label = f"{subnet['name']} ({subnet['ipCidrRange']})"
            subnet_id = f"{vpc_name}:{subnet['name']}"
            net.add_node(subnet_id, label=subnet_label, color="lightgreen", shape="ellipse")
            net.add_edge(vpc_name, subnet_id)

        for instance in vpc["instances"]:
            instance_label = f"{instance['name']} ({instance['ip']})"
            instance_id = f"{vpc_name}:{instance['name']}"
            subnet_id = f"{vpc_name}:{instance['subnet']}"
            net.add_node(instance_id, label=instance_label, color="orange", shape="dot")
            net.add_edge(subnet_id, instance_id)

        for peer in vpc["peerings"]:
            peer_name = peer["network"].split("/")[-1]
            if not any(node["id"] == peer_name for node in net.nodes):
                net.add_node(peer_name, label=peer_name, color="lightgray", shape="box")
            net.add_edge(vpc_name, peer_name, color="gray", title="Peering")

    net.write_html(arquivo_saida)
    print(f"Arquivo HTML interativo gerado: {arquivo_saida}")

def gerar_html_tabelas(topologia, arquivo_saida="topologia_tabelas.html"):
    def gerar_tabela(lista, titulo):
        if not lista:
            return f"<h2>{titulo}</h2><p>Nenhum dado encontrado.</p>"
        chaves = list(lista[0].keys())
        html = f"<h2>{titulo}</h2><table border='1' cellpadding='4' cellspacing='0'><thead><tr>"
        html += "".join([f"<th>{k}</th>" for k in chaves]) + "</tr></thead><tbody>"
        for item in lista:
            html += "<tr>" + "".join([f"<td>{item.get(k, '')}</td>" for k in chaves]) + "</tr>"
        html += "</tbody></table>"
        return html

    html = "<html><head><meta charset='UTF-8'><title>Topologia GCP - Rotas e Firewalls</title></head><body>"
    html += gerar_tabela(topologia.get("routes", []), "Rotas")
    html += gerar_tabela(topologia.get("firewalls", []), "Regras de Firewall")
    html += gerar_tabela(topologia.get("vpns", []), "Túneis VPN")
    html += "</body></html>"

    with open(arquivo_saida, "w") as f:
        f.write(html)

    print(f"Arquivo HTML de tabelas gerado: {arquivo_saida}")

def main():
    parser = argparse.ArgumentParser(description="Mapeamento e visualização de topologia de VPCs na GCP")
    parser.add_argument("--coletar", action="store_true", help="Coleta e salva a topologia como JSON")
    parser.add_argument("--exibir", action="store_true", help="Exibe o grafo na tela")
    parser.add_argument("--salvar", action="store_true", help="Salva o grafo como imagem PNG")
    parser.add_argument("--html", action="store_true", help="Gera visualização interativa em HTML")
    parser.add_argument("--arquivo", type=str, default=None, help="(Opcional) Nome base do arquivo JSON")

    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = args.arquivo or f"topologia_vpcs_{timestamp}"
    arquivo_json = f"{base}.json"
    arquivo_png = f"{base}.png"
    arquivo_html = f"{base}.html"
    arquivo_html_tabelas = f"topologia_tabelas_{timestamp}.html"

    if args.coletar:
        coletar_topologia(arquivo_json)

    if args.exibir or args.salvar or args.html:
        topologia = carregar_topologia(arquivo_json)

    if args.exibir or args.salvar:
        grafo = criar_grafo(topologia)
        desenhar_grafo(grafo, mostrar=args.exibir, salvar=args.salvar, arquivo_saida=arquivo_png)

    if args.html:
        gerar_html_interativo(topologia, arquivo_saida=arquivo_html)
        gerar_html_tabelas(topologia, arquivo_saida=arquivo_html_tabelas)

if __name__ == "__main__":
    main()

