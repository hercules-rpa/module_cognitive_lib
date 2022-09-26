from pathlib import Path
import requests, os
import xml.dom.minidom


class InfoResult:
    def __init__(self, treated_nodes, sons):
        self.treated_nodes = treated_nodes
        self.sons = sons

class ProcessExtractXml():
    def __init__(self, parameters):
        self.parameters = parameters

    def get_document(self, source, to):
        """
        Método que descarga un documento seleccionado y lo guarda en el destino.
        :param source nombre origen del documento
        :param to ruta donde almacenar el documento
        :return int código de estado de la petición
        """
        if source and to:
            file = requests.get(source, allow_redirects=True)

            dirname = os.path.dirname(to)
            if not os.path.exists(dirname):
                path = Path(dirname)
                path.mkdir(parents=True)

            if os.path.exists(to):
                os.remove(to)
            
            with open(to, 'wb') as f:
                f.write(file.content)

            return file.status_code
        return 404

    def get_childs(self, child:dict, origin, nparetn) -> InfoResult:
        """
        Método que obtiene los nodos hijos de un nodo raiz
        :param child lista de nodos a obtener
        :param origin nodo raiz
        :param nparetn nombre del nodo padre
        :return InfoResult entidad que almacena los datos obtenidos
        """
        result = []
        treated = []
        if child:
            sons = child[origin]
            treated.append(origin)
            if sons:
                for son in sons:
                    nson = nparetn.getElementsByTagName(son)
                    if son in child:
                        info = self.get_childs(child, son, nson)
                        result = result + info.hijos
                        treated.append(info.nodes_treated)
                    else:
                        result.append((nson, []))
        
        return InfoResult(treated, result)
    
    def get_dictionary(self, filename:str, rootname:str, atribname:str, childsname:list):
        """
        Método que crea un diccionario que almacena los nodos raiz y nodos hijos obtenidos
        :param filename ruta del fichero XML a analizar
        :param rootname nombre del nodo raiz
        :param atribname nombre del atributo que se desea obtener del nodo
        :param childsname lista de nombre de los nodos hijos a obtener
        :return dict diccionario con los datos obtenidos
        """
        result =  {}
        if rootname and childsname:
            mydoc = xml.dom.minidom.parse(filename)
            collection = mydoc.documentElement  # -> Objeto raíz
            if collection.localName != 'error':
                parent_nodes = collection.getElementsByTagName(rootname)
                for root in parent_nodes:
                    childs = []
                    if childsname:
                        for child in childsname:
                            childs += root.getElementsByTagName(child)
                    
                    result.setdefault(root.attributes[atribname].value, childs)
                    #result[root.attributes[atribname].value] = childs
        return result 

    def get_nodes(self, nodes:dict, filename:str):
        """
        Método encargado de obtener nodos de un fichero XML
        :param nodes diccionario de nodos
        :param filename nombre de fichero XML
        :return lista de nodos
        """
        count = 0
        result = []
        if nodes:
            treated_nodes = []
            keys = nodes.keys()
            mydoc = xml.dom.minidom.parse(filename)
            collection = mydoc.documentElement  # -> Objeto raíz
            if collection.localName != 'error':
                # Obtiene una lista de los objetos con la etiqueta padre
                for key in keys:
                    if key not in treated_nodes:
                        parent_nodes = collection.getElementsByTagName(key)
                        if parent_nodes:
                            for nparent in parent_nodes: 
                                count+=1
                                infoSons:InfoResult = self.get_childs(nodes, key, nparent)
                                if infoSons:
                                    if infoSons.treated_nodes:
                                        treated_nodes = treated_nodes + infoSons.treated_nodes
                                    if infoSons.sons:
                                        result.append((nparent, infoSons.sons))

        return result                                               