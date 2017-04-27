import os
import csv
import xml.etree.cElementTree as ET
from num2words import num2words #para converter numeros para extenso
import sqlite3
from collections import OrderedDict

#Leitura do arquivo
print('Carregando dados')
osm_file = ET.parse('map.osm')
root = osm_file.getroot()
print('Dados carregados \n')

'''
Alguns endereços no XML contém números escritos com dígitos (ex.: 42), enquanto outros são escritos por extenso.
A fim de padronizar os dados e atingir uma melhor qualidade dos mesmos, irei converter todos os números para sua versão
extendida. Por exemplo, 42 se tornaria 'Quarenta e Dois'.
'''
def numero_em_extenso():
    print('INICIANDO PROCESSO DE CONVERSÃO DE NÚMEROS')
    for elem in root.iter('tag'):
        if elem.attrib['k'] == 'addr:street' and any(char.isdigit() for char in elem.attrib['v']):            
            for palavra in elem.attrib['v'].split():
                try:
                    elem.attrib['v'] = elem.attrib['v'].replace(palavra, num2words(int(palavra), lang='pt_BR').capitalize())
                except:
                    pass
    print('ROTINA DE CONVERSÃO DE NÚMEROS FINALIZADA\n')

'''
Alguns CEPs do mapas estão configurados incorretamente. Alguns não possuem o caracter "-" antes dos três últimos digitos. 
A função "verifa_cep" irá procurar por endereços cujo o CEP não possuem dígito, CEPs que não possuem o tamanho correto (8 dígitos) ou que não 
estão cadastrados na tabela de CEP.
'''
def verifica_cep():
    print('REALIZANDO LIMPEZA DE CEPs')
    for elem in root.iter('tag'):
        if elem.attrib['k'] == 'addr:postcode':
            #CEP sem dígito e com tamanho menor que 8
            if not '-' in elem.attrib['v'] and len(elem.attrib['v']) != 8:
                #Verificando quantos caracteres faltam para completar oito dígitos
                caracteres_faltando = 8 - len(elem.attrib['v'])
                #Corrigindo CEP
                elem.attrib['v'] = '{}{}{}'.format(elem.attrib['v'][0:5], '-', elem.attrib['v'][5:] + '0' * caracteres_faltando)

            #CEP com dígito, mas menor que 9
            elif '-' in elem.attrib['v'] and len(elem.attrib['v']) != 9:                
                #Retirando dígito
                elem.attrib['v'] = elem.attrib['v'].replace('-', '')
                #Verificando quantos caracteres faltam para completar oito dígitos
                caracteres_faltando = 8 - len(elem.attrib['v'])
                #Corrigindo CEP
                elem.attrib['v'] = '{}{}{}'.format(elem.attrib['v'][0:5],'-', elem.attrib['v'][5:] + '0' * caracteres_faltando)                

            #CEP sem dígito verificador
            elif not '-' in elem.attrib['v']:                
                #Verificando quantos caracteres faltam para completar oito dígitos
                caracteres_faltando = 8 - len(elem.attrib['v'])
                #Corrigindo CEP
                elem.attrib['v'] = '{}{}{}'.format(elem.attrib['v'][0:5],'-', elem.attrib['v'][5:] + '0' * caracteres_faltando)                
    print('REALIZANDO LIMPEZA DE CEPs\n')
'''
Alguns tipos de logradouros estão sendo informados de diferentes formas no mapa. Algumas ruas, por exemplo, são encontrados com caracteres 
indevidos. A função corrige_endereco irá percorrer todas esses endereços e irá corrigir as que estiverem configuradas de forma indevida.
'''
def corrige_endereco():
    print('INICIANDO PROCESSO DE CORREÇÃO DE ENDEREÇOS')
    enderecos_estranhos = {'r': 'Rua',
                           'rua': 'Rua',
                           'r.': 'Rua',
                           'est.': 'Estrada',
                           'est': 'Estrada',
                           'av': 'Avenida',
                           'ave.': 'Avenida',
                           'av.': 'Avenida',
                           'rod': 'Rodovia',
                           'rod.': 'Rodovia'
                           }

    for elem in root.iter('tag'):
        #Verifica se o endereço no iterador é estranho
        if elem.attrib['k'] == 'addr:street' and elem.attrib['v'].split()[0].lower() in enderecos_estranhos.keys():
            logradouro = elem.attrib['v'].split()[0]
            elem.attrib['v'] = elem.attrib['v'].replace(logradouro, enderecos_estranhos[logradouro.lower()], 1)            
        #Se o endereço não for estranho, ele apenas irá colocar a primeira letra como maiúscula
        elif elem.attrib['k'] == 'addr:street' and not elem.attrib['v'].split()[0].lower() in enderecos_estranhos.keys():
            elem.attrib['v'] = elem.attrib['v'].capitalize()
    print('PROCESSO DE CORREÇÃO FINALIZADO\n')


'''
Alguns números de telefones estão configurados incorretamente no mapa. Para resolver esse problema, estarei usando a função limpa_telefone,
que removerá caracteres inválidos e reorganizará os dados apropriadamente.
'''
def limpa_telefone():
    print('LIMPANDO NÚMEROS DE TELEFONES')
    for elem in root.iter('tag'):
        #Removendo +55 e '-' do número do telefone:
        if elem.attrib['k'] == 'phone': 
            #Verificando se há +55 no número do telefone
            if '+55' in elem.attrib['v'].replace(' ',''):
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace('+55','', 1)
            #Verificando se há 55 no começo do número do telefone
            if '55' in elem.attrib['v'].replace(' ','')[:3]:
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace('55','', 1)
            #Verificando se há hífen no número do telefone
            if '-' in elem.attrib['v']:
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace('-', '')
            #Buscando por parenteses
            if '(' in elem.attrib['v'] or ')' in elem.attrib['v']:
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace('(', '')
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace(')', '')
            #Formatando número do telefone
            if not '0800' in elem.attrib['v'][:4]:
                elem.attrib['v'] = '{} {}-{}'.format(elem.attrib['v'][:2], elem.attrib['v'][2:6], elem.attrib['v'][6:10])            
    print('ROTINA CONCLUÍDA\n') 


'''
A função crie_tabelas oferecerá uma facilidade ao usuário ao construir as tabelas de seu banco de dados. Como as tabelas são padrões 
encontrados em qualquer arquivo do OpenStreetMap, a função economizará tempo no momento de criar seu ambiente.
'''
def cria_tabelas():
    print('CRIANDO TABELAS NO BANCO DE DADOS')
    try:
        #Criando tabela nodes
        cursor.execute('''CREATE TABLE nodes (
            id INTEGER PRIMARY KEY NOT NULL,
            lat REAL,
            lon REAL,
            user TEXT,
            uid INTEGER,
            version INTEGER,
            changeset INTEGER,
            timestamp TEXT);''')

        #Criando tabela nodes_tags
        cursor.execute('''CREATE TABLE nodes_tags (
            id INTEGER,
            key TEXT,
            value TEXT,
            type TEXT,
            FOREIGN KEY (id) REFERENCES nodes(id));''')

        #Criando tabela ways
        cursor.execute('''CREATE TABLE ways (
            id INTEGER PRIMARY KEY NOT NULL,
            user TEXT,
            uid INTEGER,
            version TEXT,
            changeset INTEGER,
            timestamp TEXT
        );''')

        #Criando tabela ways_tags
        cursor.execute('''CREATE TABLE ways_tags (
            id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            type TEXT,
            FOREIGN KEY (id) REFERENCES ways(id)
        );''')

        #Criando tabela ways_nodes
        cursor.execute('''CREATE TABLE ways_nodes (
            id INTEGER NOT NULL,
            node_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            FOREIGN KEY (id) REFERENCES ways(id),
            FOREIGN KEY (node_id) REFERENCES nodes(id)
        );''')
    except:
        print('OCORREU UM ERRO DURANTE O PROCESSO. VERIFIQUE SE AS TABELAS JÁ EXISTEM NO BANCO DE DADOS\n')
    print('TABELAS CRIADAS\n')



'''
A função cria_dados irá realizar uma iteração dentro do arquivo osm. Para cada tag encontrada nos elementos, um dicionário será criado, 
retornando ao final uma lista de dicionários para tags nodes e ways
'''
def cria_dados():

    schema = {'nodes': [],
          'nodes_tags': [],
          'ways': [],
          'ways_nodes': [],
          'ways_tags': []}
    
    #Criando dados para node    
    print('COLETANDO DADOS DO ARQUIVO')
    for elem in root.iter():        
        if elem.tag == 'node':
            #Atributos necessários para o database
            atributos = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
            dados_node = OrderedDict()            
            for atributo in atributos:
                dados_node[atributo] = elem.attrib[atributo]
            schema['nodes'].append(dados_node)
            
            #Verifica se existe a tag TAG dentro do nó antes de prosseguir.
            if elem.find('tag') != None:                
                for tag in elem.iter('tag'):
                    dados_node_tag = OrderedDict()
                    dados_node_tag['id'] = elem.attrib['id']
                    dados_node_tag['key'] = tag.attrib['k']
                    dados_node_tag['value'] = tag.attrib['v']                
                    schema['nodes_tags'].append(dados_node_tag)
        
        #Criando dados para way
        elif elem.tag == 'way':
            atributos = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
            dados_way = OrderedDict()
            for atributo in atributos:
                dados_way[atributo] = elem.attrib[atributo]
            schema['ways'].append(dados_way)

            #Para cada tag encontrada no elemento way, haverá uma iteração e um dicionário criado ao final do processo
            posicao_node = int()
            for tag in elem.iter('nd'):
                dados_way_node_tags = OrderedDict()
                dados_way_node_tags['id'] = elem.attrib['id']
                dados_way_node_tags['node_id'] = tag.attrib['ref']
                dados_way_node_tags['position'] = posicao_node
                posicao_node += 1
                schema['ways_nodes'].append(dados_way_node_tags)

            for tag in elem.iter('tag'):
                dados_ways_tags = OrderedDict()
                dados_ways_tags['id'] = elem.attrib['id']
                dados_ways_tags['key'] = tag.attrib['k']
                dados_ways_tags['value'] = tag.attrib['v']
                schema['ways_tags'].append(dados_ways_tags)
    print('DADOS COLETADOS COM SUCESSO\n')
    return schema
'''
A função importa_dados usará um argumento chamado arquivo para identificar qual tabela deverá ser importada para o banco de dados.
A função cria_dados() precisa já ter sido realizada, ou os arquivos .csv precisam estar de antemão na pasta db.
'''
def importa_dados(arquivo):
    caminho = os.path.abspath(os.path.dirname(__file__))
    print('IMPORTANDO TABELA {}\n'.format(arquivo))

    #Importando dados da tabela nodes
    if arquivo == 'nodes':        
        with open(caminho + '/db/{}.csv'.format(arquivo), 'r') as filename:
            csv_file = csv.reader(filename)
            for linha in csv_file:
                if len(linha) == 8:
                    try:
                        cursor.execute("INSERT INTO nodes VALUES ({}, {}, {}, '{}', {}, {}, {}, '{}');".format(linha[0], linha[1], linha[2], linha[3], linha[4], linha[5], linha[6], linha[7]))
                    except:
                        pass
    
    #Importando dados da tabela nodes_tags
    elif arquivo == 'nodes_tags':
        with open(caminho + '/db/{}.csv'.format(arquivo), 'r') as filename:
            csv_file = csv.reader(filename)
            for linha in csv_file:
                if len(linha) == 3:
                    try:
                        cursor.execute("INSERT INTO nodes_tags (id, key, value) VALUES ({}, '{}', '{}');".format(linha[0], linha[1], linha[2]))
                    except:
                        pass

    #Importando dados da tabela ways
    elif arquivo == 'ways':
        with open(caminho + '/db/{}.csv'.format(arquivo), 'r') as filename:
            csv_file = csv.reader(filename)
            for linha in csv_file:
                if len(linha) == 6:
                    try:
                        cursor.execute("INSERT INTO ways VALUES ({}, '{}', {}, '{}', {}, '{}');".format(linha[0], linha[1], linha[2], linha[3], linha[4], linha[5]))
                    except:
                        pass
    
    #Importando dados da tabela ways_tags
    elif arquivo == 'ways_tags':
        with open(caminho + '/db/{}.csv'.format(arquivo), 'r') as filename:
            csv_file = csv.reader(filename)
            for linha in csv_file:
                if len(linha) == 3:
                    try:
                        cursor.execute("INSERT INTO ways_tags (id, key, value) VALUES ({}, '{}', '{}');".format(linha[0], linha[1], linha[2]))
                    except:
                        pass
    #Importando dados da tabela ways_nodes
    elif arquivo == 'ways_nodes':
        with open(caminho + '/db/{}.csv'.format(arquivo), 'r') as filename:
            csv_file = csv.reader(filename)
            for linha in csv_file:
                if len(linha) == 3:
                    try:
                        cursor.execute("INSERT INTO ways_nodes VALUES ({}, {}, {});".format(linha[0], linha[1], linha[2]))
                    except:
                        pass

    db.commit()    
    print('ROTINA CONCLUÍDA\n')


#Executando as quatro funções para limpeza dos dados
numero_em_extenso()
verifica_cep()
corrige_endereco()
limpa_telefone()

#Conectando-se a base
db = sqlite3.connect('C:\sqlite\Araruama.db')
cursor = db.cursor()

#Criando tabelas do banco de dados
cria_tabelas()

#Criando um arquivo para cada tipo de tag
schemas = cria_dados()
for chave in schemas.keys():
    #Arquivo será salvo na pasta db do diretório em que o script está
    caminho = os.path.abspath(os.path.dirname(__file__))
    print('CRIANDO ARQUIVO {}\n'.format(chave))

    with open(caminho + '/db/{}.csv'.format(chave), 'w', encoding='iso-8859-1') as arquivo:        
        writer = csv.writer(arquivo, delimiter=',')
        #Escrevendo cabeçalho
        writer.writerow(schemas[chave][0].keys())
        #Gravando dados
        for dicionario in schemas[chave][:]:
            try:
                writer.writerow(dicionario.values())
            except:
                pass        

#Importando dados para o banco
importa_dados('nodes')
importa_dados('nodes_tags')
importa_dados('ways')
importa_dados('ways_tags')
importa_dados('ways_nodes')

#Fechando base de dados
db.close()

print('SCRIPT EXECUTADO COM SUCESSO')