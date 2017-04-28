# Limpeza de dados do OpenStreetMap

### Dados de localização

Este projeto tem como objetivo documentar o processo de limpeza de dados do OpenStreetMap. Além das dificuldades encontradas para alcançar tal objetivo, viso através deste documento salientar as ações realizadas para garantir a validade, a precisão, a completude, consistência e uniformidade dos dados do OpenStreetMap.

Utilizei de um mapa de uma área do Rio de Janeiro, cobrindo em sua totalidade toda a localidade chamada de Região dos Lagos, onde moro atualmente.

Rio de Janeiro, Brasil 
- [https://www.openstreetmap.org/export#map=9/-22.7091/-42.4841]


## Desafios encontrados

Os dados encontrados no OpenStreetMap são gerados por seus próprios usuários, seja através da api do Google ou de submissões na plataforma. Devido a esse fato, tais dados podem sofrer diferentes problemas, desde sua formatação incorreta, erros de grafia ou falta de padronização de dados. Após uma breve análise do arquivo XML, os principais problemas encontrados no mapa foram:

* **Números de telefone preenchidos sem um padrão**:
    Muitos dados são gravados sem a utilização de uma máscara padrão para os números. Alguns usuários colocam o prefixo do país (*+55*), enquanto outros não; há também ocorrência onde o usuário coloca ou não *"-"* dividindo o número; além de situações onde é utilizado parênteses para encapsular o DDD.

    Para resolver esse problema criei uma função em Python que formata e limpa esse dado, de forma que encapsule o DDD entre parênteses, e que separe o número por dígitos (*-*):

    ```python
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
    ```
* **Logradouros informados incorretamente**:
    Há ocorrência de muitos endereços com nomes abreviados na `tag[k: addr:street]`, como *av* para *Avenida* e *est.* para *Estrada*, dentre outros. A função realizou uma iteração por todas as tags do arquivo e procura de valores incorretos para correção.

    *Exemplo de dados encontrados*:
    ```XML
    <tag k="addr:street" v="av Costa Azul"/>
    <tag k="addr:street" v="av Amazonas"/>
    <tag k="addr:street" v="Est. Profº Leandro Faria Sarzedas"/>

    ```

* **CEPs indevidos**:
    Assim como os números de telefone, códigos de CEP são informados sem uma máscara que facilitaria a leitura. Utilizando a função `verifica_cep()`,eu realizo a limpeza desses dados e adiciono o dígito *-* para separar os três últimos números.

    *Diferentes tipos de CEP encontrados*:
    ```XML
    <tag k="postal_code" v="25900213"/>
    <tag k="postal_code" v="24030-128"/>    
    ```

* **Números inteiros e por extenso**:
    Em alguns casos pude perceber que quando há um número no endereço da `<tag k="addr:street"...>` ele surge de duas formas: em sua foram inteira (*1, 10, 42*); e por extenso (*Um, Dez, Quarenta e Dois*). Para alinhar esses dados e criar um padrão de preechimento, eu desenvolvi a função `numero_em_extenso()`, que passa por todo o arquivo procurando por números nos endereços dos nodes.

# Geração e importação dos dados

Todo o processo de geração e importação dos dados foi feita de forma programática. Durante a concepção do código, me vi na seguinte incógnita: insiro os dados diretamente no banco através do *script*, ou gero arquivos .csv para importação?

Decidi, por fim, fazer os dois. O *script* realiza através da função `importa_dados()` a importação de todos os dados para cada tabela do banco de dados. Não obstante, também gerei arquivos .csv utilizando a função `cria_dados()`, a fim de facilitar a importação por pessoas que se interessem pelos dados. Imagine, por exemplo, que um interessado possui um ambiente SQL configurado em seu computador, mas não dispõe de instalação Python ou de suas bibliotecas. Os arquivos .csv economizaram uma quantidade exponencial de tempo.

Além disso, o script também cria todo o schema de tabelas no banco de dados utilizando a função `cria_tabelas()`, sempre levando em consideração a praticidade para aqueles que dispõe de todos os *dependencies* em seu ambiente de trabalho.

## Tamanho dos dados

Abaixo você pode conferir informações sobre todos os arquivos convenientes disponíveis neste repositório:

```
mapa.osm (comprimido) -------------------------  10.2 MB
mapa.osm (descomprimido) ---------------------- 133.9 MB
Araruama.db -----------------------------------  68.9 MB
nodes.csv -------------------------------------  54.4 MB
nodes_tags.csv --------------------------------   582 KB
ways.csv --------------------------------------   3.5 MB
ways_nodes.csv --------------------------------  18.7 MB
ways_tags.csv ---------------------------------   3.5 MB
```

# Consulta de dados

### Quantidade total de nós (*nodes*)

```SQL
select count(*) as Total from nodes
```

```
Total
636891
```

### Quantidade total de caminhos (*ways*)

```SQL
select count(*) as Total from ways
```

```
Total
57822
```

### Número de usuários únicos

```SQL
select COUNT(DISTINCT uid) as Contagem from ways
``` 

```
Contagem
364
```

### Usuários que mais contribuiram

```SQL
select user as Usuario, count(uid) as Contribuicoes from ways
group by usuario
order by Contribuicoes DESC
limit 10
```

```
Thundercel          | 11169
Alexandrecw         |  9185
Helio Coutinho      |  8594
felipeacsi          |  2701
ftrebien            |  1882
Skippern            |  1821
Ricardo Mitidieri   |  1512
Wallace Silva       |  1403
patodiez            |  1213
ThiagoPv            |  1210
```

## Quantidade de acessos a cadeira de rodas

```SQL
select count(*) as Acessos_cadeira_de_rodas from nodes_tags
where key = 'wheelchair'
AND value = 'yes'
or value = 'limited'
```

```
Acessos_cadeira_de_rodas
22
```

## Top 3 tipos de lugares encontrados no mapa
```SQL
select value, count(*) as Total
FROM (select * from ways_tags
where key = 'place') lugares
group by value
order by Total DESC
limit 3
```

```
city_block  |	71
islet       |	68
island      |	24
```