import unittest
import os
from module_cognitive_treelogic.PDF2Table import ProcessExtractTable
from module_cognitive_treelogic.ExtractXML import ProcessExtractXml
from module_cognitive_treelogic.WebScrapping import WebScrapping


class Tests(unittest.TestCase):

    def test_extract_xml(self):
        parameters = {'url':'https://boe.es/diario_boe/xml.php?id=BOE-S-20220701', 'filename':'dest/xml/indexBOE-S-20220701.xml'}
        psm = ProcessExtractXml(parameters)
        psm.traer_documento(parameters['url'], parameters['filename'])
        secciones = psm.obtener_diccionario(parameters['filename'], 'seccion', 'nombre', ['departamento'])
        departamentos = psm.obtener_diccionario(parameters['filename'], 'departamento', 'nombre', ['item'])
        items = psm.obtener_diccionario(parameters['filename'], 'item', 'id', ['titulo', 'urlPdf'])
        if os.path.exists(parameters['filename']):
            os.remove(parameters['filename'])
        self.assertEqual(len(secciones), 6)
        self.assertEqual(len(departamentos), 28)
        self.assertEqual(len(items), 145)

    def test_pdf2table(self):
        parameters_pdf = {}
        parameters_pdf['files'] = []
        parameters_pdf['excel'] = False
        parameters_pdf['files'].append({'path':'test_files/525644_Resolucion_Concesion_PREDOC2020_firmada.pdf','page':'19,50,51'})
        p = ProcessExtractTable(parameters_pdf)
        self.assertEqual(len(p.execute()),1)

    def test_extract_convocatoria_info(self):
        bdns = WebScrapping()
        result = bdns.obtain_data_bdns_file("test_files/525644.html")
        self.assertEqual(result["Órgano convocante"], "ESTADO") 
        self.assertEqual(result["Sede electrónica para la presentación de solicitudes"], "https://ciencia.sede.gob.es") 
        self.assertEqual(result["Código BDNS"], "525644") 
        self.assertEqual(result["Mecanismo de Recuperación y Resiliencia"], "NO") 
        self.assertEqual(result["Fecha de registro"], "28/09/2020") 
        self.assertEqual(result["Instrumento de ayuda"], "SUBVENCIÓN Y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN ") 
        self.assertEqual(result["Tipo de convocatoria"], "Concurrencia competitiva - canónica") 
        #self.assertEqual(result["Presupuesto total de la convocatoria"], "108,954,960.00 €") 
        #self.assertEqual(result["Título de la convocatoria en español"], "Resolución de 30 de septiembre de 2020, de la Presidencia de la Agencia Estatal de Investigación, por la que se aprueba la convocatoria 2020 de ayudas para contratos predoctorales en el marco del Plan Estatal de I+D+i 2017-2020..") 
        self.assertEqual(result["Título de la convocatoria en otra lengua cooficial"], ".") 
        self.assertEqual(result["Tipo de beneficiario elegible"], "PERSONAS JURÍDICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA") 
        self.assertEqual(result["Sector económico del beneficiario"], "ACTIVIDADES PROFESIONALES, CIENTÍFICAS Y TÉCNICAS") 
        self.assertEqual(result["Región de impacto"], "ES - ESPAÑA ") 
        self.assertEqual(result["Finalidad (política de gasto)"], "INVESTIGACIÓN, DESARROLLO E INNOVACIÓN") 
        #self.assertEqual(result["Título de las Bases reguladoras"], "Orden CNU/692/2019, de 20 de junio, por la que se aprueban las bases reguladoras para la concesión de ayudas en el marco del Programa de Promoción del Talento y su Empleabilidad en I+D+i del Plan Estatal de I+D+i 2017-2020")
        self.assertEqual(result["Dirección electrónica de las bases reguladoras"], "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2019-9533")
        self.assertEqual(result["¿El extracto de la convocatoria se publica en diario oficial?"], "Sí") 
        self.assertEqual(result["¿Se puede solicitar indefinidamente?"], "No") 
        self.assertEqual(result["Fecha de inicio del periodo de solicitud"], "13/10/2020") 
        self.assertEqual(result["Fecha de finalización del periodo de solicitud"], "27/10/2020") 
        self.assertEqual(result["SA Number (Referencia de ayuda de estado)"], "") 
        self.assertEqual(result["Cofinanciado con Fondos UE"], "FSE - FONDO SOCIAL EUROPEO ") 
        self.assertEqual(result["Reglamento (UE)"], "") 
        self.assertEqual(result["Sector de productos"], "")
        
if __name__ == '__main__':
    unittest.main()     