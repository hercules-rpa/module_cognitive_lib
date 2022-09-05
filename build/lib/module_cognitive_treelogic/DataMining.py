from SPARQLWrapper import SPARQLWrapper, JSON
import json
import os
import pandas as pd
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from umap import UMAP
import hdbscan
from sklearn.preprocessing import LabelEncoder


le_category = LabelEncoder()
le_email = LabelEncoder()
le_tag = LabelEncoder()
dataframe = None

def __load_data():
    sparql = SPARQLWrapper("http://edma.gnoss.com:8890/sparql",)

    #--- Nombre |email|descriptor/tag | num_apariciones ---
    sparql.setQuery("""
        
    select ?person ?tag ?nombrePersona ?email count(distinct ?doc) as ?num from <http://gnoss.com/document.owl> from <http://gnoss.com/person.owl> from <http://gnoss.com/taxonomy.owl> where {
    ?doc a <http://purl.org/ontology/bibo/Document>.
    ?doc <http://purl.org/ontology/bibo/authorList> ?autor.
    ?autor <http://www.w3.org/1999/02/22-rdf-syntax-ns#member> ?person.
    ?person <http://xmlns.com/foaf/0.1/name> ?nombrePersona.
    ?person <https://www.w3.org/2006/vcard/ns#email> ?email.
    ?doc <http://vivoweb.org/ontology/core#freeTextKeyword> ?tag.
    }order by desc(?num)
    """)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(5)
    """
    --- Nombre |email| categoria/area_tematica | num_apariciones ---
    select ?person ?nombrecategoria ?nombrePersona ?email count(distinct ?doc) as ?num from <http://gnoss.com/document.owl> from <http://gnoss.com/person.owl> from <http://gnoss.com/taxonomy.owl> where {
    ?doc a <http://purl.org/ontology/bibo/Document>.
    ?doc <http://purl.org/ontology/bibo/authorList> ?autor.
    ?autor <http://www.w3.org/1999/02/22-rdf-syntax-ns#member> ?person.
    ?person <http://xmlns.com/foaf/0.1/name> ?nombrePersona.
    ?person <https://www.w3.org/2006/vcard/ns#email> ?email.
    ?doc <http://w3id.org/roh/hasKnowledgeArea> ?area.
    ?area <http://w3id.org/roh/categoryNode> ?nodo.
    ?nodo <http://www.w3.org/2008/05/skos#prefLabel> ?nombrecategoria.
    }order by desc(?num)
    """
    #Extraeremos el area tematica con la API de esta forma podremos relacionarlos con las areas tematicas que hay 
    #en la odontologia, ya que son distintas a las del SGI.
    try:
        results = ""
        results = sparql.query().convert()
    except:
        parentdir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),os.pardir))
        with open(parentdir + '/test_files/datos2detalle.json') as json_file:
            data = json.load(json_file)
    if results:
        df = pd.DataFrame.from_dict(results)
    else:
        df = pd.DataFrame.from_dict(data)
    df_processing = df
    df_processing = df_processing.drop('person',1)
    df_processing = df_processing.drop('nombrepersona',1)
    df_processing = df_processing.drop('num',1)
    #print(df_processing.head())
    df_processing.nombrecategoria = le_category.fit_transform(df_processing.nombrecategoria) #Vectorizamos las palabras
    df_processing.email = le_email.fit_transform(df_processing.email) #Vectorizamos las palabras
    df_processing.tag = le_tag.fit_transform(df_processing.tag) #Vectorizamos las palabras
    return df_processing

def load_model():
    '''Load model UMAP nad HDB CLUSTER'''
    global dataframe
    df_processing = __load_data()
    #Cargamos la libreria
    u = UMAP()
    projection = u.fit_transform(df_processing)
    clusterer = hdbscan.HDBSCAN(min_cluster_size=15, gen_min_span_tree=True)
    clusterer.fit(projection)
    labels = clusterer.labels_
    hdb_cluster = pd.DataFrame(labels)  
    df_final = pd.concat([df_processing, hdb_cluster], axis=1)
    df_final.columns = ['tag','nombrecategoria', 'email', 'hdb_cluster']
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    #print('Estimated number of clusters: %d' % n_clusters_)
    dataframe = df_final
    #Revertimos la vectorizacion
    dataframe.email = le_email.inverse_transform(dataframe.email)
    dataframe.nombrecategoria = le_category.inverse_transform(dataframe.nombrecategoria)
    dataframe.tag = le_tag.inverse_transform(dataframe.tag)

def get_all_cluster():
    '''Return dataframe generated with clustering'''
    if dataframe is None:
        return None
    return dataframe

def get_all_categories():
    '''Return all categories'''
    if dataframe is None:
        return None
    return list(set(dataframe['nombrecategoria'].to_list()))

def get_all_tag():
    '''Return all tag'''
    if dataframe is None:
        return None
    return list(set(dataframe['tag'].to_list()))

def get_categories_interest_research(email: str):
    '''Return all categories where research is in'''
    if dataframe is None:
        return None
    return list(set(dataframe.loc[dataframe.email == email]['nombrecategoria'].to_list()))

def get_tags_interest_research(email: str):
    '''Return all tags where research is in'''
    if dataframe is None:
        return None
    return list(set(dataframe.loc[dataframe.email == email]['tag'].to_list()))

def get_research_clusters(email: str):
    '''Return all cluster where research is in'''
    if dataframe is None:
        return None
    return list(set(dataframe.loc[dataframe.email == email]['hdb_cluster'].to_list()))

def get_research_relation(email: str):
    '''Return all relation where research is in'''
    if dataframe is None:
        return None
    clusters = get_research_clusters(email)
    relation_set = set(dataframe[dataframe['hdb_cluster'].isin(clusters)]['email'].to_list())
    relation_set.remove(email) #eliminamos al investigador que usamos para buscar sus relaciones.
    return list(relation_set)

def get_research_tag(tags: list):
    '''Return all emails for tags'''
    if dataframe is None:
        return None
    researchs_set = set(dataframe[dataframe['tag'].isin(tags)]['email'].to_list())
    return list(researchs_set)

def get_research_category(categories: list):
    '''Return all emails for categories'''
    if dataframe is None:
        return None
    researchs_set = set(dataframe[dataframe['nombrecategoria'].isin(categories)]['email'].to_list())
    return list(researchs_set)

def get_research_category_tag(tags: list, categories: list):
    '''Return all emails for tags and categories'''
    df_tags = dataframe[dataframe['tag'].isin(tags)]
    df_categories = dataframe[dataframe['nombrecategoria'].isin(categories)]
    df = df_tags.merge(df_categories, how='inner',on='email')
    return list(set(df['email'].to_list()))

"""
load_model()
print(get_all_tag())
print(get_research_tag(['Internet of Things','IoT','security']))
print(get_research_category(['Physical Sciences','Computer Science']))
print(get_research_category_tag(['Internet of Things','IoT','security'],['Physical Sciences','Computer Science']))
"""