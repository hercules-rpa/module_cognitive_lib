from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

import time
import requests
import csv,json


class WebScrapping:

    def search_with_date_BDNS(self, dD: time, dH: time, *args: str) -> None:
        """
        Método para buscar, por fecha, convocatorias. Las convocatorias, adicionalmente, se guardan en un archivo CSV.

        :param dD time: Objeto time con la fecha inicial para la búsqueda.
        :param dH time: Objeto time con la fecha final para la búsqueda.
        :param args str: Argumento variable con las palabras clave para la búsqueda.
        :return dict con los datos de las convocatorias que cumplen los criterios de la búsqueda.
        """
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context(accept_downloads=True)

            page = context.new_page()
            page.goto(
                "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias")
            page.click("input[name=\"titulo\"]")
            if len(args) == 1:
                args = args[0].split()
                #page.locator("select[name=\"tipoBusqPalab\"]").select_option("2")
                #page.fill("input[name=\"titulo\"]", args[0])
            else:
                args = ['investigación', 'i+d']
                #page.fill("input[name=\"titulo\"]", "investigacion")
            page.click("input[name=\"fecDesde\"]")
            page.fill("input[name=\"fecDesde\"]", time.strftime('%d/%m/%Y', dD))
            page.click("input[name=\"fecHasta\"]")
            page.fill("input[name=\"fecHasta\"]", time.strftime('%d/%m/%Y', dH))
            page.click("select[name=\"regionalizacion\"]")
            page.press("select[name=\"regionalizacion\"]", "ArrowUp")
            page.press("select[name=\"regionalizacion\"]", "ArrowUp")
            page.click("button:has-text(\"Buscar\")")

            with page.expect_download(timeout=0) as download_info:
                page.click("img[alt=\"icono csv\"]")
            download = download_info.value

            download.save_as("convocatorias.csv")

            context.close()
            browser.close()
            data={}
            with open("convocatorias.csv", 'r', encoding='ISO-8859-1') as csvFile:
                rows = csv.DictReader(csvFile, delimiter=',')
                for row in rows:
                    id = row['Código BDNS']
                    data[id] = row
            return json.dumps(data)
    def obtain_data_bdns(self, num_bdns: int) -> dict:
        """
        Método para obtener una ampliación de la información de las convocatorias.

        :param num_bdns int: Número de BDNS.
        :return Diccionario con la información ampliada.
        """
        url = 'https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatoria/' + \
            str(num_bdns)
        response = requests.request('GET', url, verify=False)
        dicc = {}
        soup = BeautifulSoup(response.text, 'html.parser')
        i = 0
        for link in soup.find_all('div'):
            if link.find('h3') != None:
                if link.find('p') != None:
                    dicc[link.find('h3').text] = link.find('p').text
                elif link.find('li') != None:
                    dicc[link.find('h3').text] = ''.join(e.text for e in link.find_all('li'))
        return dicc
        
    def obtain_data_bdns_file(self, path: str) -> dict:
        """
        Método para obtener una ampliación de la información de las convocatorias a través de un fichero.

        :param path str: Path del fichero.
        :return Diccionario con la información ampliada.
        """
        with open(path, 'r', encoding='ISO-8859-1') as file:
            response_text = file.read()
            file.close()
        dicc = {}
        soup = BeautifulSoup(response_text, 'html.parser')
        i = 0
        for link in soup.find_all('div'):
            if link.find('h3') != None:
                if link.find('p') != None:
                    dicc[link.find('h3').text] = link.find('p').text
                elif link.find('li') != None:
                    dicc[link.find('h3').text] = ''.join(e.text for e in link.find_all('li'))
        return dicc