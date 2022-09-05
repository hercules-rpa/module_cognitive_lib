import pandas as pd
import matplotlib.pyplot as plt
import csv
from pdf2image import convert_from_path
import os, sys
import numpy as np
import time
from imutils.object_detection import non_max_suppression
import re
import tabula 
import imutils
import PyPDF2
import pytesseract
import camelot
import uuid
from PyPDF2  import PdfFileReader
import pandas as pd
import xlsxwriter

#conda install -c conda-forge/label/gcc7 ghostscript


#Posibles atributos
    # - pagina/s
    # - busqueda de un valor
    # - busqueda de una cabecera
    # - tipo, concensiones (contendrá 3 tablas?)

PATH_TEMP = "/tmp/"
PATH_FILES = ""

class ProcessExtractTable():
    def __init__(self, parameters):
        self.parameters = parameters


    def execute(self):
        print(self.parameters)
        files          = self.parameters['files']
        excel       = self.parameters['excel']
        list_df = []
        for f in files:
            path = f['path']
            page = f['page']
            f_name, _ = os.path.splitext(path)
            name_file = f_name.split('/')[-1]
            if not page:
                page = 'all'
            file = self.get_preprocessing_page(path, name_file, page)
            dfs = self.get_solution(file)
            list_df.append(dfs) #dfs es un array de df
            if excel:
                self.to_excel(name_file, dfs)
                #enviamos por correo los excel generados
            #self.result = list_df
        return list_df
            

        

    def to_excel(self, name, dfs):
        writer = pd.ExcelWriter(name+".xlsx", engine="xlsxwriter")
        workbook = writer.book
        startrow = 2
        startcol = 0
        format_header = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'border': 2,
            'border_color':'#538DD5',
            'fg_color': '#4f81bd',
            'align': 'center',
            'valign': 'center'}) 

        format_colors = [workbook.add_format({
            'text_wrap': True,
            'border': 2,
            'border_color':'#538DD5',
            'fg_color': '#c5d9f1',
            'align': 'center',
            'valign': 'center'}), 
            workbook.add_format({
            'text_wrap': True,
            'border': 2,
            'border_color':'#538DD5',
            'fg_color': '#ffffff',
            'align': 'center',
            'valign': 'center'})]

        for i,df in enumerate(dfs):
            df.to_excel(writer,sheet_name="Table-"+str(i),startrow=startrow, startcol=startcol)
            worksheet_result = writer.sheets["Table-"+str(i)]
            fila = 0
            color_index = 0
            df = df.replace(np.nan, " ")
            #PONEMOS EL FORMATO EN LOS DIFERENTES DATOS QUE TENEMOS, COLOR ALTERNATIVO PARA CADA FILA, ETC..
            for f in range(startrow+1, startrow+1+df.shape[0]):
                columna = 0
                for c in range(startcol+1, startcol+df.shape[1]+1):
                    value = str(df.iloc[fila,columna]).replace("\r", " ")
                    worksheet_result.write(f,c, value, format_colors[color_index])
                    columna = columna +1
                fila = fila +1
                color_index = (color_index+1)%2
            
            
            #Eliminamos la columna indice, noexiste otra forma de hacerlo
            # for c in range(startrow, startrow + df.shape[0]+10):
            #     worksheet_result.write(c,0,' ')
            # worksheet_result.set_column('A:I',20)
        writer.save()

    #pasamos de: '1,2,5-7' a [1,2,5,6,7]
    def stringToRange(self, x):
        result = []
        for part in x.split(','):
            if '-' in part:
                a, b = part.split('-')
                a, b = int(a), int(b)
                result.extend(range(a, b + 1))
            else:
                a = int(part)
                result.append(a)
        return result

    #Obtenemos la página que nos interesa y la tratamos, por ejemplo. Si está girada la centramos.
    def get_preprocessing_page(self, pdf_file, name, page):
        infile = PdfFileReader(pdf_file, strict=False)
        fpath = os.path.join(PATH_TEMP, f"{name}-{page}.pdf")
        froot, fext = os.path.splitext(fpath)
        if page == 'all':
            pages = self.stringToRange('1-'+str(infile.getNumPages()))
        else:
            pages = self.stringToRange(page)

        outfile = PyPDF2.PdfFileWriter()
        for idx, page in enumerate(pages):
            p = infile.getPage(page - 1)
            outfile.addPage(p)
            with open(fpath, "wb+") as f:
                outfile.write(f)
            layout, dim = camelot.utils.get_page_layout(fpath)
            # fix rotated PDF
            chars = camelot.utils.get_text_objects(layout, ltype="char")
            horizontal_text = camelot.utils.get_text_objects(layout, ltype="horizontal_text")
            vertical_text = camelot.utils.get_text_objects(layout, ltype="vertical_text")
            rotation = camelot.utils.get_rotation(chars, horizontal_text, vertical_text)
            layout, dim = camelot.utils.get_page_layout(pdf_file)
            if rotation != "":
                if rotation == "anticlockwise":
                    p.rotateClockwise(90)
                elif rotation == "clockwise":
                    p.rotateCounterClockwise(90)
                # outfile.addPage(p)
                with open(fpath, "wb+") as f:
                    outfile.write(f)
        return fpath

    def get_solution(self, pdf_file):
        camelot_tables_lattice_0 = camelot.read_pdf(pdf_file, flavor='lattice',line_tol= 2,joint_tol= 2, line_scale= 30,split_text= True, pages = 'all')
        camelot_tables_lattice_1 = camelot.read_pdf(pdf_file, flavor='lattice',line_tol= 1,joint_tol= 1, line_scale= 15,split_text= True, pages = 'all')
        camelot_tables_lattice_2 = camelot.read_pdf(pdf_file, flavor='lattice',split_text= True, pages = 'all')
        camelot_tables_stream_0  = camelot.read_pdf(pdf_file, flavor='stream', row_tol = 24, pages = 'all')
        camelot_tables_stream_1  = camelot.read_pdf(pdf_file, flavor='stream', row_tol = 12, pages = 'all')
        camelot_tables_stream_2 = camelot.read_pdf(pdf_file, flavor='stream',split_text=True, pages = 'all')




        camelot_list = [camelot_tables_lattice_0, camelot_tables_lattice_1, camelot_tables_lattice_2, camelot_tables_stream_0, camelot_tables_stream_1, camelot_tables_stream_2]
        df_list = []
        best_solution_camelot = None
        for _, camel in enumerate(camelot_list):
            df_list.append([x.df for x in camel])

        if len(df_list) > 0:
            best_solution_camelot  = df_list[0]
            for idx, df in enumerate(df_list):
                best_solution_camelot = self.get_best_solution(best_solution_camelot, df)
                # self.to_excel('camelot_tables_'+str(idx), df)
        return best_solution_camelot

    def get_best_solution(self, table1, table2): 
        best_solution = []
        #Nos quedamos con el que tenga mas columnas, menos filas y menos espacios en blanco
        if len(table1) - len(table2) == 0: #Comprobamos que tengamos las mismas tablas en cada uno
            for i in range(0,len(table1)):
                df_1 = table1[i]
                df_2 = table2[i]
                df_1 = df_1.replace(r'^\s*$', np.nan, regex=True)
                df_2 = df_2.replace(r'^\s*$', np.nan, regex=True)
                df_1 = df_1.dropna(axis=1, thresh=len(df_1)/2, how='all')
                df_2 = df_2.dropna(axis=1, thresh=len(df_1)/2, how='all')
                df_1_aux = df_1.dropna(axis=0, how='any')
                df_2_aux = df_2.dropna(axis=0, how='any') #si cualquier valor es nan elimina la fila
                nan_df1 = df_1_aux.isna().sum().sum()
                nan_df2 = df_2_aux.isna().sum().sum()

                # print(df_1.shape, nan_df1, df_2.shape, nan_df2)
                if df_1.shape[1] >= df_2.shape[1] and  df_1_aux.shape[0] >= df_2_aux.shape[0] and nan_df1 <= nan_df2:
                    best_solution.append(df_1)
                else:
                    best_solution.append(df_2)

        elif len(table1) - len(table2) < 0: #Hay mas tablas en stream, puede estar cogiendo texto que no deba
            best_solution = table1

        else:
            best_solution = table2
                
        return best_solution


# parameters = {
#     "files":[
#         {
#             "path": "readpdf/RESOLUCIÓN DE CONCESIÓN-PROYECTOS UMU.pdf",
#             "page": "4",
#             "image": False
#         }
        # ,
        # {
        #     "path": "readpdf/nuevas/PRE2020_TerceraRC_Art20_4_Firmada.pdf",
        #     "page": "5",
        #     "image": False
        # }
        # ,
        # {
        #     "path": "readpdf/CONCESIÓN_PREDOC2020_ Res 29 junio 2021 (WEB 29 junio) - MURCIA.pdf",
        #     "page": 'all',
        #     "image": False
        # },
        # {
        #     "path": "readpdf/PRP - REDES DE INVESTIGACIÓN - UMU.pdf",
        #     "page": None,
        #     "image": False
        # },
        # {
        #     "path": "readpdf/nuevas/Resolucion_Concesion_PREDOC2020_firmada.pdf",
        #     "page": "5",
        #     "image": False
        # }    
#     ],
#     "excel": False
# }
# pr = ProcessExtractTable(parameters)
# pr.execute()
