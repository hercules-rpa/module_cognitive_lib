
from SPARQLWrapper import SPARQLWrapper, JSON
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
from nltk.corpus import stopwords
from gensim.models import Word2Vec
from umap import UMAP
import copy
import json
import os
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import hdbscan
import nltk
nltk.download('stopwords')



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
    
    #Limpiamos los tags y quitamos los stopwords
    df_processing['tag'] = df_processing['tag'].str.lower()
    df_processing['tag'] = df_processing['tag'].str.replace('[^a-zA-Z]',' ',regex=True)
    df_processing['tag'] = df_processing['tag'].apply(lambda x: ' '.join([word for word in x.split() if word not in stopwords.words('english') and word not in stopwords.words('spanish')]))
    df_processing['nombrecategoria'] = df_processing['nombrecategoria'].str.lower()
    df_processing['nombrecategoria'] = df_processing['nombrecategoria'].str.replace('[^a-zA-Z]',' ',regex=True)
    df_processing['nombrecategoria'] = df_processing['nombrecategoria'].apply(lambda x: ' '.join([word for word in x.split() if word not in stopwords.words('english') and word not in stopwords.words('spanish')]))
    
    #Combinamos Categoria y Tags para mayor vocabulario
    df_processing['combine'] = df_processing.values.tolist()
    df_processing['combine'] = df_processing[['tag','nombrecategoria']].values.tolist()
    dictionary_nlp = df_processing['combine'].tolist()
    #Generamos el vocabulario y vectorizamos las palabras (NLP)
    model = Word2Vec(dictionary_nlp, min_count=3)
    
    #print(model.wv['sdn'])
    return df_processing, model

def load_model():
    '''Load model UMAP nad HDB CLUSTER'''
    global dataframe, model
    df_processing, model = __load_data()
    #Volcamos la informacion del modelo para pasarle UMAP
    data_dict = []
    for i in range(0, len(model.wv)): 
        data_dict.append(model.wv[model.wv.index_to_key[i]])

    #Cargamos la libreria UMAP (machine learning)
    u = UMAP(n_neighbors=15, target_metric= 11)
    projection = u.fit_transform(data_dict)
    
    #Añadimos al dataframe los vectores generados a traves de las palabras
    df_processing['vector_word'] = df_processing['tag'].apply(lambda x: projection[model.wv.key_to_index[x]] if x in model.wv else None) #En vez de coger los valores del model, cogemos los valores de UMAP, ya que ha reducido la dimensión
    df_processing['similarity'] = df_processing['tag'].apply(lambda x: model.wv.most_similar(x) if x in model.wv else None)
    #Eliminamos las filas donde hay nulos
    df_processing = df_processing.dropna(axis=0)
    df_processing['similarity'] = df_processing['similarity'].apply(lambda x: [ projection[model.wv.key_to_index[word[0]]] for word in x])

    
    df_process_cluster = pd.DataFrame()
    df_process_cluster[['vector_word_1','vector_word_2']] = pd.DataFrame(df_processing.vector_word.tolist(), index= df_processing.index)
    np_similarity = np.array(df_processing.similarity.tolist())
    np_similarity = np_similarity.reshape((len(df_processing), 10*np_similarity.shape[2]))
    df_process_cluster = pd.concat([df_process_cluster, pd.DataFrame(np_similarity)], axis=1, join='inner')
    #Generamos los clusters
    clusterer = hdbscan.HDBSCAN(min_cluster_size=15, gen_min_span_tree=True)
    clusterer.fit(df_process_cluster)
    
    labels = clusterer.labels_
    hdb_cluster = pd.DataFrame(labels)
    # n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    # print('Estimated number of clusters: %d' % n_clusters_)
    df_cluster = pd.concat([df_processing, hdb_cluster], axis=1, join='inner')
    df_cluster.columns = ['tag','nombrecategoria', 'email', 'combine','vector_word', 'similarity', 'hdb_cluster']
    dataframe = df_cluster
    

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