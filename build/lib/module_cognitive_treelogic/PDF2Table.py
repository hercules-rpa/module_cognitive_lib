import pandas as pd
import os
import numpy as np
import PyPDF2
import camelot
import smtplib
import smtplib,ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PyPDF2  import PdfFileReader


PATH_TEMP = "/tmp/"
PATH_FILES = ""

class ProcessExtractTable():
    def __init__(self, parameters):
        self.parameters = parameters


    def execute(self):
        """
        Método que ejecuta el proceso de extraer de un PDF la tabla deseada.
        """
        files       = self.parameters['files']
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
            list_df.append(dfs)
            if excel:
                self.to_excel(name_file, dfs)
                self.send_mail("smtp.um.es",25,"noreply@um.es",self.parameters['email'],"PDF2Table fichero XLSX.","A continuación se adjunta el fichero XLSX con la tabla pasada por parámetro.\n\nSaludos.",name_file+"xlsx")
        return list_df
            

        

    def to_excel(self, name, dfs):
        """
        Método que convierte a excel el dataframe convertido del archivo PDF.

        :param name str: Nombre con el que se va a identificar al fichero.
        :param dfs Dataframe: Dataframe con el contenido de la tabla extraída del PDF.
        """
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
            for f in range(startrow+1, startrow+1+df.shape[0]):
                columna = 0
                for c in range(startcol+1, startcol+df.shape[1]+1):
                    value = str(df.iloc[fila,columna]).replace("\r", " ")
                    worksheet_result.write(f,c, value, format_colors[color_index])
                    columna = columna +1
                fila = fila +1
                color_index = (color_index+1)%2
        writer.save()

    def stringToRange(self, x):
        """
        Método para sacar la secuencia de una agrupación de números.

        :param x str: Rango de números puesto como input.
        :return array con secuencia completa.
        """
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

    def get_preprocessing_page(self, pdf_file, name, page):
        """
        Método para procesar la página que nos interesa tratar en el PDF.

        :param pdf_file str: Path del PDF a tratar.
        :param name str: Nombre del fichero PDF.
        :param page str: Páginas a tratar del PDF.
        :return path del archivo PDF con las páginas seleccionadas.
        """
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
                with open(fpath, "wb+") as f:
                    outfile.write(f)
        return fpath

    def get_solution(self, pdf_file):
        """
        Método que busca si hay una solución en la tabla seleccionada.

        :param pdf_file str: path del archivo PDF que se está tratando.
        """
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
        return best_solution_camelot

    def get_best_solution(self, table1, table2): 
        """
        Método para encontrar la mejor solución para mostrar en el documento.

        :param table1 []: Array de df con el contenido de la tabla.
        :param table2 []: Array de df con el contenido de la tabla
        """
        best_solution = []
        if len(table1) - len(table2) == 0:
            for i in range(0,len(table1)):
                df_1 = table1[i]
                df_2 = table2[i]
                df_1 = df_1.replace(r'^\s*$', np.nan, regex=True)
                df_2 = df_2.replace(r'^\s*$', np.nan, regex=True)
                df_1 = df_1.dropna(axis=1, thresh=len(df_1)/2, how='all')
                df_2 = df_2.dropna(axis=1, thresh=len(df_1)/2, how='all')
                df_1_aux = df_1.dropna(axis=0, how='any')
                df_2_aux = df_2.dropna(axis=0, how='any') 
                nan_df1 = df_1_aux.isna().sum().sum()
                nan_df2 = df_2_aux.isna().sum().sum()

                if df_1.shape[1] >= df_2.shape[1] and  df_1_aux.shape[0] >= df_2_aux.shape[0] and nan_df1 <= nan_df2:
                    best_solution.append(df_1)
                else:
                    best_solution.append(df_2)

        elif len(table1) - len(table2) < 0:
            best_solution = table1

        else:
            best_solution = table2
                
        return best_solution

    def send_mail(self, smtp_server, port, sender, receiver, subject, body, attached,username="",passw=""):
        """
        Método para enviar por email el resultado.
        
        :param smtp_server str: Servidor SMTP.
        :param port str: Puerto al que enviamos la petición.
        :param sender str: Email del usuario que envía el correo.
        :param receiver str: Email del usuario que reciviría el correo.
        :param subject str: Asunto del email.
        :param body str: Body del email que se envía.
        :param attached str: path del archivo a adjuntar.
        :param username str: usuario de la cuenta. Por defecto "".
        :param passw str: contraseña de la cuenta. Por defecto "".
        """
        mime_subtype = 'plain'
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            if port == 465:
                sender_email = username
                password = passw
                server.login(sender_email, password)
            msg =  self.create_message(sender,receiver,subject,body, mime_subtype,attached)
            try:
                server.sendmail(sender, receiver, msg.as_string())
            except:
                return "Sending error: No se ha podido enviar el email a "+receiver+" desde "+sender+" con el contenido :"+ body+" y adjuntos : "+ ' '.join(attached if attached is not None else "[]")
        return "Mensaje enviado correctamente a "+receiver+" desde "+sender+" con el contenido :"+ body+" y adjuntos : "+ ' '.join(attached if attached is not None else "[]")

    def create_message(self,sender,receiver,subject,body,subtype, attached = None):
        """
        Método para crear un mensaje MIME.

        :param sender str: Email del usuario que envía el correo.
        :param receiver str: Email del usuario que reciviría el correo.
        :param subject str: Asunto del email.
        :param body str: Body del email que se envía.
        :param subtype str: Tipo de mensaje MIME que se quiere construir.
        :param attached str: path del archivo a adjuntar.

        :return mensaje MIME construido para su envío.
        """
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = receiver
        message["Subject"] = subject
        message["Bcc"] = receiver 
        message.attach(MIMEText(body, subtype))
        if (attached is not None):
            for att in attached:
                self.attach_file(att,message)
        return message


    def attach_file(self,filename,message):
        """
        Método para insertar un archivo en el formato MIME.

        :param filename str: path con el fichero que queremos adjuntar.
        :param message str: mensaje MIME al que queremos adjuntar el fichero.
        """
        self.update_log("Se ha adjuntado al correo el documento "+filename,True)
        with open(filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())   
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )
        message.attach(part)
