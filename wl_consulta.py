import xml.etree.ElementTree as ET

import Dataset
import pynetdicom

from pynetdicom.sop_class import ModalityWorklistInformationFind


# Função para carregar as configurações do XML
def load_config_from_xml(filename='config.xml'):
    try:
        tree = ET.parse(filename)
        root = tree.getroot()

        worklist_ip = root.find('./worklist/ip').text
        worklist_port = int(root.find('./worklist/port').text)
        worklist_aet = root.find('./worklist/aet').text

        seu_programa_ip = root.find('./program/ip').text
        seu_programa_port = int(root.find('./program/port').text)
        seu_programa_aet = root.find('./program/aet').text

        return {
            "worklist_ip": worklist_ip,
            "worklist_port": worklist_port,
            "worklist_aet": worklist_aet,
            "seu_programa_ip": seu_programa_ip,
            "seu_programa_port": seu_programa_port,
            "seu_programa_aet": seu_programa_aet
        }
    except FileNotFoundError:
        print(f"Erro: O arquivo {filename} não foi encontrado.")
        return None
    except ET.ParseError:
        print(f"Erro: O arquivo {filename} está mal formatado.")
        return None
    except Exception as e:
        print(f"Erro inesperado ao carregar {filename}: {str(e)}")
        return None


# Função para criar um arquivo XML com os dados da Worklist
def save_worklist_to_xml(worklist_data, filename='worklist.xml'):
    try:
        root = ET.Element("Worklist")

        for idx, item in enumerate(worklist_data, start=1):
            worklist_item = ET.SubElement(root, f"Item{idx}")
            for elem in item:
                element = ET.SubElement(worklist_item, elem.keyword)
                element.text = str(elem.value)

        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        print(f"Worklist salva em {filename}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo XML: {str(e)}")


pynetdicom.debug_logger()

# Carrega as configurações do arquivo XML
config = load_config_from_xml()

if config is None:
    print("Erro ao carregar as configurações. Verifique o arquivo config.xml.")
    exit(1)  # Termina o programa se houver um erro nas configurações

# Criação da instância do ApplicationEntity (AE) do seu programa
ae = pynetdicom.AE(ae_title=config['seu_programa_aet'])

# Adiciona o contexto de apresentação para a SOP Class 'Worklist Information Model - FIND'
ae.add_requested_context(ModalityWorklistInformationFind)

# Associação (connection) com o servidor de Worklist
try:
    assoc = ae.associate(config['worklist_ip'], config['worklist_port'], ae_title=config['worklist_aet'])

    if assoc.is_established:
        print("Associação estabelecida com sucesso.")

        ds = Dataset()  # Dataset de consulta vazio

        worklist_items = []

        # Realiza a consulta (C-FIND) para obter a Worklist
        for (status, identifier) in assoc.send_c_find(ds, ModalityWorklistInformationFind):
            if status and identifier:
                worklist_items.append(identifier)
            else:
                print("Nenhum item encontrado na Worklist ou fim da lista.")
                break

        # Salva os itens da Worklist em um arquivo XML
        if worklist_items:
            save_worklist_to_xml(worklist_items)

        # Encerra a associação DICOM
        assoc.release()
    else:
        print("Não foi possível estabelecer a associação com o servidor de Worklist.")
except Exception as e:
    print(f"Erro ao tentar estabelecer a associação: {str(e)}")

# Loop simples para manter o programa rodando
op = 0
while op == 0:
    op = input("Digite 1 para sair\n")
